import csv
import io
import uuid
import wave
from datetime import datetime, timezone
from pathlib import Path

from guard import decide, parse_view
from numparse import parse_amount, parse_digit_string


MAX_RECORDING_SECONDS = 15
MIN_RECORDING_SECONDS = 0.1
SESSION_LOG = Path(__file__).resolve().parent / "results" / "live_sessions.csv"
SESSION_FIELDS = (
    "session_id",
    "event",
    "timestamp_utc",
    "mode",
    "language",
    "kind",
    "expected_len",
    "transcript_v25",
    "literal_v25",
    "transcript_v30",
    "parsed_v25",
    "parsed_v30",
    "guard_decision",
    "guard_reasons",
    "user_confirmation",
    "user_correction",
    "final_verified_number",
    "api_status",
    "api_request_ids",
    "recording_duration_seconds",
)


class AudioValidationError(ValueError):
    pass


def validate_wav(audio_bytes, max_seconds=MAX_RECORDING_SECONDS):
    if not audio_bytes:
        raise AudioValidationError("The recording is empty. Record it again.")
    try:
        with wave.open(io.BytesIO(audio_bytes), "rb") as wav_file:
            if wav_file.getcomptype() != "NONE":
                raise AudioValidationError(
                    "The recording must be uncompressed WAV audio."
                )
            rate = wav_file.getframerate()
            frames = wav_file.getnframes()
            if rate <= 0 or frames <= 0:
                raise AudioValidationError("The WAV recording contains no audio.")
            duration = frames / rate
    except (wave.Error, EOFError) as error:
        raise AudioValidationError(
            "The microphone recording is not a readable WAV file."
        ) from error
    if duration < MIN_RECORDING_SECONDS:
        raise AudioValidationError(
            "The recording is too short to contain a spoken number."
        )
    if duration > max_seconds:
        raise AudioValidationError(
            f"The recording is {duration:.1f} seconds. Please record no more "
            f"than {max_seconds} seconds."
        )
    return duration


def audio_fingerprint(audio_bytes, lang_code, kind, expected_len):
    import hashlib

    digest = hashlib.sha256()
    for value in (
        audio_bytes,
        lang_code.encode("utf-8"),
        kind.encode("utf-8"),
        str(expected_len or "").encode("ascii"),
    ):
        digest.update(len(value).to_bytes(8, "big"))
        digest.update(value)
    return digest.hexdigest()


def evaluate_transcripts(v25_response, v30_response, kind, expected_len=None):
    if not isinstance(v25_response, dict) or not isinstance(v30_response, dict):
        raise ValueError("Both real model responses are required for Guard evaluation.")
    transcript_v25 = v25_response.get("transcript")
    transcript_v30 = v30_response.get("transcript")
    if not isinstance(transcript_v25, str) or not transcript_v25.strip():
        raise ValueError("Prisma v2.5 returned an empty transcript.")
    if not isinstance(transcript_v30, str) or not transcript_v30.strip():
        raise ValueError("Prisma v3.0 returned an empty transcript.")
    views = {"Prisma v2.5": transcript_v25, "Prisma v3.0": transcript_v30}
    parsed_v25, _ = parse_view(kind, transcript_v25)
    parsed_v30, _ = parse_view(kind, transcript_v30)
    guard_result = decide(kind, views, expected_len=expected_len)
    return {
        "views": views,
        "parsed_v25": parsed_v25,
        "parsed_v30": parsed_v30,
        "guard": guard_result,
    }


def validate_correction(kind, value, expected_len=None):
    value = value.strip()
    if not value:
        raise ValueError("Enter the number you intended to say.")
    if kind == "digits":
        parsed = parse_digit_string(value)
        if parsed["unknown"] or not parsed["digits"]:
            raise ValueError("Enter only a valid number or spoken digit words.")
        if expected_len and len(parsed["digits"]) != expected_len:
            raise ValueError(
                f"That number has {len(parsed['digits'])} digits; "
                f"{expected_len} are expected."
            )
        return parsed["digits"]
    parsed = parse_amount(value)
    if parsed["value"] is None or parsed["unknown"]:
        raise ValueError("Enter a number amount the existing parser can understand.")
    return parsed["value"]


def new_session_id():
    return str(uuid.uuid4())


def append_session_event(session, event, path=SESSION_LOG):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "session_id": session["session_id"],
        "event": event,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "live",
        "language": session.get("language", ""),
        "kind": session.get("kind", ""),
        "expected_len": session.get("expected_len", ""),
        "transcript_v25": session.get("transcript_v25", ""),
        "literal_v25": session.get("literal_v25", ""),
        "transcript_v30": session.get("transcript_v30", ""),
        "parsed_v25": session.get("parsed_v25", ""),
        "parsed_v30": session.get("parsed_v30", ""),
        "guard_decision": session.get("guard_decision", ""),
        "guard_reasons": "|".join(session.get("guard_reasons", [])),
        "user_confirmation": session.get("user_confirmation", ""),
        "user_correction": session.get("user_correction", ""),
        "final_verified_number": session.get("final_verified_number", ""),
        "api_status": session.get("api_status", ""),
        "api_request_ids": "|".join(session.get("api_request_ids", [])),
        "recording_duration_seconds": session.get("recording_duration_seconds", ""),
    }
    is_new = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=SESSION_FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow(row)
    return path
