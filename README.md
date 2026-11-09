# SankhyaGuard

SankhyaGuard is a local Flask prototype for checking whether a spoken number transcript should be accepted or confirmed. It targets digit strings and amounts in English, Kannada, and Hindi. It uses Gnani AI Prisma speech-to-text; it does not train or replace a speech-recognition model. The earlier Streamlit interface remains available as an alternative.

The app compares two Prisma readings, parses them with the project's number parser, and applies the existing Guard. Agreement is not proof of correctness: two readings can make the same mistake. Treat the results as an experiment, not as a guarantee for financial or identity decisions.

## Features

- **Streamlit alternative:** retain the existing Try it recording flow, 72-clip Demo Audios browser, results view, and optional live-session log.
- **Premium web interface:** Live recording, plus a Demo Audios browser with three language columns. Previewing a clip is local; processing requires an explicit credit-consent checkbox and a separate button press.
- **Replay:** inspect only complete, saved clean-pilot outputs. Replay does not make API requests.
- **Confirmation:** accept a suggested number or enter a locally validated correction; user confirmation is distinct from model output.
- **Offline tests:** check parser, Guard, replay, UI and API-client behavior without contacting Prisma.

The web prototype does not need a database. Browser speech playback uses the device's built-in speech synthesis and does not call Timbre or use API credits. The microphone recording is held temporarily while the local server converts it and sends it to Prisma after consent; the app does not save that audio.

## Requirements

- Windows 10/11
- Python 3.12
- Optional: a Gnani AI API key for explicitly initiated live transcription

## Set up on Windows

Open PowerShell in this project folder and run:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If `.venv` already exists, you can skip the first command.

## Run the app

Run the premium Flask interface from the project folder:

```powershell
.\.venv\Scripts\python.exe server.py
```

Open `http://127.0.0.1:5000/` in Chrome. The server binds to this computer only. Stop it with **Ctrl+C**. To use the previous Streamlit interface instead:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the local URL printed by Streamlit, usually `http://localhost:8501`.

## Optional live Prisma requests

Live processing in either interface is off by default. Previewing a demo clip or replaying a saved result does not make API calls. The Flask interface requires all of these actions:

1. Provide a Gnani AI key in a local `.env` file as `GNANI_API_KEY=...` (or as an environment variable).
2. Check the on-screen notice that API credits may be used.
3. Explicitly click **Process selected clip** or start recording in Live mode.

Processing sends two requests for the selected recording: Prisma v2.5 and Prisma v3.0. A spoken reply during confirmation can send one additional Prisma request. The server limits a run to 24 attempted Prisma requests by default; `SG_MAX_CALLS` can lower or raise this limit up to 1000. Review your account's current pricing and credit balance before processing. Never commit or share `.env`; it is excluded by `.gitignore`. The app does not automatically retry a failed request.

`main.py` is an older standalone test script, not the Streamlit app. It sends a Prisma request when `audio/clip1.mp3` and an API key are present; do not run it unless you deliberately intend that request.

## Run the focused offline tests

```powershell
.\.venv\Scripts\python.exe -m unittest test_app test_voice_orb_component test_live_workflow test_prisma_client test_replay_data test_guard test_numparse
```

These tests mock the API client where needed. A passing test run does not demonstrate live API access or consume credits.

Run the premium interface's focused offline checks with:

```powershell
.\.venv\Scripts\python.exe -m unittest test_core test_server test_replay_data
```

## Project map

- `server.py` and `static/index.html` — local Flask interface, explicit live-processing gate, 72-clip browser, pilot replay, and result display.
- `core.py` — parser/Guard response shaping and spoken-reply intent parsing for the Flask interface.
- `test_core.py` and `test_server.py` — offline checks for the Flask logic and HTTP routes.
- `app.py` — retained Streamlit interface, Demo Audios selection, explicit live-processing gate, and result display.
- `main.py` — legacy one-request test script; see the warning above.
- `voice_orb_component.py` and `voice_orb_component/` — browser microphone orb and WAV capture.
- `prisma_client.py` — validated Prisma HTTP client; loads credentials only when called.
- `live_workflow.py` — WAV validation, transcript parsing/Guard evaluation, correction validation, and opt-in event logging.
- `numparse.py` and `guard.py` — language-aware number parsing and ACCEPT/CONFIRM decision logic.
- `replay_data.py` — validates saved pilot rows and locates pilot audio.
- `dataset_script.csv` — 72-item dataset manifest. It is not evidence that all items have model results.
- `results/day8_clean_pilot_results.csv` — local pilot results; the `results/` folder is excluded from Git.
- `DAY10_PILOT_REPORT.md` — detailed account of the saved clean pilot and its limitations.

## Evaluation status and limitations

The saved clean pilot has 8 rows, of which 7 have complete paired Prisma outputs. It is not the full 72-clip experiment. Full clean and phone result files and results for phone/SNR conditions are not available in the current project state. Pilot counts are small and should not be treated as statistically significant or as a broad performance claim. The written labels have not been independently re-verified against every recording.

Local audio folders (`audio/`, `audio_phone/`, `audio_snr5/`, `audio_snr10/`, and `raw_audio/`), `.env`, the virtual environment, live logs, and TTS cache are ignored by Git. This repository is public, so do not commit credentials, private recordings, or personal data; anyone can view and fork the code, and GitHub Actions history and logs are public.

## Current development state

This is a local engineering prototype. The current app has been exercised with offline tests and local browser checks. The microphone and live Prisma workflow should be tested separately and deliberately; no live request is implied by installing or starting the app.
