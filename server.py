"""Loopback-only Flask server for the premium SankhyaGuard interface."""

import csv
import io
import os
import re
import subprocess
import tempfile
import threading
import wave
from pathlib import Path

from flask import Flask, jsonify, request, send_file, send_from_directory
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge

import prisma_client
from core import analyse, parse_reply, pretty
from live_workflow import validate_correction
from replay_data import PROJECT_DIR, audio_path_for, load_replay_rows


MAX_AUDIO_BYTES = 10 * 1024 * 1024
MAX_RECORDING_SECONDS = 15
MIN_RECORDING_SECONDS = 0.6
LANGCODE = {"en": "en-IN", "kn": "kn-IN", "hi": "hi-IN"}
LANGUAGE_NAMES = {"en": "English", "kn": "Kannada", "hi": "Hindi"}
ID_RE = re.compile(r"^(en|kn|hi)_\d{2}$")
DATASET = PROJECT_DIR / "dataset_script.csv"


def _read_call_limit():
    raw = os.getenv("SG_MAX_CALLS", "24")
    try:
        value = int(raw)
    except ValueError as error:
        raise RuntimeError("SG_MAX_CALLS must be a positive integer.") from error
    if not 1 <= value <= 1000:
        raise RuntimeError("SG_MAX_CALLS must be between 1 and 1000.")
    return value


MAX_CALLS = _read_call_limit()
STATE = {"calls": 0}
LOCK = threading.Lock()

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config["MAX_CONTENT_LENGTH"] = MAX_AUDIO_BYTES + 64 * 1024


class UserError(ValueError):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code


class UpstreamError(RuntimeError):
    pass


@app.errorhandler(UserError)
def handle_user_error(error):
    return jsonify(error=str(error)), error.status_code


@app.errorhandler(RequestEntityTooLarge)
def handle_large_request(_error):
    return jsonify(error="The upload is too large. Choose audio under 10 MB."), 413


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    if isinstance(error, HTTPException):
        return jsonify(error="The request could not be completed."), error.code
    app.logger.exception("Unhandled local app error")
    return jsonify(error="The server could not complete the request."), 500


def require_same_origin_post():
    if request.headers.get("X-SankhyaGuard-Request") != "1":
        raise UserError("This request did not come from the SankhyaGuard app.", 403)


def require_live_consent():
    if request.form.get("live_consent") != "true":
        raise UserError(
            "Confirm that live processing may use API credits before continuing.",
            403,
        )


def parse_correction_options():
    kind = request.form.get("kind", "")
    if kind not in ("digits", "amount"):
        raise UserError("Choose a supported number type.")
    raw_length = request.form.get("expected_len", "")
    try:
        expected_len = int(raw_length)
    except (TypeError, ValueError) as error:
        raise UserError("The expected digit count must be a whole number.") from error
    if kind == "digits" and expected_len not in (0, 6, 10):
        raise UserError("Choose a 6-digit PIN, a 10-digit phone number, or unknown length.")
    if kind == "amount" and expected_len != 0:
        raise UserError("Amounts do not use an expected digit count.")
    value = request.form.get("value", "")
    if len(value) > 64:
        raise UserError("The correction is too long.")
    return kind, value, expected_len or None


def parse_form_options():
    lang = request.form.get("lang", "")
    kind = request.form.get("kind", "")
    if lang not in LANGCODE or kind not in ("digits", "amount"):
        raise UserError("Choose a supported language and number type.")
    raw_length = request.form.get("expected_len", "")
    try:
        expected_len = int(raw_length)
    except (TypeError, ValueError) as error:
        raise UserError("The expected digit count must be a whole number.") from error
    if not 0 <= expected_len <= 20:
        raise UserError("The expected digit count must be between 0 and 20.")
    if kind == "amount" and expected_len:
        raise UserError("Amounts do not use an expected digit count.")
    if kind == "digits" and expected_len not in (0, 6, 10):
        raise UserError("Choose a 6-digit PIN, a 10-digit phone number, or unknown length.")
    return lang, kind, expected_len or None


def convert_to_wav(raw, max_seconds=MAX_RECORDING_SECONDS):
    if not raw:
        raise UserError("The audio recording is empty.")
    if len(raw) > MAX_AUDIO_BYTES:
        raise UserError("The audio upload is too large. Choose audio under 10 MB.", 413)

    with tempfile.TemporaryDirectory(prefix="sankhyaguard-") as directory:
        source = Path(directory) / "recording.bin"
        destination = Path(directory) / "recording.wav"
        source.write_bytes(raw)
        try:
            completed = subprocess.run(
                [
                    "ffmpeg",
                    "-nostdin",
                    "-v",
                    "error",
                    "-y",
                    "-i",
                    str(source),
                    "-ac",
                    "1",
                    "-ar",
                    "16000",
                    "-c:a",
                    "pcm_s16le",
                    str(destination),
                ],
                capture_output=True,
                timeout=20,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise UserError(
                "Audio conversion is unavailable or took too long. Check that ffmpeg is installed.",
                422,
            ) from error
        if completed.returncode != 0 or not destination.is_file():
            raise UserError("Could not decode this recording. Try another audio file.", 422)
        wav_bytes = destination.read_bytes()

    try:
        with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
            if (
                wav_file.getcomptype() != "NONE"
                or wav_file.getnchannels() != 1
                or wav_file.getsampwidth() != 2
                or wav_file.getframerate() != 16000
            ):
                raise UserError("Audio conversion did not produce the required WAV format.")
            frames = wav_file.getnframes()
            duration = frames / wav_file.getframerate()
    except (wave.Error, EOFError) as error:
        raise UserError("The converted audio is not a valid WAV file.", 422) from error

    if duration < MIN_RECORDING_SECONDS:
        raise UserError("That recording was too short. Please speak the whole number.")
    if duration > max_seconds:
        raise UserError(
            f"Keep the recording under {max_seconds} seconds and try again."
        )
    return wav_bytes, duration


def read_upload():
    uploaded = request.files.get("audio")
    if uploaded is None:
        raise UserError("No audio was received.")
    raw = uploaded.stream.read(MAX_AUDIO_BYTES + 1)
    if len(raw) > MAX_AUDIO_BYTES:
        raise UserError("The audio upload is too large. Choose audio under 10 MB.", 413)
    return convert_to_wav(raw)


def transcribe_pair(wav_bytes, lang):
    with LOCK:
        if STATE["calls"] + 2 > MAX_CALLS:
            raise UserError(
                "The per-run Prisma request limit has been reached. "
                "No new request was sent.",
                429,
            )
        responses = []
        for model in ("v25", "v30"):
            STATE["calls"] += 1
            try:
                responses.append(
                    prisma_client.transcribe(
                        wav_bytes, "recording.wav", LANGCODE[lang], model
                    )
                )
            except (prisma_client.PrismaError, ValueError) as error:
                app.logger.warning("Prisma %s request failed: %s", model, error)
                raise UpstreamError(
                    "A Prisma request failed. One or more requests may have used "
                    "credits; the app did not retry automatically."
                ) from error
    return responses


def response_text(response):
    value = response.get("transcript")
    return value if isinstance(value, str) else ""


def replay_rows():
    rows, warnings = load_replay_rows(demo_ids_path=None)
    for warning in warnings:
        app.logger.warning("Pilot replay data: %s", warning)
    return rows


def find_replay_row(condition, clip_id):
    if condition not in ("clean", "phone", "snr5", "snr10") or not ID_RE.fullmatch(clip_id):
        raise UserError("That replay clip is not valid.")
    for row in replay_rows():
        if row["id"] == clip_id and row["condition"] == condition:
            return row
    raise UserError("No complete saved pilot result exists for that clip.", 404)


def load_demo_rows():
    rows = []
    try:
        with DATASET.open(encoding="utf-8-sig", newline="") as stream:
            for row in csv.DictReader(stream):
                clip_id = row.get("id", "")
                lang = row.get("language", "")
                kind = row.get("kind", "")
                if (
                    not ID_RE.fullmatch(clip_id)
                    or lang not in LANGUAGE_NAMES
                    or not clip_id.startswith(f"{lang}_")
                    or kind not in ("digits", "amount")
                ):
                    continue
                path = PROJECT_DIR / "audio" / f"{clip_id}.wav"
                if not path.is_file() or path.stat().st_size > MAX_AUDIO_BYTES:
                    continue
                try:
                    expected = int(row["expected_len"]) if row.get("expected_len") else None
                except (TypeError, ValueError):
                    continue
                if expected not in (None, 6, 10):
                    continue
                rows.append(
                    {
                        "id": clip_id,
                        "language": lang,
                        "language_name": LANGUAGE_NAMES[lang],
                        "kind": kind,
                        "expected_len": expected,
                        "condition": "clean",
                    }
                )
    except (OSError, UnicodeError, csv.Error) as error:
        app.logger.exception("Could not load demo manifest")
        raise UserError("The demo audio list could not be loaded.", 500) from error
    return rows


@app.get("/")
def index():
    return send_from_directory(PROJECT_DIR / "static", "index.html")


@app.get("/api/status")
def status():
    with LOCK:
        calls = STATE["calls"]
    return jsonify(calls=calls, max_calls=MAX_CALLS)


@app.get("/api/demo/cases")
def demo_cases():
    return jsonify(load_demo_rows())


@app.get("/api/demo/clip/<clip_id>")
def demo_clip(clip_id):
    if not ID_RE.fullmatch(clip_id):
        raise UserError("That demo clip ID is not valid.")
    if not any(row["id"] == clip_id for row in load_demo_rows()):
        raise UserError("That demo clip is not available.", 404)
    path = PROJECT_DIR / "audio" / f"{clip_id}.wav"
    return send_file(path, mimetype="audio/wav", conditional=True)


@app.post("/api/check")
def check():
    require_same_origin_post()
    require_live_consent()
    lang, kind, expected_len = parse_form_options()
    wav_bytes, duration = read_upload()
    try:
        v25, v30 = transcribe_pair(wav_bytes, lang)
    except UpstreamError as error:
        return (
            jsonify(error=str(error), calls=STATE["calls"], max_calls=MAX_CALLS),
            502,
        )

    views = {"v2.5": response_text(v25)}
    v25_output = v25.get("output")
    if isinstance(v25_output, dict):
        literal = v25_output.get("literal")
        if isinstance(literal, str) and literal.strip():
            views["v2.5 words"] = literal
    views["v3.0"] = response_text(v30)
    result = analyse(kind, views, expected_len, lang)
    result.update(
        duration=round(duration, 1),
        calls=STATE["calls"],
        max_calls=MAX_CALLS,
        notes=[],
    )
    return jsonify(result)


@app.post("/api/reply")
def reply():
    require_same_origin_post()
    require_live_consent()
    lang, _kind, _expected_len = parse_form_options()
    wav_bytes, _duration = read_upload()
    with LOCK:
        if STATE["calls"] + 1 > MAX_CALLS:
            raise UserError(
                "The per-run Prisma request limit has been reached. "
                "No new request was sent.",
                429,
            )
        STATE["calls"] += 1
        try:
            response = prisma_client.transcribe(
                wav_bytes, "reply.wav", LANGCODE[lang], "v25"
            )
        except (prisma_client.PrismaError, ValueError) as error:
            app.logger.warning("Prisma spoken-reply request failed: %s", error)
            raise UpstreamError(
                "The reply could not be understood. The request may have used "
                "credits; it was not retried."
            ) from error
        calls = STATE["calls"]
    text = response_text(response)
    return jsonify(text=text, intent=parse_reply(text), calls=calls, max_calls=MAX_CALLS)


@app.post("/api/correction")
def correction():
    require_same_origin_post()
    kind, value, expected_len = parse_correction_options()
    try:
        corrected = validate_correction(kind, value, expected_len)
    except ValueError as error:
        raise UserError(str(error)) from error
    canonical = str(corrected)
    formatted = pretty(kind, canonical if kind == "digits" else int(canonical))
    return jsonify(value=canonical, pretty=formatted)


@app.get("/api/replay/cases")
def replay_cases():
    rows = replay_rows()
    return jsonify(
        [
            {
                "id": row["id"],
                "condition": row["condition"],
                "kind": row["kind"],
                "lang": row["language"],
            }
            for row in rows
        ]
    )


@app.get("/api/replay/<condition>/<clip_id>")
def replay_one(condition, clip_id):
    row = find_replay_row(condition, clip_id)
    views = {
        "v2.5": row.get("view_v2_5", ""),
        "v3.0": row.get("view_v3_0", ""),
    }
    expected_len = int(row["expected_len"]) if row.get("expected_len", "").strip() else None
    result = analyse(row["kind"], views, expected_len, row["language"])
    truth = row["truth"].strip()
    result["truth"] = truth
    result["truth_pretty"] = pretty(row["kind"], truth if row["kind"] == "digits" else int(truth))
    return jsonify(result)


@app.get("/api/clip/<condition>/<clip_id>")
def replay_clip(condition, clip_id):
    row = find_replay_row(condition, clip_id)
    path = audio_path_for(row, PROJECT_DIR)
    if path is None or not path.is_file():
        raise UserError("Audio is missing for this saved pilot case.", 404)
    return send_file(path, mimetype="audio/wav", conditional=True)


@app.errorhandler(UpstreamError)
def handle_upstream_error(error):
    return jsonify(error=str(error), calls=STATE["calls"], max_calls=MAX_CALLS), 502


if __name__ == "__main__":
    print(
        "\nSankhyaGuard premium app is running at http://127.0.0.1:5000/"
        f"\nPer-run limit: {MAX_CALLS} Prisma requests."
        "\nLive processing requires explicit consent in the app."
    )
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
