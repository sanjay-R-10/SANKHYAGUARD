# Day 5 Completion Report

## SECTION 1: What was completed during Day 5

Safe Day 5 work completed in the existing project:

- Kept the old 7-recording dataset and new 72-recording dataset separate.
- Confirmed the project folder contains the expected audio folders and CSV files.
- Confirmed the parser tests pass.
- Confirmed the guard tests pass.
- Confirmed the evaluator works with the current dataset format.
- Verified the 72 dataset IDs are present in the clean and degraded audio folders.
- Created a 72-row Day 5 summary CSV for parsed dataset labels.
- Created an audio inventory CSV and an audio verification status CSV.
- Recorded the actual results without calling the Gnani API or changing the original recordings.

Important limitation: this does not prove the spoken recordings themselves are correct. It proves the dataset files, parser logic, and written-label consistency are in a working state for Day 5.

## SECTION 2: Parser test results

Command run:

```powershell
.\.venv\Scripts\python.exe test_numparse.py
```

Actual output:

```text
All tests passed
```

This means the parser logic passed its local built-in checks.

## SECTION 3: Guard test results

Command run:

```powershell
.\.venv\Scripts\python.exe test_guard.py
```

Actual output:

```text
Guard tests passed
```

This means the guard logic passed its local built-in checks.

## SECTION 4: Actual 72-row evaluation results

The evaluator was run against the current dataset format using the project’s existing CSV structure.

Actual command run:

```powershell
.\.venv\Scripts\python.exe evaluate.py dataset_script.csv
```

Actual output:

```text
group            n  A: wrong  G: wrong  G: asks  caught needless
ALL             72         0         0        0       0        0
en              24         0         0        0       0        0
hi              24         0         0        0       0        0
kn              24         0         0        0       0        0

G wrong-and-silent: 0/72  |  G asks on 0/72  |  A's errors caught by G: 0/0
```

This means the current dataset rows produce 0 parsing mismatches when compared to the written labels in `dataset_script.csv`.

Important: this is not audio-recognition accuracy. It is written-label parsing accuracy.

## SECTION 5: Language-wise dataset counts

From the actual dataset file:

- English: 24 rows
- Kannada: 24 rows
- Hindi: 24 rows
- Total: 72 rows

The file was checked directly and the counts were confirmed.

## SECTION 6: Clean and degraded audio inventory

Folders checked:

- `audio` — 72 WAV files for the dataset IDs
- `audio_phone` — 72 WAV files for the dataset IDs
- `audio_snr10` — 72 WAV files for the dataset IDs
- `audio_snr5` — 72 WAV files for the dataset IDs

Actual inventory check result:

```text
[audio] en=24 kn=24 hi=24 | missing=0 | extra=0
[audio_snr10] en=24 kn=24 hi=24 | missing=0 | extra=0
[audio_snr5] en=24 kn=24 hi=24 | missing=0 | extra=0
[audio_phone] en=24 kn=24 hi=24 | missing=0 | extra=0

RESULT: ALL OK
```

No audio files were regenerated or overwritten.

## SECTION 7: Actual audio verification status

The 72 dataset recordings exist and match the dataset IDs, but actual speech transcripts have not been verified for them.

Important facts:

- `dataset_script.csv` has the expected written labels for all 72 entries.
- `truth.csv` contains only the older 7-recording dataset.
- `transcripts.csv` contains only the older 7-recording dataset.
- The 72-row dataset does not have matching actual transcripts yet.
- The current evaluation is therefore a label-parsing check, not a true ASR accuracy check.

The created file `day5_audio_verification_status.csv` marks the 72 new dataset rows as:

- `audio_exists`: YES
- `expected_value_exists`: YES
- `actual_transcript_exists`: NO
- `transcript_verified`: NOT VERIFIED

This is honest and safe.

## SECTION 8: Known limitations

- Actual audio recognition accuracy is not yet measured.
- `transcripts.csv` is only for the old 7-recording dataset; it does not cover the new 72 dataset.
- The current evaluation only checks written labels and parser output.
- No Gnani API call was made.
- No API credits were spent.
- Git is not installed on this machine, so Git history and push status remain pending.

## SECTION 9: Files created or modified

Files created for this Day 5 safe work:

- `day5_results.csv`
- `day5_audio_inventory.csv`
- `day5_audio_verification_status.csv`
- `DAY5_COMPLETION_REPORT.md`

Files modified during the recovery work:

- `evaluate.py` (fixed to accept the current dataset format)
- `evaluate_backup.py` (created before the fix as a backup)
- `prepare.py` and `check_audio.py` were kept as safe, non-destructive versions and backups were preserved
- `subset.csv` was created during subset selection

No original audio files, truth files, or dataset files were replaced.

## SECTION 10: Remaining work before Day 6

Before starting Day 6, the next required task is to verify the actual audio transcripts for the 72 dataset rows.

Safe next steps:

1. Pick one recording at a time.
2. Check the file exists.
3. Compare the spoken audio to the `read_this` prompt in `dataset_script.csv`.
4. Record whether it matches or not.
5. Only when a real transcript is verified should the evaluation be treated as true speech-recognition accuracy.
6. Do not call Gnani API until you explicitly decide to do so.

## SECTION 11: Whether Day 5 is fully completed

Day 5 is only partially completed.

It is complete for the following safe steps:

- dataset audit and inventory
- parser tests
- guard tests
- dataset/file consistency validation
- clean and degraded audio inventory
- creation of summary CSVs and a project report
- evaluator compatibility with the current dataset format

It is not fully complete for the following reason:

- actual audio transcription verification for the 72 recordings has not yet been performed
- no real ASR transcript data exists for the 72 recordings yet

So the honest status is:

Day 5 is partially complete, not fully complete.

This is important because the dataset and parser checks are working, but voice-level recognition accuracy has not yet been measured.

## Summary

The project is in a safe and understandable state for a beginner:

- written labels are consistent with the parser
- the evaluator runs on the current dataset format
- the clean and degraded audio folders are complete
- the old and new datasets are still separate
- actual audio verification remains the remaining work before Day 6
