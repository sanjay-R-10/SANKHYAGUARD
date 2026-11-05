# SankhyaGuard — Day 11 Completion Report

> Status note (live-app update): This report describes the earlier offline-only
> Day 11 implementation. It has since been extended with the gated live voice
> workflow described in [DAY11_LIVE_APP_IMPLEMENTATION_REPORT.md](./DAY11_LIVE_APP_IMPLEMENTATION_REPORT.md).
> Read that report for the current app behavior and verification status.

## Scope

Day 11's Streamlit application was implemented as an offline, saved-results demo. Day 12 was not started.

No Prisma/Gnani or Timbre calls were made; no credits were spent; `.env` was not read; and no experiment results, Day 10 reports, or charts were changed. No files were staged, committed, tagged, or pushed.

## Original Day 11 requirements

The supplied Claude instructions asked for a Streamlit app with Try it, Results, and How it works tabs; saved Replay Mode; side-by-side normal-app/Guard decisions; candidates and disputed digits; confirmation wording; saved result audio; chart and limitations; safe handling of missing/incomplete data; and no accidental paid requests.

The instructions also supplied starter code for `prisma_client.py`, `ui_helpers.py`, `readback.py`, `tts_test.py`, `test_readback.py`, and `app.py`. Those files did not exist before this work, so new implementations were created from the supplied requirements and starter behavior.

## Implemented files

- `app.py` — Streamlit application with Try it, Results, and How it works tabs. It opens in Replay Mode and contains no live-mode selector or call button.
- `replay_data.py` — validates the pilot CSV schema and demo IDs, filters incomplete pairs, and resolves audio paths safely.
- `ui_helpers.py` — preserves the supplied Indian number formatting, reason text, candidate cards, and disputed-digit highlighting.
- `readback.py` — preserves the supplied English, Kannada, and Hindi confirmation text and deterministic cache keys. It reuses existing cached audio when present; uncached synthesis raises an explicit offline-disabled error.
- `prisma_client.py` — provides the expected `transcribe` interface but raises `LiveCallsDisabled` immediately. It does not import environment loaders, read credentials, or send requests.
- `tts_test.py` — safe placeholder that reports that paid synthesis is disabled; it does not call `synthesize`.
- `test_readback.py` — offline tests for formatting, language templates, cache keys, cached audio reuse, reason text, highlighting, and disabled paid operations. Cache files used by tests are confined to a temporary directory.
- `test_replay_data.py` — tests for pilot loading, invalid/empty IDs, incomplete pairs, missing files/columns, and audio path handling.
- `test_app.py` — Streamlit smoke test; verifies the app starts, has a saved-pilot selector, and exposes only disabled paid controls.
- `DAY11_COMPLETION_REPORT.md` — this report.

No existing project source, result CSV, Day 10 output, or `.gitignore` was modified.

## Replay Mode

The app loads `results/day8_clean_pilot_results.csv` using its actual columns, including `view_v2_5` and `view_v3_0`. It does not assume the absent `results_*_all.csv` files or silently translate the full-results schema.

`demo_ids.txt` is checked against the saved rows and `dataset_script.csv`. Only complete paired rows are offered. The incomplete `hi_11` row is excluded, and the app reports that incomplete rows were skipped. The three selected replay rows are `kn_01`, `en_01`, and `kn_11`; each has a matching clean audio file in the project.

The app displays the saved views, the existing parser's interpretation, the first-view comparison, the Guard decision, candidates, and confirmation wording. Missing audio produces a warning; the saved transcript can still be viewed. The dataset label is hidden until the user chooses to reveal it.

## Live Prisma and Timbre safety

- **Prisma:** disabled. The UI does not offer Live Mode, and the `prisma_client.transcribe` function always raises without making a request.
- **Timbre:** paid synthesis disabled. The app shows confirmation text and a disabled audio control when no cache entry exists. Existing cached audio may be played without synthesis.
- `.env` is not loaded by the new modules. The app does not import `main.py` or `run_views.py`.
- `tts_test.py` was not run.

This is a deliberate safety adaptation to the supplied live-request starter code. The app is for offline replay only.

## Results tab and limitations

The Results tab displays the existing pilot-only `results_chart.png` and `RESULTS_AUTO.md`. These remain labeled as pilot data, not full 72-clip results. The app explains that only seven model pairs are complete, `hi_11` is incomplete, no phone/SNR model results are available, and written labels were not independently verified against the recordings.

## Tests and checks

Using `.venv\Scripts\python.exe`:

- `test_numparse.py` — passed.
- `test_guard.py` — passed.
- `test_evaluate.py` — passed.
- `test_readback.py` — 7 tests passed.
- `test_replay_data.py` — 6 tests passed.
- `test_app.py` — 1 test passed; Streamlit emitted its standard bare-mode context warning, but the test had no app exceptions.
- `test_build_results.py` — passed.
- `test_run_views.py` — passed; the test exercises the local selector only and did not run the API runner.
- `python -m unittest test_make_report.py` — 6 tests passed.
- Python syntax compilation for the new app modules and tests — passed.
- Actual replay loader — returned 3 selected complete rows (`kn_01`, `en_01`, `kn_11`), excluded one incomplete row, and found audio files for all selected clips.

The local Streamlit server was started with the existing virtual environment, returned HTTP 200 from `http://127.0.0.1:8507/`, and was then stopped. This confirms the server responded locally; **no browser-based visual test was performed**.

The new app/readback/Prisma modules were also inspected to confirm they do not load `.env`, read environment credentials, or call `requests.post`. The Prisma function is an immediate disabled stub; readback only returns an existing cache file or raises that synthesis is disabled.

## Run the application

From the project directory in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The app opens in offline Replay Mode. Do not enable live calls; they are intentionally unavailable in this build.

## Remaining limitations

- The full clean/phone experiment and analysis are still missing; this app does not claim full-experiment coverage.
- No live Prisma transcription or Timbre synthesis is available in this safe offline build.
- Replay depends on the saved pilot CSV and local audio files. Missing files are reported in the app.
- The project has no browser-based verification recorded for this task.
