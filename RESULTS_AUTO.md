# SankhyaGuard — Automatically Generated Results

> **PILOT ONLY:** This report uses saved clean-pilot data. It is not the full 72-clip experiment.

## Data scope

- Source: `results/day8_clean_pilot_results.csv` (8 rows).
- Complete pairs evaluated: 7.
- Skipped rows: 1.
- Missing full-result inputs: `results_clean_all.csv`, `results_phone_all.csv`.
- No phone, SNR 5, or SNR 10 model results are included.
- Dataset labels were not independently checked against each recording during this report generation.

## Evaluation definitions

Counts below use the existing `evaluate.py` and Guard logic. A is the first view; G is the Guard. A caught error means the Guard requested confirmation on a row where A was wrong; it is not a correction.

## Metrics

| Dataset | Input | Evaluated | Skipped | Skip reasons | A wrong | G silent wrong | G asks | Caught | Needless |
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
| clean pilot | 8 | 7 | 1 | unavailable_model_response: 1 | 3 | 2 | 1 | 1 | 0 |

### Evaluated rows by language

| Dataset | Language | Evaluated | A wrong | G silent wrong | G asks | Caught | Needless |
|---|---|---:|---:|---:|---:|---:|---:|
| clean pilot | en | 4 | 0 | 0 | 0 | 0 | 0 |
| clean pilot | kn | 3 | 3 | 2 | 1 | 1 | 0 |

The evaluator excludes rows without a truth value or usable transcript views. Its metric denominators are the evaluated rows, except caught errors, which are counted among first-view errors.

## Row details

| Dataset | ID | Language | Truth label | First-view parsed | Guard decision | Guard parsed | Outcome |
|---|---|---|---:|---:|---|---:|---|
| clean pilot | `en_01` | en | 6043321819 | 6043321819 | ACCEPT | 6043321819 | accepted value matches dataset label |
| clean pilot | `en_02` | en | 9001338908 | 9001338908 | ACCEPT | 9001338908 | accepted value matches dataset label |
| clean pilot | `kn_01` | kn | 7056413953 | 90000 | CONFIRM | 90000 | confirmation (wrong_length) |
| clean pilot | `en_11` | en | 13000 | 13000 | ACCEPT | 13000 | accepted value matches dataset label |
| clean pilot | `en_12` | en | 30000 | 30000 | ACCEPT | 30000 | accepted value matches dataset label |
| clean pilot | `kn_11` | kn | 13000 | 911718 | ACCEPT | 911718 | silent error against dataset label |
| clean pilot | `kn_12` | kn | 30000 | 13000 | ACCEPT | 13000 | silent error against dataset label |

## Incomplete or skipped rows

| Dataset | ID | Skip reason |
|---|---|---|
| clean pilot | `hi_11` | unavailable_model_response |

## Demo clip availability

- **Prisma wrong and Guard asks:** `kn_01`
- **Accepted value matches dataset label:** `en_01`
- **Silent error:** `kn_11`
- **Phone quality: unavailable.** No phone-condition model results are present.
- **Kannada:** `kn_01`

The generated `demo_ids.txt` contains only supported pilot IDs, one per line. A selected clip may represent more than one category. Matching a written label is not independent proof that the audio itself is correct.

## Limitations

- Agreement between model views does not prove a number is correct.
- These counts describe only the supplied result files and the current parser/Guard.
- Missing responses are skipped, not treated as successful results.
