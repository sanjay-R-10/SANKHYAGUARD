# SankhyaGuard — Day 9 Error Analysis and Findings

## 1. Dataset and evaluation coverage

The full dataset contains 72 clips: 24 English, 24 Kannada, and 24 Hindi. This report does **not** evaluate all 72 clips. The saved API results are for the clean 8-clip pilot only.

The Day 8 pilot results CSV contains 8 rows:

- 7 clips have successful results from both Prisma v2.5 and Prisma v3.0 and were evaluated.
- `hi_11` has a saved Prisma v3.0 response, but its earlier Prisma v2.5 request returned HTTP 504. It remains incomplete and is excluded from paired evaluation.

There are no phone-quality or SNR 5 API results in the inspected pilot CSVs.

## 2. Day 7 and Day 8 results

Day 7 and Day 8 use the same seven complete pairs for the guard evaluation. Day 8 added a successful v3.0 response for `hi_11`, but that did not complete its model pair. The existing evaluation therefore remains:

| Group | Evaluated pairs | First view wrong (A) | Guard wrong and accepted (G) | Guard confirmations | Errors caught | Needless confirmations |
|---|---:|---:|---:|---:|---:|---:|
| All | 7 | 3 | 2 | 1 | 1 | 0 |
| English | 4 | 0 | 0 | 0 | 0 | 0 |
| Kannada | 3 | 3 | 2 | 1 | 1 | 0 |
| Hindi | 0 | — | — | — | — | — |

`A` is the first view, Prisma v2.5. `G` is the guard using both model views. The Hindi result is not zero-error evidence: there are no complete Hindi pairs in the evaluation.

## 3. Error classification

The table classifies discrepancies against the expected values recorded in the dataset. The recordings were not independently checked again as part of this analysis, so “recognition error” here means **the saved transcript disagrees with the dataset’s intended value**; it is not independent proof of what is audible in the file.

| Clip | Language | Expected value | Saved model transcripts | Parser output(s) | Guard decision | Classification | Explanation |
|---|---|---:|---|---|---|---|---|
| `kn_01` | Kannada | `7056413953` (10 digits) | v2.5: `₹90,000`; v3.0: `90,000 ರೂಪಾಯಿ.` | `90000` from each digit-kind view | `CONFIRM` (`wrong_length`) | **R**; caught by guard | The outputs represent 90,000 rather than the intended 10-digit string. The guard noticed the parsed value had the wrong digit length and asked for confirmation. |
| `kn_11` | Kannada | `13000` | v2.5: `911718`; v3.0: `911718` | `911718` from each amount view | `ACCEPT` | **R + G** | The saved number differs from the intended amount. Both views agree, so the guard accepted the same wrong value. |
| `kn_12` | Kannada | `30000` | v2.5: `₹13,000`; v3.0: `13000 ರೂಪಾಯಿ.` | `13000` from each amount view | `ACCEPT` | **R + G** | Both outputs represent 13,000 rather than the intended 30,000. The parser extracted the transcript value consistently, and the guard accepted because the parsed views agree. |

**Category counts (categories can overlap):**

- **R — Recognition mismatch:** 3 clips (`kn_01`, `kn_11`, `kn_12`), measured against dataset labels.
- **F — Formatting error:** 0 verified errors. Differences such as `₹13,000` versus `13,000 rupees` preserve the same numeric amount and were not errors by themselves.
- **P — Parser error:** 0 verified errors in these examples. The parser outputs shown above match the numbers expressed in the saved transcripts.
- **G — Guard error:** 2 silent accepts (`kn_11`, `kn_12`). These overlap with the recognition mismatches: they are the two errors that the guard did not catch.

## 4. Recognition, parser, and guard findings

### Recognition

All three evaluated Kannada examples have a transcript/value mismatch against the written expected value. This is a small sample and the ground-truth audio itself was not independently verified during this analysis.

### Formatting

The saved responses use different display formats, including a rupee symbol, grouped digits, and currency words. For the amounts in this pilot, the parser resolves those formats to the same numeric value. No standalone formatting failure was verified.

### Parser

No evidence in these examples shows that the parser changed a correct transcript into an incorrect number:

- `₹90,000` and `90,000 રૂપಾಯಿ.` parse to the numeric digits/value 90000.
- `911718` parses to 911718.
- `₹13,000` and `13000 ರೂಪಾಯಿ.` parse to 13000.

The wrong values are already present in the saved model outputs relative to the dataset labels. A wrong final value alone is not proof of a parser bug.

### Guard

For `kn_01`, the guard did not accept the wrong-length digit string; it requested confirmation. For `kn_11` and `kn_12`, both models produced the same parsed value, so the guard’s agreement rule accepted it. This confirms a limitation of agreement-only checking: if the available views share an error, agreement cannot reveal that error.

## 5. Verified issues and possible improvements

Verified from the saved files:

1. Two wrong values (`kn_11` and `kn_12`) were silently accepted by the guard relative to the expected dataset values.
2. The only Hindi pilot clip, `hi_11`, lacks a complete pair. Its v3.0 response is saved, but v2.5 returned HTTP 504.
3. There are not yet API results for the full dataset or the phone/SNR 5 conditions.

No parser or guard production code was changed. No parser fix is justified by these cases because the parser correctly interpreted the saved transcript values. A broad rule such as always confirming Kannada amounts might catch these examples but could also create unnecessary prompts; seven complete pairs are not enough to measure that trade-off.

Possible next improvements should be evaluated on more independently checked examples. In particular:

- Verify the actual recordings against their written labels before treating those labels as confirmed ground truth.
- Expand the measured sample across languages, digits and amounts, and audio conditions.
- Measure both missed errors and unnecessary confirmations before changing guard behavior.
- Do not treat two models from the same vendor agreeing as independent proof that the number is correct.

## 6. Missing responses and limitations

- The evaluated sample is **7 complete pairs**, not 8 and not 72.
- `hi_11` has one saved v3.0 response but no usable v2.5 response; it is excluded from paired guard metrics.
- The result set covers clean audio only.
- The recordings and expected labels have not all been independently verified in this analysis.
- The sample is small and uses one speaker’s recordings and synthetic-number data. It does not establish performance for other speakers or real-world conversations.
- Prisma v2.5 and v3.0 are from the same vendor, so their errors may be shared.
- The evaluation metrics describe this saved pilot only and should not be presented as general accuracy claims.

## 7. Tests and evaluation run

During this Day 9 review:

```text
test_numparse.py: All tests passed
test_guard.py: Guard tests passed
```

The saved Day 8 results were evaluated with the existing evaluator:

```text
Rows: input=8 evaluated=7 skipped=1
Skipped (unavailable_model_response): 1 [hi_11]
ALL: n=7, A wrong=3, G wrong=2, G asks=1, caught=1, needless=0
English: n=4, A wrong=0, G wrong=0, G asks=0
Kannada: n=3, A wrong=3, G wrong=2, G asks=1, caught=1
```

No parser, guard, evaluator, result CSV, call log, or raw response was changed for this analysis.

## 8. Recommended next steps

1. Independently verify the audio and expected labels for the pilot, especially the three Kannada clips, before calling the mismatches confirmed speech errors.
2. Keep the current guard policy unchanged until a larger, verified dataset can measure missed errors and unnecessary prompts.
3. Before collecting more conditions, ensure the API runner and result paths identify the audio condition so clean, phone, and SNR 5 files cannot be confused.
4. Record actual balance before and after each approved API batch; do not infer credit costs from request counts.
5. Before a public LinkedIn demo, build and test a clear demo interface, show only measured results, disclose incomplete coverage and limitations, and avoid claims based on the full 72 clips until they have actual verified transcripts.

## 9. Completion status

Day 9 analysis is complete for the **available clean pilot results only**. The full 72-clip, multi-condition experiment and complete Hindi pilot pair remain unfinished. No production code was changed and no API calls were made during this analysis.
