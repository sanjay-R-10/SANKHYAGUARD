# SankhyaGuard — Day 10 Completion Report

## Scope and safety

This report records only the Day 10 work completed in this local session. No Day 11 or Day 12 work was started.

- No Prisma/Gnani or Timbre/TTS API calls were made.
- No credits were spent.
- `.env` was not read, displayed, or modified.
- No experiment results or raw responses were changed.
- No files were deleted.
- Nothing was staged, committed, tagged, pushed, or switched to another branch.

## Step 1 — Python packages

Step 1 was completed before this session, as confirmed in the task instructions:

- Existing virtual environment: `C:\Users\sanja\Desktop\sankhyaguard\.venv`
- Python: 3.12.10
- matplotlib: 3.11.2
- streamlit: 1.66.1

No packages were installed or reinstalled during this session.

## Step 2 — Results report

**Status: pilot report completed; full experiment report remains blocked.**

The required full-result inputs are missing:

- `results_clean_all.csv`
- `results_phone_all.csv`
- `analyse.py`
- Claude's original `make_report.py` source

Created `make_report.py`, which checks for both full input files and validates Claude's expected full-result columns before analyzing them. Since the full files are missing, it used only `results/day8_clean_pilot_results.csv` and created pilot-labeled `RESULTS_AUTO.md` and `results_chart.png`. It did not create or substitute full-result CSVs.

The pilot schema uses `view_v2_5` and `view_v3_0`, not the full-result fields `view_v25_itn`, `view_v25_literal`, and `view_v30`. The script handles that through a separate pilot-only path, without renaming columns or mixing pilot rows into a full report.

The generated pilot report reproduced the existing evaluator counts: 8 input rows, 7 evaluated pairs, 1 skipped (`hi_11`), first-view wrong 3, Guard silently wrong 2, Guard asks 1, caught 1 of 3, and needless confirmations 0. This does not complete the full clean or phone report.

## Step 3 — Select five demo clips

**Status: partially completed with three verified pilot clips; the requested five-category selection is blocked.**

`analyse.py` and its “Every row to study” output are absent. Created `demo_ids.txt` with three actual, complete pilot IDs:

1. `kn_01` — first view wrong; Guard asks.
2. `en_01` — accepted value matches the dataset label (audio not independently verified).
3. `kn_11` — silent error against the dataset label; Kannada.

Kannada is represented by `kn_01` and `kn_11`. Phone quality is unsupported because no phone-condition model results exist. The file is a pilot-only subset, not the original five-item analysis-based selection.

## Step 4 — Git safety

The existing `.gitignore` contains `tts_cache/` and the existing ignore rules were preserved.

The branch remained `master`. No Git staging, commit, tag, push, or branch change was performed.

## Files created or modified

- Created `make_report.py`, `test_make_report.py`, `RESULTS_AUTO.md`, `results_chart.png`, and `demo_ids.txt`.
- Updated `DAY10_COMPLETION_REPORT.md` with the pilot-only implementation status.
- `.gitignore` was not changed during this task; `tts_cache/` was already ignored.

No experiment CSVs, raw responses, prior Day 7–9 reports, or unrelated source scripts were modified.

## Commands and checks performed

- Checked whether each required Day 10 input/output file existed.
- Inspected the header and first two rows of `results/day8_clean_pilot_results.csv`; it had 8 rows.
- Read the opening sections of the Day 7, Day 8, and Day 9 completion reports.
- Searched project Python, Markdown, text, and CSV files for Claude's expected report columns, analysis output phrase, and report filenames; no original report code or analysis output was found.
- Inspected `.gitignore`.
- `.\.venv\Scripts\python.exe -m unittest test_make_report.py` — passed, 6 tests.
- `.\.venv\Scripts\python.exe make_report.py` and `.\.venv\Scripts\python.exe make_report.py --overwrite-generated` — generated/refreshed pilot-only report/chart and listed missing full inputs. The overwrite option was used only for the outputs created by this task.
- `.\.venv\Scripts\python.exe evaluate.py results/day8_clean_pilot_results.csv` — 8 input, 7 evaluated, 1 skipped; metrics matched the generated report.
- `test_numparse.py`, `test_guard.py`, `test_evaluate.py`, `test_build_results.py`, and `test_run_views.py` — all passed.
- Verified the three demo IDs exist in the dataset and are complete rows in the saved pilot.
- Viewed the generated chart and checked final Git status. Branch remained `master`.
- No live experiment script or API call was run.

## Remaining Day 10 tasks

To complete the full-results report and five-clip selection safely, the project still needs genuine `results_clean_all.csv` and `results_phone_all.csv` with the expected columns, plus `analyse.py` and its actual output. The original Claude report source was not available; `make_report.py` implements the stated schema and existing evaluator/Guard rules without claiming to be Claude's missing source.

## Pilot-only continuation

The subsequent pilot-only work is documented in [DAY10_PILOT_REPORT.md](./DAY10_PILOT_REPORT.md). It independently re-evaluates the eight saved clean-pilot rows using the existing evaluator and Guard, without changing the source CSV.

- Verified counts: 8 input rows, 7 evaluated pairs, and `hi_11` skipped because its model pair is incomplete.
- Verified metrics: first-view wrong 3, Guard silently wrong 2, Guard asks 1, caught 1 of 3 first-view errors, needless confirmations 0.
- [RESULTS_AUTO.md](./RESULTS_AUTO.md) and [results_chart.png](./results_chart.png) were generated by `make_report.py` in explicit pilot-only mode. The report lists the skipped row and missing full-result inputs; the chart title and annotation identify its pilot scope.
- [demo_ids_pilot.txt](./demo_ids_pilot.txt) contains three supported clean-pilot IDs: `kn_01` (wrong first view and confirmation), `en_01` (accepted value matches dataset label; audio not independently verified), and `kn_11` (silent error). The Kannada category is represented by `kn_01` and `kn_11`. Phone-quality results are unavailable, so no phone clip was selected.
- [results_chart_pilot.png](./results_chart_pilot.png) was created from the verified evaluator counts, with a clean-pilot-only title, visible denominators, and a caveat that categories overlap and the audio labels were not independently checked. It does not represent 72 clips or phone/SNR results.
- The saved pilot transcript columns can support an offline Replay Mode through a small schema adapter, but no app or adapter was built. There is no existing app schema to compare against.

This continuation does not complete the full experiment. The full clean/phone reports, full 72-clip evaluation, and analysis-based five-clip selection remain blocked by missing full-result files and missing analysis code/output. No Day 11 or Day 12 work was started.
