# SankhyaGuard — Day 8 Completion Report

## Scope that was run

The original Day 8 request covered all 72 clips in three audio conditions: clean, phone, and SNR 5, with two Prisma models. The user then chose the smaller, currently supported scope: the existing **clean 8-clip pilot only**, with a maximum credit spend of 500.

This report covers that approved smaller scope. Phone and SNR 5 were not run.

## Dataset and saved results

The dataset contains 72 clips: 24 English, 24 Kannada, and 24 Hindi. The pilot subset contains eight clean clips: four English, three Kannada, and one Hindi.

Seven clips already had complete v2.5/v3.0 pairs. The remaining safe, uncached item was `hi_11` with Prisma v3.0. The earlier `hi_11` v2.5 HTTP 504 response was left untouched and was not retried.

The approved command was:

```powershell
.\.venv\Scripts\python.exe run_views.py --pilot --id hi_11 --model prisma-v3.0 --live
```

The dry run showed one missing response, the clean `hi_11` WAV was present, and no existing call was being retried. The runner then received the required `SEND` confirmation.

## Calls and model coverage

| Language | Clean clips | Prisma v2.5 successful | Prisma v3.0 successful | Complete pairs |
|---|---:|---:|---:|---:|
| English | 4 | 4 | 4 | 4 |
| Kannada | 3 | 3 | 3 | 3 |
| Hindi | 1 | 0 | 1 | 0 |
| **Total** | **8** | **7** | **8** | **7** |

The new Day 8 request, `hi_11` with Prisma v3.0, succeeded with HTTP 200. The existing `hi_11` Prisma v2.5 result remains an HTTP 504, so that clip still does not have a complete pair.

The current call log contains 15 successful calls, one HTTP 504 failure, and one cache-hit entry. During this Day 8 run:

- New API requests: **1**
- Successful new requests: **1**
- Failed new requests: **0**
- Reused cached results while building the CSV: **the existing seven complete pairs**

No phone or SNR 5 responses exist from this experiment.

## Evaluation

The new, separate results file was evaluated with the existing metrics and denominators:

```text
Rows: input=8 evaluated=7 skipped=1
Skipped (unavailable_model_response): 1 [hi_11]
group            n  A: wrong  G: wrong  G: asks  caught needless
ALL              7         3         2        1       1        0
en               4         0         0        0       0        0
kn               3         3         2        1       1        0

G wrong-and-silent: 2/7  |  G asks on 1/7  |  A's errors caught by G: 1/3
```

`A` is the first view (Prisma v2.5); `G` is the guard using the available paired views. The Hindi row is skipped because v2.5 is unavailable after its HTTP 504. The successful v3.0 transcript alone is not treated as a complete paired evaluation.

These are clean-pilot results only. They are not results for all 72 clips or for phone/SNR 5 audio.

## Credit reporting

Before the call, the user reported a balance of 4,999 out of 5,000 credits. The call log marks the new request as a paid call, but no post-call balance was available during this task. Therefore, the exact number of credits consumed—and whether the call stayed within the 500-credit cap—cannot be verified from the project files. No credit amount is estimated here.

## Tests run

All local tests passed:

```text
test_numparse.py       All tests passed
test_guard.py          Guard tests passed
test_evaluate.py       Evaluator tests passed
test_run_views.py      Runner language-filter tests passed
test_build_results.py Result-builder tests passed
```

The evaluator was also run on the new saved Day 8 CSV and reported the counts and metrics above.

## Files created or modified

Created during this Day 8 execution:

- `results/raw/hi_11__prisma-v3.0.json` — the new successful response.
- `results/day8_clean_pilot_results.csv` — built from saved responses; the previous Day 7 CSV was preserved.
- `DAY8_COMPLETION_REPORT.md` — this report.

Updated during the Day 8 local-preparation work:

- `evaluate.py` — reports input/evaluated/skipped counts and skip reasons while preserving metric definitions.
- `run_views.py` — adds a language filter without changing live confirmation or cache protections.
- `build_results.py` — adds a cached-response all-dataset option and keeps existing subset behavior.
- `results/calls_log.csv` — appended the single successful Day 8 request.
- `test_evaluate.py`, `test_run_views.py`, and `test_build_results.py` — added local regression tests.

No raw response was overwritten. No files were staged, committed, or pushed.

## Completion status and remaining work

**Day 8 is not fully complete.** The approved clean pilot subset was refreshed with the missing v3.0 result, but the Hindi pair remains incomplete because its earlier v2.5 request failed. The requested phone and SNR 5 conditions were not run, and the full 72-clip experiment was not run.

The next step is to check the credit balance in the provider dashboard and record the actual post-call balance before claiming a verified credit cost. Any further API work for phone/SNR 5 or the full dataset requires a condition-aware runner and result-file layout so that different audio conditions cannot share or confuse the same cache entry.
