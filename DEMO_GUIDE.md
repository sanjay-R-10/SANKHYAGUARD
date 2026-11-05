# SankhyaGuard Demo Guide

This guide is for a short, local demonstration. The commands below use the existing Python virtual environment and saved files. They do **not** call the API or spend credits.

## 1. What SankhyaGuard does

SankhyaGuard takes one or more spoken-number transcripts, converts each transcript into a number, and decides whether to `ACCEPT` the result or ask the user to `CONFIRM` it.

It is a checking layer for number transcripts. It is not a speech-recognition model. Prisma produced the saved pilot transcripts; SankhyaGuard parses and checks those transcripts.

## 2. Features that exist today

- Number parsing for supported English, Kannada, and Hindi forms in `numparse.py`.
- An `ACCEPT`/`CONFIRM` decision function in `guard.py`.
- A local evaluator in `evaluate.py`.
- A safe-by-default API runner in `run_views.py`. It supports a dry run by default and requires explicit live mode and a per-request `SEND` confirmation for uncached calls. **Do not use live mode for this demo.**
- A result builder in `build_results.py` that reads saved responses and refuses to overwrite an existing output.
- Saved clean pilot results in `results/day8_clean_pilot_results.csv`.

There is no graphical or browser-based demo application yet, and there is no `README.md`.

## 3. Open PowerShell in the project folder

In VS Code, open the project folder and choose **Terminal → New Terminal**. Confirm that the prompt is in the project folder:

```powershell
cd C:\Users\sanja\Desktop\sankhyaguard
```

The project has a local virtual environment using Python 3.12. To activate it in PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, do not change the machine’s execution policy for the demo. Run the same commands using the virtual-environment interpreter directly:

```powershell
.\.venv\Scripts\python.exe --version
```

Expected output starts with `Python 3.12`.

## 4. Run the saved local pilot evaluation

Use the Day 8 CSV so the newer saved `hi_11` v3.0 transcript is visible in the file, while the paired evaluator still correctly skips the incomplete Hindi pair:

```powershell
.\.venv\Scripts\python.exe evaluate.py results\day8_clean_pilot_results.csv
```

Expected key output:

```text
Rows: input=8 evaluated=7 skipped=1
Skipped (unavailable_model_response): 1 [hi_11]
ALL              7         3         2        1       1        0
en               4         0         0        0       0        0
kn               3         3         2        1       1        0
```

The numbers mean the evaluator saw eight pilot rows, evaluated seven complete pairs, and skipped `hi_11` because its v2.5 request returned HTTP 504. The result is only for the clean pilot—not the full dataset.

To display the saved transcripts and statuses in PowerShell:

```powershell
Import-Csv results\day8_clean_pilot_results.csv |
  Select-Object id,language,truth,v2_5_transcript,v3_0_transcript,paired_views_status |
  Format-Table -Wrap
```

## 5. Demonstrate the parser

This example parses a written transcript locally; it does not use audio or contact Prisma:

```powershell
.\.venv\Scripts\python.exe -c "from numparse import parse_amount; print(parse_amount('Rs. 13,000'))"
```

Expected output:

```text
{'value': 13000, 'unknown': [], 'reason': 'ok'}
```

## 6. Demonstrate the guard

### Example where two views agree

```powershell
.\.venv\Scripts\python.exe -c "from guard import decide; print(decide('amount', {'v2.5': 'Rs. 13,000', 'v3.0': '13,000 rupees'}))"
```

Expected decision: `ACCEPT`, with value `13000`.

### Example where a digit-length check asks for confirmation

```powershell
.\.venv\Scripts\python.exe -c "from guard import decide; print(decide('digits', {'v2.5': '90,000', 'v3.0': '90,000'}, expected_len=10))"
```

Expected decision: `CONFIRM`, with `wrong_length` among the reasons.

### Important limitation to explain

Agreement does not prove correctness. This local example deliberately mirrors the saved `kn_11` case:

```powershell
.\.venv\Scripts\python.exe -c "from guard import decide; print(decide('amount', {'v2.5': '911718', 'v3.0': '911718'}))"
```

The guard accepts `911718` because both views agree. In the pilot CSV, the expected dataset value for `kn_11` is `13000`. The guard is not given that expected answer during its decision; this is a known shared-error limitation, not a parser failure.

## 7. Optional older comparison script

`compare_results.py` reads the older `truth.csv` and `transcripts.csv` only. It does not call an API, but it is **not** the eight-clip pilot: the legacy files contain three Kannada transcripts and have missing English transcripts. Windows PowerShell may need UTF-8 mode to print the rupee symbol:

```powershell
$env:PYTHONUTF8 = '1'
.\.venv\Scripts\python.exe compare_results.py
Remove-Item Env:\PYTHONUTF8
```

Use the Day 8 saved pilot evaluation as the main results demonstration.

## 8. Dependencies and scripts to avoid

No dependency manifest such as `requirements.txt` or `pyproject.toml` is present. The parser, guard, evaluator, saved CSV display, and local tests use the project’s Python environment and local files. The API scripts use extra packages such as `requests` and `python-dotenv`; they are not needed for this local walkthrough.

Do **not** run these as part of the recording:

- `main.py` — sends a request to the external speech API.
- `run_views.py --live` — can send paid API requests.
- `build_results.py` — unnecessary for the demo and writes a CSV output (it protects existing files, but there is no reason to rebuild results during recording).

The normal `run_views.py` command is a dry run, but the result demonstration does not need to run it.

## 9. Suggested words for the LinkedIn video

You can say:

> “SankhyaGuard is a small verification layer for spoken-number transcripts in English, Kannada, and Hindi. It is not a speech-recognition model. I take a transcript, parse the number, and check whether available transcript views agree or whether the user should confirm it.
>
> “Here is a local parser example: ‘Rs. 13,000’ becomes 13,000. Here, two transcript views agree, so the guard accepts. Here, the digit-length rule asks for confirmation.
>
> “The saved clean pilot has eight clips, but only seven complete Prisma v2.5/v3.0 pairs. On those seven, the first view was wrong three times. The guard asked for confirmation once, caught one of those errors, and silently accepted two shared Kannada errors.
>
> “This is an early pilot, not a general accuracy claim. The Hindi pair is incomplete, the full 72-clip experiment and degraded conditions have not been evaluated, and model agreement is not proof that a number is correct.”

Do not say that the guard corrected the wrong values. It can ask for confirmation; it does not know the correct answer unless a separate verified source supplies it.

## 10. Known limitations

- The saved pilot results cover seven complete **clean** audio/model pairs.
- `hi_11` remains incomplete: v3.0 succeeded, but v2.5 returned HTTP 504.
- Phone-quality and SNR 5 recognition results have not been collected.
- The full 72 clips have not been evaluated with saved transcripts.
- The expected labels and recordings have not all been independently verified.
- Two Kannada errors were silently accepted when both models agreed on the same wrong value.
- The sample uses one speaker and a small set of generated numbers; it does not establish performance for other speakers or real conversations.
- Prisma v2.5 and v3.0 are from the same vendor and can share errors.

## 11. Features not yet implemented

- A graphical or web demo interface.
- A complete, independently checked evaluation of all 72 clips.
- Complete results for Hindi in the pilot.
- API results for phone and SNR 5 audio conditions.
- Timbre TTS or Evon integration in the demonstrated flow.
- A validated rule that can catch the shared Kannada errors without causing an unknown number of unnecessary confirmation prompts.

## 12. Two-to-three-minute video outline

| Time | Part | What to show or say |
|---|---|---|
| 0:00–0:20 | Introduction | Show the project folder/title. Say SankhyaGuard checks number transcripts; it is not an ASR model. |
| 0:20–0:45 | Problem | Explain that a wrong phone number or amount can matter, and two transcripts can agree yet still be wrong. |
| 0:45–1:20 | What it does | Show the parser command converting `Rs. 13,000` to `13000`, then show the guard accepting agreement and asking for confirmation on a wrong-length digit string. |
| 1:20–1:55 | Saved pilot | Run `evaluate.py` on `results\day8_clean_pilot_results.csv`. Point out 8 input, 7 evaluated, and 1 skipped. |
| 1:55–2:20 | Limitation | Show or mention the `kn_11` shared-error example. Explain that agreement cannot catch identical mistakes. |
| 2:20–2:40 | Conclusion | Say this is a small clean pilot, not a complete 72-clip or degraded-audio evaluation. State the next step is broader, independently verified testing. |

Target length: approximately 2 minutes 40 seconds. Keep the terminal and file names readable, and do not show `.env`, credentials, or live API screens.
