# SankhyaGuard — Day 11 Live App Implementation Report

## Status

The app now includes a real microphone-recording interface and a guarded live Prisma workflow. The live workflow is off by default and was not used during implementation.

**Live API was not tested during implementation.**

No Prisma/Gnani or Timbre request was sent, no API credits were used, `.env` was not opened or read, and Day 12 was not started.

## What was inspected

- `app.py`, `guard.py`, `numparse.py`, `prisma_client.py`, `ui_helpers.py`, `readback.py`, and `replay_data.py`.
- Existing evaluation and result-generation code, including `evaluate.py` and `run_views.py`.
- The existing Day 8 pilot CSV, pilot report, chart, demo IDs, Day 10 report, and previous Day 11 completion report.
- Existing tests and the installed Streamlit environment.
- Gnani's official STT documentation:
  - [STT API request](https://docs.gnani.ai/api/STT/speech-to-text.md)
  - [Prisma v3 model](https://docs.gnani.ai/api/STT/models/prisma-v3.md)
  - [API error responses](https://docs.gnani.ai/api/introduction/errors.md)

The installed Streamlit environment was checked for microphone-recording packages. A small local custom Streamlit component was used instead, with no additional package install.

## Live workflow implemented

- `app.py` provides **Try it**, **Demo Audios**, **Results**, and **How it works** tabs and keeps the saved clean-pilot replay available.
- **Demo Audios** lists the 72 manifest-matched WAV clips in three language columns (24 each for English, Kannada, and Hindi). Selecting and previewing a bundled clip is offline; loading it into **Try it** still requires the existing Live Mode, credit acknowledgement, and explicit process action before Prisma can be called.
- The main page uses a midnight-black background, electric-cobalt primary color, and acid-lime accent. It has a brief title splash: SankhyaGuard appears with a 3D-style entrance, then fades into the app.
- The page background uses CSS-only pseudo-elements behind the Streamlit main content to create a subtle cobalt resonance sphere, orbit ellipses, and acid-lime sound trace. These are pointer-inert, cannot cover app controls, adapt on mobile, and stop moving for reduced-motion preferences. No external image or library is used.
- The cyan/violet orb was replaced with a smaller cobalt-and-lime orb (150–205 px, responsive sizing) so its instructions fit clearly beneath it. The orb itself starts recording on the first tap and stops on the next tap. The embedded browser component reads microphone amplitude locally, expands/contracts the orb, and shifts its glow with the user's voice. It captures PCM audio in memory, converts it to a 16 kHz WAV, and passes the recording to Streamlit. It stops automatically after 15 seconds and supports keyboard focus and reduced-motion preferences.
- After recording, Streamlit provides audio playback. Recording does not make an API request.
- The app checks that the uploaded WAV is readable PCM, non-empty, between 0.1 and 15 seconds, and no larger than 10 MB before enabling processing.
- Live Mode defaults to **OFF**. Processing additionally requires the user's credit acknowledgement, a valid recording, and a deliberate **Process recording (2 Prisma requests)** click. Startup, recording, tab changes, replay, and UI reruns do not invoke Prisma.
- The same recorded audio is sent sequentially to Prisma v2.5 and v3.0. Each model call is a separate paid request. The app does not automatically retry. It prevents resubmitting the same recording and settings within the current app session.
- If either response fails or returns an empty transcript, the app displays the available actual transcript/error and does not run the Guard with missing or invented data.
- The verified request shape follows the official docs and the project's existing runner: `POST https://api.vachana.ai/stt/v3`, `X-API-Key-ID` authentication, multipart `audio_file`, `language_code`, and `format=transcribe`; the v3 call also selects `prisma-v3.0`. Credentials are loaded lazily only when the explicit live action reaches the client. No key is hardcoded or shown.
- `live_workflow.py` uses the existing `numparse.py` parser and `guard.py` decision logic. It parses both real transcripts and gives both views to the existing Guard. User confirmation is distinct from the Guard decision, and user confirmation is not presented as independent proof.
- The user can confirm a candidate or enter a correction validated by the existing parser. The original transcripts and Guard decision remain unchanged, and the final number is labeled as user-confirmed or user-corrected.
- Local session logging is opt-in. It appends events to `results/live_sessions.csv`, separate from pilot results, and stores transcript, parsed values, Guard result/reasons, user action, final number, request IDs, status, language/kind, timestamp, and duration. Raw audio and API keys are not saved.
- The Results tab retains the pilot chart and report with explicit pilot-only labeling; live sessions are displayed separately.

Because the existing Guard requires multiple views, a live result is based on two actual Prisma model responses. Those models are from the same provider; agreement is not independent ground truth.

## Files created or modified

- Created `app.py`.
- Created `prisma_client.py`.
- Created `live_workflow.py`.
- Created `voice_orb_component.py` and `voice_orb_component/index.html` for the interactive microphone orb.
- Created `.streamlit/config.toml` for the dark app theme.
- Created `test_live_workflow.py`, `test_prisma_client.py`, and `test_voice_orb_component.py`.
- Updated `test_app.py` with offline checks for the default-off gate, no processing on startup/UI reruns, demo clip loading without API calls, and confirmation/correction actions.
- Updated `test_readback.py` to remove the obsolete expectation that the Prisma client is a disabled stub; existing TTS-disabled checks remain.
- Added a status note to `DAY11_COMPLETION_REPORT.md` pointing to this current live-app report.
- Created this report.

Existing pilot CSVs, Day 10 outputs, `demo_ids.txt`, `.gitignore`, `.env`, audio files, and TTS cache were not changed. No files were staged, committed, tagged, pushed, or deleted.

## Tests and checks

Using `.venv\Scripts\python.exe`:

- `python -m unittest test_numparse test_guard test_make_report test_readback test_replay_data test_live_workflow test_prisma_client test_app test_voice_orb_component` — **35 tests passed**.
- Manually invoked five function-style tests from `test_evaluate.py`, `test_build_results.py`, and `test_run_views.py` — **all passed**. These test local evaluation/build/selection behavior; they do not run the live runner.
- `python -m py_compile app.py prisma_client.py live_workflow.py voice_orb_component.py test_app.py test_live_workflow.py test_prisma_client.py test_voice_orb_component.py` — passed.
- The embedded JavaScript was syntax-checked with `node --check`.
- The mocked API client tests checked multipart request construction, response parsing, HTTP failure handling, input validation, and no automatic network retry. These are mock tests, not evidence of live API success.
- Streamlit `AppTest` checked startup without a Prisma call, Live Mode off by default, processing disabled without a recording, no Prisma calls after toggling/acknowledging, and user confirmation/correction behavior.
- Demo Audios verification: 72 manifest-matched WAVs (24 per language); loading a clip into **Try it** passed without invoking Prisma. The focused app, component, workflow, client, replay, Guard, and parser suite passed 25 tests.
- The app returned HTTP 200 locally. Browser inspection confirmed that the custom orb component loaded, the old separate microphone control is gone, Live Mode defaults off, processing is disabled until a recording exists, and the Results and How it works tabs render. A browser screenshot was reviewed.
- The browser microphone was not used to record a real sample, and no live request was made. Browser visual inspection does not verify physical microphone permissions or Gnani API access.

`pytest` is not installed in the existing virtual environment, so no package was installed; the function-style offline tests were invoked directly instead.

## Run the application

Open PowerShell in the project folder and run:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

To stop the local server, press **Ctrl+C** in that PowerShell window.

The app starts with **LIVE MODE OFF**. To make a live test later, the user must choose Live Mode, acknowledge possible credit use, record and listen to a number, then explicitly press **Process recording**. That deliberate action makes two paid API requests. Do not use it until ready to spend credits.

## Remaining limitations and next step

- Actual microphone permission and captured audio were not tested in this implementation session. The orb's sound-reactive behavior is implemented in browser code, but should be tried locally with microphone permission before any paid API test.
- No Timbre/TTS request is part of this flow.
- The live log contains sensitive spoken numbers and transcripts if the user opts in; keep it private. The `results/` folder is ignored by Git.
- The pilot remains only seven complete clean pairs and is not mixed with live sessions or presented as full-experiment data.

**Next step:** run the command above and inspect the screen in Live Mode OFF. If you later approve a paid live test, make one short recording, listen to it, and deliberately process it; do not treat the mock tests as proof that the real API has been exercised.
