import base64
import binascii
import csv
from html import escape
import re

import streamlit as st

import prisma_client
from live_workflow import (
    AudioValidationError,
    append_session_event,
    audio_fingerprint,
    evaluate_transcripts,
    new_session_id,
    validate_correction,
    validate_wav,
)
from replay_data import PROJECT_DIR, audio_path_for, load_replay_rows
from ui_helpers import (
    CSS,
    candidates_html,
    friendly_reasons,
    indian,
)
from voice_orb_component import voice_orb


LANGUAGE_CODES = {"en": "en-IN", "kn": "kn-IN", "hi": "hi-IN"}
LANGUAGE_NAMES = {"en": "English", "kn": "Kannada", "hi": "Hindi"}
MAX_AUDIO_BYTES = 10 * 1024 * 1024

APP_CSS = """
<style>
.stApp {position:relative;isolation:isolate;height:100vh;min-height:100vh;background:radial-gradient(ellipse at 50% 10%,#101a35 0%,#080c17 44%,#05070d 100%);color:#eef2ff;}
.stApp::before {position:fixed;z-index:0;top:5vh;right:-18vw;width:min(78vw,1000px);height:min(86vh,900px);min-height:540px;pointer-events:none;content:"";opacity:.25;transform-style:preserve-3d;background:
radial-gradient(circle at 50% 50%,#0a1120 0 18%,#13264c80 22%,transparent 38%),
radial-gradient(ellipse 34% 23% at 50% 50%,transparent 96%,#5380ff88 98%,transparent 100%),
radial-gradient(ellipse 43% 30% at 50% 50%,transparent 97%,#c7f00060 99%,transparent 100%),
radial-gradient(ellipse 25% 44% at 50% 50%,transparent 97%,#5380ff55 99%,transparent 100%),
radial-gradient(circle at 68% 28%,#c7f000 0 3px,transparent 5px),
radial-gradient(circle at 29% 69%,#5482ff 0 3px,transparent 5px);
animation:sg-resonance-drift 28s ease-in-out infinite;}
.stApp::after {position:fixed;z-index:0;top:47vh;right:0;width:min(78vw,980px);height:12vh;min-height:70px;pointer-events:none;content:"";opacity:.12;background:linear-gradient(90deg,transparent,#3568ff 25%,#c7f000 52%,#3568ff 76%,transparent);clip-path:polygon(0 49%,12% 49%,14% 45%,16% 53%,18% 30%,20% 72%,22% 43%,24% 55%,27% 49%,42% 49%,44% 46%,46% 52%,48% 24%,50% 78%,52% 42%,54% 57%,56% 49%,72% 49%,74% 44%,76% 54%,78% 32%,80% 70%,82% 43%,84% 55%,87% 49%,100% 49%,100% 52%,87% 52%,84% 58%,82% 46%,80% 73%,78% 35%,76% 57%,74% 47%,72% 52%,56% 52%,54% 60%,52% 45%,50% 81%,48% 27%,46% 55%,44% 49%,42% 52%,27% 52%,24% 58%,22% 46%,20% 75%,18% 33%,16% 56%,14% 48%,12% 52%,0 52%);background-size:200% 100%;animation:sg-wave-glide 18s linear infinite;}
[data-testid="stHeader"] {position:relative;z-index:2;background:transparent;}
[data-testid="stMain"] {position:relative;z-index:1;}
@keyframes sg-resonance-drift {0%,100%{transform:perspective(1000px) rotateY(-7deg) rotateZ(-.25deg) scale(1)}50%{transform:perspective(1000px) rotateY(-3deg) rotateZ(.25deg) scale(1.015)}}
@keyframes sg-wave-glide {to{background-position:200% 0}}
.sg-shell {max-width:900px;margin:0 auto;padding:10px 0 24px;}
.sg-header {display:flex;align-items:center;justify-content:space-between;margin:10px 0 22px;}
.sg-brand {font-size:2rem;font-weight:800;letter-spacing:-.045em;color:#f4f6ff;text-shadow:0 6px 0 #101a35,0 10px 22px #3568ff66;transform-origin:50% 100%;animation:sg-title-arrive 1.15s cubic-bezier(.2,.8,.2,1) both;}
.sg-subtitle {color:#a6b0c9;font-size:.95rem;margin-top:3px;animation:sg-subtitle-arrive .8s .28s ease-out both;}
.sg-ready {border:1px solid #a7cf00;background:#20280b;color:#d9ff48;border-radius:999px;padding:7px 13px;font-size:.82rem;}
.sg-intro {position:fixed;inset:0;z-index:99999;display:grid;place-items:center;background:radial-gradient(ellipse at 50% 46%,#101a35 0%,#080c17 54%,#05070d 100%);pointer-events:none;animation:sg-intro-exit .65s 1.45s ease-in forwards;}
.sg-intro-content {text-align:center;perspective:900px;}
.sg-intro-title {margin:0;color:#f4f6ff;font-size:clamp(2.4rem,8vw,4.8rem);font-weight:850;letter-spacing:-.06em;text-shadow:0 8px 0 #101a35,0 15px 34px #3568ff88;animation:sg-intro-title .95s cubic-bezier(.16,.84,.25,1) both;}
.sg-intro-line {width:0;height:2px;margin:17px auto 0;background:linear-gradient(90deg,transparent,#3568ff,#c7f000,transparent);box-shadow:0 0 16px #c7f00088;animation:sg-intro-line .7s .55s ease-out forwards;}
@keyframes sg-intro-title {0%{opacity:0;transform:rotateX(-72deg) translateY(36px) scale(.8);filter:blur(10px)}70%{opacity:1;transform:rotateX(8deg) translateY(-4px) scale(1.035);filter:blur(0)}100%{opacity:1;transform:rotateX(0) translateY(0) scale(1);filter:blur(0)}}
@keyframes sg-intro-line {to{width:min(72vw,330px)}}
@keyframes sg-intro-exit {to{opacity:0;visibility:hidden}}
@keyframes sg-title-arrive {0%{opacity:0;transform:perspective(700px) rotateX(-62deg) translateY(28px) scale(.92);filter:blur(8px)}65%{opacity:1;transform:perspective(700px) rotateX(7deg) translateY(-2px) scale(1.015);filter:blur(0)}100%{opacity:1;transform:perspective(700px) rotateX(0) translateY(0) scale(1);filter:blur(0)}}
@keyframes sg-subtitle-arrive {from{opacity:0;transform:translateY(9px)}to{opacity:1;transform:translateY(0)}}
.sg-panel {background:#0c1220dd;border:1px solid #26375f;border-radius:20px;padding:22px;margin:14px 0;}
.sg-warning {background:#1b210b;border:1px solid #718d13;border-radius:14px;padding:13px 16px;color:#d9f47a;}
.sg-kicker {color:#9fb8ff;text-transform:uppercase;letter-spacing:.13em;font-size:.72rem;font-weight:700;}
.sg-big-number {font-size:clamp(2rem,7vw,4rem);font-weight:750;letter-spacing:-.04em;color:#f8fbff;line-height:1.1;margin:.3em 0;}
.sg-transcript {font-size:1.1rem;color:#d2d9e8;line-height:1.6;overflow-wrap:anywhere;}
.sg-muted {color:#a6b0c9;font-size:.88rem;}
.sg-result {border-radius:16px;padding:18px;background:#10182a;border:1px solid #314777;margin:14px 0;}
.sg-final {background:linear-gradient(120deg,#121a0a,#101a35);border:1px solid #c7f00077;border-radius:18px;padding:20px;margin-top:18px;}
@media (max-width:640px) {.sg-panel{padding:16px}.sg-brand{font-size:1.8rem}.stApp::before{top:12vh;right:-34vw;width:115vw;height:75vh;min-height:480px;opacity:.2}.stApp::after{top:48vh;opacity:.08}}
@media (prefers-reduced-motion: reduce) {.sg-brand,.sg-subtitle,.sg-intro-title,.sg-intro-line,.stApp::before,.stApp::after{animation:none}.sg-intro{animation:sg-intro-exit .1s .1s forwards}}
</style>
"""

st.set_page_config(page_title="SankhyaGuard", page_icon="🛡️", layout="centered")
st.markdown(CSS + APP_CSS, unsafe_allow_html=True)
st.session_state.setdefault("processed_fingerprints", set())
st.session_state.setdefault("live_result", None)
st.session_state.setdefault("correction_requested", False)
st.session_state.setdefault("voice_recording", None)
st.session_state.setdefault("voice_event_id", None)
st.session_state.setdefault("voice_capture_error", "")
st.session_state.setdefault("selected_demo_audio", None)
st.session_state.setdefault("loaded_demo_audio_id", None)
st.session_state.setdefault("demo_load_error", "")
st.session_state.setdefault("live-digit-length", 10)
show_intro = not st.session_state.get("intro_seen", False)
st.session_state["intro_seen"] = True
if show_intro:
    st.markdown(
        "<div class='sg-intro' aria-hidden='true'><div class='sg-intro-content'>"
        "<h1 class='sg-intro-title'>SankhyaGuard</h1><div class='sg-intro-line'></div>"
        "</div></div>",
        unsafe_allow_html=True,
    )

tab_try, tab_demo, tab_results, tab_how = st.tabs(
    ["Try it", "Demo Audios", "Results", "How it works"],
    key="app-navigation",
    on_change="rerun",
)


def display_number(kind, value):
    if value is None or value == "":
        return "Could not read a number"
    return str(value) if kind == "digits" else f"₹{indian(value)}"


def load_demo_audio_rows():
    dataset_path = PROJECT_DIR / "dataset_script.csv"
    audio_dir = PROJECT_DIR / "audio"
    rows = []
    warnings = []
    try:
        with dataset_path.open(encoding="utf-8-sig", newline="") as stream:
            for row in csv.DictReader(stream):
                clip_id = row.get("id", "")
                language = row.get("language", "")
                if (
                    not re.fullmatch(r"(en|kn|hi)_\d{2}", clip_id)
                    or language not in LANGUAGE_NAMES
                    or not clip_id.startswith(f"{language}_")
                    or row.get("kind") not in ("digits", "amount")
                ):
                    warnings.append(
                        f"Skipped a manifest row with invalid clip metadata: {clip_id or '(missing ID)'}."
                    )
                    continue
                expected_value = (row.get("expected_len") or "").strip()
                try:
                    expected_len = int(expected_value) if expected_value else None
                except ValueError:
                    warnings.append(
                        f"Skipped {clip_id}: expected digit count is not an integer."
                    )
                    continue
                audio_path = audio_dir / f"{clip_id}.wav"
                if not audio_path.is_file():
                    warnings.append(f"Audio file is missing for {clip_id}.")
                    continue
                rows.append(
                    {
                        "id": clip_id,
                        "language": language,
                        "kind": row["kind"],
                        "expected_len": expected_len,
                        "audio_path": audio_path,
                    }
                )
    except (OSError, UnicodeError, csv.Error) as error:
        return [], [f"Could not load the demo audio manifest: {error}"]
    return rows, warnings


def select_demo_audio(clip_id):
    st.session_state["selected_demo_audio"] = clip_id


def load_selected_demo_audio(clip_id, language, kind, expected_len):
    if not re.fullmatch(r"(en|kn|hi)_\d{2}", clip_id):
        st.session_state["demo_load_error"] = "The selected demo clip ID is invalid."
        return
    audio_path = PROJECT_DIR / "audio" / f"{clip_id}.wav"
    try:
        if audio_path.stat().st_size > MAX_AUDIO_BYTES:
            raise AudioValidationError("This demo audio file is too large to process.")
        audio_bytes = audio_path.read_bytes()
        duration = validate_wav(audio_bytes)
    except (OSError, AudioValidationError) as error:
        st.session_state["voice_recording"] = None
        st.session_state["demo_load_error"] = str(error)
        return

    st.session_state["voice_recording"] = {
        "bytes": audio_bytes,
        "duration": duration,
        "event_id": f"demo-{clip_id}",
    }
    st.session_state["live-language"] = language
    st.session_state["live-kind"] = kind
    if kind == "digits" and expected_len is not None:
        st.session_state["live-digit-length"] = expected_len
    st.session_state["loaded_demo_audio_id"] = clip_id
    st.session_state["live_result"] = None
    st.session_state["correction_requested"] = False
    st.session_state["demo_load_error"] = ""
    st.session_state["app-navigation"] = "Try it"


def show_replay_case(row):
    st.markdown(f"**Saved pilot clip:** `{escape(row['id'])}`")
    audio_path = audio_path_for(row, PROJECT_DIR)
    if audio_path is not None and audio_path.is_file():
        st.audio(audio_path.read_bytes(), format="audio/wav")
    else:
        st.warning(
            f"Audio file is missing for {row['id']}; the saved transcripts can still be viewed."
        )
    views = {
        "Prisma v2.5": row["view_v2_5"],
        "Prisma v3.0": row["view_v3_0"],
    }
    columns = st.columns(2)
    for column, (name, transcript) in zip(columns, views.items()):
        column.markdown(f"**{name} transcript**")
        column.code(transcript, language=None)
    result = evaluate_transcripts(
        {"transcript": views["Prisma v2.5"]},
        {"transcript": views["Prisma v3.0"]},
        row["kind"],
        int(row["expected_len"]) if row.get("expected_len", "").strip() else None,
    )
    st.write(
        "Guard decision:",
        result["guard"]["decision"],
        "—",
        display_number(row["kind"], result["guard"]["value"]),
    )
    if result["guard"]["reasons"]:
        st.caption("Reason: " + "; ".join(result["guard"]["reasons"]))
    st.caption(
        "Replay compares saved model outputs with the existing parser and Guard; "
        "the dataset label is not an independent audio check."
    )


def append_event_if_requested(session, event):
    if not session.get("save_locally"):
        return
    try:
        saved_path = append_session_event(session, event)
        st.caption(f"Saved locally to `{saved_path.relative_to(PROJECT_DIR)}`.")
    except OSError as error:
        st.error(f"The session could not be saved locally: {error}")


def show_live_result(result):
    if not result:
        return
    st.markdown('<div class="sg-panel">', unsafe_allow_html=True)
    st.markdown('<div class="sg-kicker">AI transcription</div>', unsafe_allow_html=True)
    if result.get("transcript_v25"):
        st.markdown(
            f"<div class='sg-transcript'><b>Prisma v2.5:</b> "
            f"{escape(result['transcript_v25'])}</div>",
            unsafe_allow_html=True,
        )
    if result.get("literal_v25"):
        st.markdown("**Prisma v2.5 literal form**")
        st.code(result["literal_v25"], language=None)
    if result.get("transcript_v30"):
        st.markdown(
            f"<div class='sg-transcript'><b>Prisma v3.0:</b> "
            f"{escape(result['transcript_v30'])}</div>",
            unsafe_allow_html=True,
        )
    if result.get("api_status") != "SUCCESS":
        st.error(
            result.get("error_message")
            or "A complete pair of non-empty Prisma transcripts is unavailable."
        )
        st.info(
            "The Guard was not run because it needs both real model transcripts. "
            "This audio will not be retried automatically; record a new clip if you choose to try again."
        )
        st.markdown("</div>", unsafe_allow_html=True)
        return

    guard_result = result["guard"]
    st.markdown('<div class="sg-kicker">AI understood</div>', unsafe_allow_html=True)
    st.markdown(
        f"<div class='sg-big-number'>{escape(display_number(result['kind'], guard_result['value']))}</div>",
        unsafe_allow_html=True,
    )
    parsed_text = (
        f"v2.5 parsed as {display_number(result['kind'], result['parsed_v25'])}; "
        f"v3.0 parsed as {display_number(result['kind'], result['parsed_v30'])}."
    )
    st.caption(parsed_text)
    if guard_result["decision"] == "ACCEPT":
        st.success("Guard decision: ACCEPT — the two parsed model views agree.")
    else:
        st.warning("Guard decision: CONFIRM — the Guard found a reason to ask.")
        if guard_result["reasons"]:
            for reason in friendly_reasons(guard_result["reasons"]):
                st.write("• " + reason)
    if guard_result["candidates"]:
        st.markdown(
            candidates_html(
                result["kind"],
                guard_result["candidates"],
                guard_result["disputed_positions"],
            ),
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    if result.get("user_confirmation") == "YES":
        st.markdown(
            f"<div class='sg-final'><div class='sg-kicker'>User confirmed</div>"
            f"<div class='sg-big-number'>{escape(display_number(result['kind'], result['final_verified_number']))}</div>"
            "<div class='sg-muted'>This records your confirmation; it is not independent proof of transcription accuracy.</div></div>",
            unsafe_allow_html=True,
        )
        return
    if result.get("user_confirmation") == "CORRECTED":
        st.markdown(
            f"<div class='sg-final'><div class='sg-kicker'>User corrected the AI</div>"
            f"<div class='sg-big-number'>{escape(display_number(result['kind'], result['final_verified_number']))}</div>"
            f"<div class='sg-muted'>AI understood: {escape(display_number(result['kind'], guard_result['value']))}</div></div>",
            unsafe_allow_html=True,
        )
        return

    candidates = guard_result["candidates"]
    if not candidates:
        st.warning(
            "The transcription could not be parsed into a safe number. "
            "Enter the number you intended below; the AI result will remain unchanged."
        )
        st.session_state["correction_requested"] = True
    else:
        st.markdown("### Is this the number you spoke?")
        if len(candidates) > 1:
            st.caption("The models disagree. Choose the value you intended before confirming.")
            selected = st.selectbox(
                "Choose the number you spoke",
                candidates,
                format_func=lambda value: display_number(result["kind"], value),
                key=f"live-candidate-{result['session_id']}",
            )
        else:
            selected = candidates[0]
            st.markdown(
                f"<div class='sg-result'>"
                f"<div class='sg-big-number'>{escape(display_number(result['kind'], selected))}</div>"
                "</div>",
                unsafe_allow_html=True,
            )
        yes_col, no_col = st.columns(2)
        if yes_col.button(
            "YES, CORRECT",
            type="primary",
            key=f"live-yes-{result['session_id']}",
        ):
            result["user_confirmation"] = "YES"
            result["final_verified_number"] = selected
            result["user_correction"] = ""
            append_event_if_requested(result, "USER_CONFIRMED")
            st.rerun()
        if no_col.button(
            "NO, INCORRECT",
            key=f"live-no-{result['session_id']}",
        ):
            st.session_state["correction_requested"] = True
            st.rerun()

    if st.session_state["correction_requested"] and not result.get(
        "user_confirmation"
    ):
        with st.form(f"correction-form-{result['session_id']}"):
            correction = st.text_input("Enter the number you intended to say")
            submitted = st.form_submit_button("Save correction")
        if submitted:
            try:
                corrected = validate_correction(
                    result["kind"], correction, result.get("expected_len")
                )
            except ValueError as error:
                st.error(str(error))
            else:
                result["user_confirmation"] = "CORRECTED"
                result["user_correction"] = str(corrected)
                result["final_verified_number"] = corrected
                append_event_if_requested(result, "USER_CORRECTED")
                st.session_state["correction_requested"] = False
                st.rerun()


with tab_try:
    st.markdown('<div class="sg-shell">', unsafe_allow_html=True)
    header_left, header_right = st.columns([4, 1])
    with header_left:
        st.markdown(
            "<div class='sg-brand'>SankhyaGuard</div>"
            "<div class='sg-subtitle'>Voice Number Verification</div>",
            unsafe_allow_html=True,
        )
    with header_right:
        st.markdown("<div class='sg-ready'>● Ready</div>", unsafe_allow_html=True)

    capture_event = voice_orb(max_seconds=15, key="voice-orb-recorder")
    if (
        isinstance(capture_event, dict)
        and capture_event.get("event_id") != st.session_state["voice_event_id"]
    ):
        st.session_state["voice_event_id"] = capture_event.get("event_id")
        if capture_event.get("state") == "recording":
            st.session_state["voice_recording"] = None
            st.session_state["live_result"] = None
            st.session_state["voice_capture_error"] = ""
        elif capture_event.get("error"):
            st.session_state["voice_recording"] = None
            st.session_state["voice_capture_error"] = str(capture_event["error"])
        elif capture_event.get("audio_base64"):
            try:
                recorded_bytes = base64.b64decode(
                    capture_event["audio_base64"], validate=True
                )
                recorded_duration = validate_wav(recorded_bytes)
            except (binascii.Error, ValueError, AudioValidationError) as error:
                st.session_state["voice_recording"] = None
                st.session_state["voice_capture_error"] = (
                    f"The browser recording could not be validated: {error}"
                )
            else:
                if len(recorded_bytes) > MAX_AUDIO_BYTES:
                    st.session_state["voice_recording"] = None
                    st.session_state["voice_capture_error"] = (
                        "The recording is too large to process safely."
                    )
                else:
                    st.session_state["voice_recording"] = {
                        "bytes": recorded_bytes,
                        "duration": recorded_duration,
                        "event_id": capture_event["event_id"],
                    }
                    st.session_state["voice_capture_error"] = ""
                    st.session_state["live_result"] = None
                    st.session_state["correction_requested"] = False

    if st.session_state["voice_capture_error"]:
        st.error(st.session_state["voice_capture_error"])
    if st.session_state["demo_load_error"]:
        st.error(st.session_state["demo_load_error"])

    live_enabled = st.toggle(
        "Enable LIVE MODE",
        value=False,
        help="Off means no Prisma requests can be made.",
        key="live_mode",
    )
    st.markdown(
        "<div class='sg-warning'>Live transcription sends the recording to Gnani AI / Prisma "
        "and may consume credits. Processing sends two requests: Prisma v2.5 and Prisma v3.0. "
        "No request is made until you explicitly click Process recording.</div>",
        unsafe_allow_html=True,
    )
    if live_enabled:
        st.warning("LIVE MODE ON — each processed recording can use two API calls.")
    live_acknowledged = st.checkbox(
        "I understand that processing may use Gnani AI API credits.",
        value=False,
        key="live-credit-acknowledgement",
    )
    language = st.selectbox(
        "Language",
        options=("en", "kn", "hi"),
        format_func=lambda code: LANGUAGE_NAMES[code],
        key="live-language",
    )
    kind = st.radio(
        "Number type",
        options=("digits", "amount"),
        format_func=lambda value: "Phone / PIN digits" if value == "digits" else "Amount",
        horizontal=True,
        key="live-kind",
    )
    expected_len = None
    if kind == "digits":
        digit_length = st.number_input(
            "Expected digit count (0 means unknown)",
            min_value=0,
            max_value=20,
            step=1,
            key="live-digit-length",
        )
        expected_len = int(digit_length) or None

    recording = st.session_state["voice_recording"]
    audio_bytes = recording["bytes"] if recording else b""
    duration = recording["duration"] if recording else None
    validation_error = ""
    if audio_bytes:
        if st.session_state["loaded_demo_audio_id"]:
            st.caption(
                f"Selected demo clip: {st.session_state['loaded_demo_audio_id']}"
            )
        st.audio(audio_bytes, format="audio/wav")
        st.caption(f"Recording ready: {duration:.1f} seconds. Listen before processing.")

    save_locally = st.checkbox(
        "Save transcripts and number to a local evaluation log",
        value=False,
        help="This stores transcript/number values in results/live_sessions.csv. Audio is not saved.",
        key="save-live-session",
    )
    fingerprint = (
        audio_fingerprint(audio_bytes, LANGUAGE_CODES[language], kind, expected_len)
        if audio_bytes and not validation_error
        else ""
    )
    attempted = fingerprint in st.session_state["processed_fingerprints"] if fingerprint else False
    if attempted:
        st.info(
            "This recording was already submitted in this app session and will not be sent again. "
            "Record a new clip if you choose to make another request."
        )
    process_clicked = st.button(
        "Process recording (2 Prisma requests)",
        type="primary",
        disabled=(
            not live_enabled
            or not live_acknowledged
            or not audio_bytes
            or bool(validation_error)
            or attempted
        ),
        key="process-live-recording",
    )
    if process_clicked and audio_bytes and duration is not None:
        st.session_state["processed_fingerprints"].add(fingerprint)
        session = {
            "session_id": new_session_id(),
            "fingerprint": fingerprint,
            "kind": kind,
            "language": language,
            "expected_len": expected_len,
            "recording_duration_seconds": round(duration, 3),
            "save_locally": save_locally,
            "api_request_ids": [],
            "api_status": "STARTED",
        }
        v25_response = None
        v30_response = None
        try:
            with st.spinner("Understanding your number with Prisma v2.5..."):
                v25_response = prisma_client.transcribe(
                    audio_bytes, "recording.wav", LANGUAGE_CODES[language], "v25"
                )
            session["api_request_ids"].append(
                str(v25_response.get("request_id") or "")
            )
            session["transcript_v25"] = v25_response["transcript"]
            if not session["transcript_v25"].strip():
                raise ValueError("Prisma v2.5 returned an empty transcript.")
            output = v25_response.get("output")
            session["literal_v25"] = (
                output.get("literal", "")
                if isinstance(output, dict)
                and isinstance(output.get("literal", ""), str)
                else ""
            )
            with st.spinner("Comparing the second real model reading..."):
                v30_response = prisma_client.transcribe(
                    audio_bytes, "recording.wav", LANGUAGE_CODES[language], "v30"
                )
            session["api_request_ids"].append(
                str(v30_response.get("request_id") or "")
            )
            session["transcript_v30"] = v30_response["transcript"]
            if not session["transcript_v30"].strip():
                raise ValueError("Prisma v3.0 returned an empty transcript.")
            evaluated = evaluate_transcripts(
                v25_response, v30_response, kind, expected_len
            )
            session.update(
                {
                    "api_status": "SUCCESS",
                    "views": evaluated["views"],
                    "parsed_v25": evaluated["parsed_v25"],
                    "parsed_v30": evaluated["parsed_v30"],
                    "guard": evaluated["guard"],
                    "guard_decision": evaluated["guard"]["decision"],
                    "guard_reasons": evaluated["guard"]["reasons"],
                    "user_confirmation": "",
                    "user_correction": "",
                    "final_verified_number": "",
                }
            )
        except (prisma_client.PrismaError, ValueError, KeyError) as error:
            session["api_status"] = (
                "PARTIAL" if v25_response is not None else "FAILED_OR_UNKNOWN"
            )
            session["error_message"] = str(error)
            if isinstance(error, prisma_client.PrismaError) and error.request_id:
                session["api_request_ids"].append(error.request_id)
            if v25_response is not None and v30_response is None:
                session.setdefault("transcript_v25", v25_response.get("transcript", ""))
                session.setdefault("literal_v25", "")
            if v30_response is not None:
                session.setdefault("transcript_v30", v30_response.get("transcript", ""))
        st.session_state["live_result"] = session
        st.session_state["correction_requested"] = False
        if save_locally:
            append_event_if_requested(session, "TRANSCRIPTION_RESULT")
        st.rerun()

    current_result = st.session_state.get("live_result")
    if current_result and current_result.get("fingerprint") != fingerprint:
        current_result = None
    if current_result:
        show_live_result(current_result)

    with st.expander("Replay saved clean-pilot examples"):
        st.caption(
            "Replay does not make API calls. Pilot outputs are separate from new live sessions."
        )
        replay_rows, replay_warnings = load_replay_rows()
        for warning in replay_warnings:
            st.warning(warning)
        if replay_rows:
            replay_labels = [
                f"{row['id']} | {row['condition']} | {row['kind']} | {row['language']}"
                for row in replay_rows
            ]
            selected_replay = st.selectbox(
                "Choose a saved pilot clip",
                replay_labels,
                key="replay-pilot-selection",
            )
            show_replay_case(replay_rows[replay_labels.index(selected_replay)])
        else:
            st.warning("No complete pilot examples are available to replay.")
    st.markdown("</div>", unsafe_allow_html=True)

with tab_demo:
    st.subheader("Demo Audios")
    st.caption(
        "Choose one of the bundled WAV clips to preview and load it into Try it. "
        "Selecting or loading a clip does not call Prisma or use credits."
    )
    st.info(
        "To transcribe a selected clip, open Try it, enable LIVE MODE, acknowledge "
        "possible API credits, and click Process recording. That sends two Prisma requests."
    )
    demo_rows, demo_warnings = load_demo_audio_rows()
    for warning in demo_warnings:
        st.warning(warning)
    demo_by_id = {row["id"]: row for row in demo_rows}
    language_columns = st.columns(3)
    for column, language_code in zip(language_columns, ("en", "kn", "hi")):
        with column:
            st.markdown(f"### {LANGUAGE_NAMES[language_code]}")
            language_rows = [
                row for row in demo_rows if row["language"] == language_code
            ]
            if not language_rows:
                st.caption("No demo audio files are available.")
            for row in language_rows:
                clip_id = row["id"]
                label = "Phone / PIN" if row["kind"] == "digits" else "Amount"
                st.button(
                    f"{clip_id} · {label}",
                    key=f"select-demo-{clip_id}",
                    on_click=select_demo_audio,
                    args=(clip_id,),
                    width="stretch",
                )
    selected_demo_id = st.session_state.get("selected_demo_audio")
    selected_demo = demo_by_id.get(selected_demo_id)
    if selected_demo is None and selected_demo_id:
        st.warning(f"The selected demo clip is not available: {selected_demo_id}.")
    elif selected_demo is not None:
        st.markdown(f"### Preview {selected_demo['id']}")
        try:
            preview_bytes = selected_demo["audio_path"].read_bytes()
        except OSError as error:
            st.error(f"Could not read the selected audio file: {error}")
        else:
            preview_col, load_col = st.columns([3, 1])
            preview_col.audio(preview_bytes, format="audio/wav")
            load_col.button(
                "Load into Try it",
                key=f"load-demo-{selected_demo['id']}",
                type="primary",
                on_click=load_selected_demo_audio,
                args=(
                    selected_demo["id"],
                    selected_demo["language"],
                    selected_demo["kind"],
                    selected_demo["expected_len"],
                ),
                width="stretch",
            )
            st.caption(
                "After loading, switch to Try it to process the clip using the existing "
                "Live Mode and credit-acknowledgement controls."
            )

with tab_results:
    st.subheader("Measured pilot results")
    st.caption("Seven complete clean-pilot pairs; not the full experiment.")
    chart_path = PROJECT_DIR / "results_chart.png"
    report_path = PROJECT_DIR / "RESULTS_AUTO.md"
    if chart_path.is_file():
        st.image(str(chart_path), caption="Pilot-only chart.")
    else:
        st.warning("The pilot chart is missing.")
    if report_path.is_file():
        st.markdown(report_path.read_text(encoding="utf-8"))
    else:
        st.warning("The pilot report is missing.")
    st.markdown("### Live sessions")
    st.caption(
        "New user sessions are not mixed with pilot evaluation data. Saving is opt-in and writes an append-only event log at `results/live_sessions.csv`."
    )
    session_log = PROJECT_DIR / "results" / "live_sessions.csv"
    if session_log.is_file():
        with session_log.open(encoding="utf-8", newline="") as stream:
            st.dataframe(list(csv.DictReader(stream)), width="stretch")
    else:
        st.info("No locally saved live sessions.")

with tab_how:
    st.markdown(
        """
### How verification works

1. **Record** a short number using your browser's microphone. The audio stays in memory until you leave the app.
2. **Choose Live Mode** and acknowledge that processing may use credits.
3. **Click Process recording**. The app sends the same recording once to Prisma v2.5 and once to Prisma v3.0. Neither is called on startup, while recording, or during replay.
4. **Parse and compare**: SankhyaGuard uses the existing parser and Guard on those two actual model transcripts.
5. **Confirm or correct** the number. The final value is labeled as user-confirmed or user-corrected, not as independently verified.

The two Prisma models are from the same provider; agreement is not proof that their transcript is correct. If either call fails or returns empty text, the Guard is not given fabricated data. The audio is never saved to disk.
"""
    )
