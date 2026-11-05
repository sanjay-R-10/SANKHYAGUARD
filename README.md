# SankhyaGuard

SankhyaGuard is a Streamlit prototype for checking whether a spoken number transcript should be accepted or confirmed. It targets digit strings and amounts in English, Kannada, and Hindi. It uses Gnani AI Prisma speech-to-text; it does not train or replace a speech-recognition model.

The app compares two Prisma readings, parses them with the project's number parser, and applies the existing Guard. Agreement is not proof of correctness: two readings can make the same mistake. Treat the results as an experiment, not as a guarantee for financial or identity decisions.

## Features

- **Try it:** record a short number with the microphone orb, listen to the recording, and optionally process it.
- **Demo Audios:** browse and preview the 72 local WAV clips (24 per language). Loading a clip into Try it is offline.
- **Results:** view the clean-pilot report/chart and any separately saved live-session log.
- **Confirmation:** accept a suggested number or enter a correction; user confirmation is distinct from model output.
- **Offline tests:** check parser, Guard, replay, UI and API-client behavior without contacting Prisma.

The prototype does not need a database: selected audio and results are kept in the current Streamlit session, and saving a live-session event log is optional.

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

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the local URL printed by Streamlit, usually `http://localhost:8501`. Stop the app with **Ctrl+C** in PowerShell.

## Optional live Prisma requests

Live Mode is off by default. Demo clip selection, preview, recording, and loading audio do not make API calls. Live processing is enabled only after all of these actions:

1. Provide a Gnani AI key in a local `.env` file as `GNANI_API_KEY=...` (or as an environment variable).
2. Turn on **Enable LIVE MODE**.
3. Acknowledge that API credits may be used.
4. Click **Process recording**.

Processing sends two requests for the selected recording: Prisma v2.5 and Prisma v3.0. Review your account's current pricing and credit balance before processing. Never commit or share `.env`; it is excluded by `.gitignore`. The app does not automatically retry a failed request.

`main.py` is an older standalone test script, not the Streamlit app. It sends a Prisma request when `audio/clip1.mp3` and an API key are present; do not run it unless you deliberately intend that request.

## Run the focused offline tests

```powershell
.\.venv\Scripts\python.exe -m unittest test_app test_voice_orb_component test_live_workflow test_prisma_client test_replay_data test_guard test_numparse
```

These tests mock the API client where needed. A passing test run does not demonstrate live API access or consume credits.

## Project map

- `app.py` — Streamlit interface, Demo Audios selection, explicit live-processing gate, and result display.
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

Local audio folders (`audio/`, `audio_phone/`, `audio_snr5/`, `audio_snr10/`, and `raw_audio/`), `.env`, the virtual environment, live logs, and TTS cache are ignored by Git. Keep the repository private if you later choose to publish source code containing project details, and invite only people you intend to grant access.

## Current development state

This is a local engineering prototype. The current app has been exercised with offline tests and local browser checks. The microphone and live Prisma workflow should be tested separately and deliberately; no live request is implied by installing or starting the app.
