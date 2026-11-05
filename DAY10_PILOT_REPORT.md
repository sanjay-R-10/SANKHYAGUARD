# SankhyaGuard — Clean Pilot Results

## Data scope

- **8** clean pilot rows are present in `results/day8_clean_pilot_results.csv`.
- **7** rows have complete paired Prisma v2.5/v3.0 results and were evaluated.
- **1** row, `hi_11`, is incomplete and skipped because its v2.5 response is unavailable; its saved v3.0 transcript alone is not a complete pair.
- This is a **clean pilot only**, not the full 72-clip experiment.
- There are no phone, SNR 5, or SNR 10 model results in this pilot. The existence of audio files for those conditions is not model-result evidence.

The pilot contains four English rows, three Kannada rows, and one Hindi row. The evaluated pairs are four English and three Kannada; Hindi has no complete pair.

## Source fields and evaluation method

The saved result CSV contains the dataset `truth`, `expected_len`, and `kind`; the actual saved model transcripts in `v2_5_transcript` and `v3_0_transcript`; and paired evaluation views in `view_v2_5` and `view_v3_0`. `paired_views_status` identifies whether both views are available.

The CSV does not store parsed values or Guard decisions. Those were reproduced locally using the existing `parse_view`, `decide`, and `evaluate.py` logic. The evaluator's existing definitions were left unchanged:

- **A wrong**: the first view (Prisma v2.5) parses to a value different from the dataset truth.
- **G silent wrong**: the Guard accepts a value different from dataset truth.
- **G asks**: the Guard returns `CONFIRM`.
- **Caught**: the Guard asks on a row where A was wrong. This is a confirmation, not a correction.
- **Needless**: the Guard asks on a row where A was not wrong.

Truth comparison is against the dataset labels. The recordings were not independently re-verified here, so these results do not prove that each spoken recording matches its written label.

## Per-row results

| Clip | Language | Kind | Dataset truth | Prisma v2.5 parsed value | Prisma v3.0 parsed value | Guard | Evaluation outcome |
|---|---|---|---:|---:|---:|---|---|
| `en_01` | English | Digits | `6043321819` | `6043321819` | `6043321819` | ACCEPT | Accepted value matches dataset truth |
| `en_02` | English | Digits | `9001338908` | `9001338908` | `9001338908` | ACCEPT | Accepted value matches dataset truth |
| `kn_01` | Kannada | Digits | `7056413953` | `90000` | `90000` | CONFIRM | First view is wrong; Guard asks because the parsed value has the wrong length |
| `en_11` | English | Amount | `13000` | `13000` | `13000` | ACCEPT | Accepted value matches dataset truth |
| `en_12` | English | Amount | `30000` | `30000` | `30000` | ACCEPT | Accepted value matches dataset truth |
| `kn_11` | Kannada | Amount | `13000` | `911718` | `911718` | ACCEPT | Silent error: both views agree on a value different from dataset truth |
| `kn_12` | Kannada | Amount | `30000` | `13000` | `13000` | ACCEPT | Silent error: both views agree on a value different from dataset truth |
| `hi_11` | Hindi | Amount | `13000` | — | `13000` | Not evaluated | Incomplete pair; skipped by the evaluator |

“Accepted value matches dataset truth” means it matches the saved label; it is not an independent verification of the audio.

## Verified pilot metrics

The existing evaluator was run on the saved Day 8 CSV and reported:

| Measure | Result | Evaluator denominator |
|---|---:|---:|
| Input rows | 8 | — |
| Evaluated complete pairs | 7 | — |
| Skipped rows | 1 (`hi_11`, `unavailable_model_response`) | — |
| First-view wrong | 3 | 7 evaluated pairs |
| Guard silently accepted a wrong value | 2 | 7 evaluated pairs |
| Guard asked for confirmation | 1 | 7 evaluated pairs |
| First-view errors that led to confirmation | 1 | 3 first-view errors |
| Needless confirmations | 0 | 7 evaluated pairs |

These are counts from the existing evaluation logic, independently reproduced from the saved pilot CSV and cross-checked against the per-row parser and Guard decisions above. No new metric definition or percentage was introduced.

The pilot-only visualization is [results_chart_pilot.png](./results_chart_pilot.png). It shows raw counts with each evaluator denominator labeled, notes that categories can overlap, and is explicitly limited to the seven complete clean-pilot pairs.

## What the Guard did

- `kn_01`: both views parsed to `90000`, not the 10-digit dataset value. The Guard asked for confirmation because the value had the wrong expected length. This is the one first-view error that led to confirmation; the Guard did not correct it.
- `kn_11`: both views parsed to `911718`, and the Guard accepted their agreement even though it differs from the dataset label `13000`.
- `kn_12`: both views parsed to `13000`, and the Guard accepted their agreement even though it differs from the dataset label `30000`.
- The other four complete rows were accepted with values matching their dataset labels.
- `hi_11` was not evaluated because one model response was unavailable.

Agreement between two model views is not proof of correctness: the two Kannada amount errors show that both can agree on the same wrong value.

## Limitations and missing experiment conditions

- Only 7 of the 8 pilot rows have complete paired model results.
- This is not a full 72-clip evaluation; the 72-item dataset does not mean 72 clips were transcribed and evaluated.
- No phone, SNR 5, or SNR 10 model results were evaluated.
- The error counts are small and should not be treated as statistically significant or as a broad performance claim.
- Dataset truth was not independently checked against each recording during this work.
- Results are specific to these saved pilot responses, the current parser, and the current Guard.

The full clean and phone reports, full experiment analysis, and five-clip selection from `analyse.py` remain blocked because the corresponding full result files, analysis script, and analysis output are not available.
