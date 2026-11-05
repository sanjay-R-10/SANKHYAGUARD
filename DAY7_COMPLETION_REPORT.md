# SankhyaGuard — Day 7 Completion Report

## What Day 7 tested

The pilot compared two saved Prisma transcripts for each selected recording:

- Prisma v2.5
- Prisma v3.0

SankhyaGuard parsed both transcripts and decided whether to `ACCEPT` the number or ask the user to confirm it. The evaluation compared those decisions with the expected values written in the dataset.

The pilot has seven complete audio/model pairs. The Hindi recording `hi_11` is incomplete: Prisma v2.5 returned HTTP 504, and no Prisma v3.0 request was sent. The incomplete row is not counted in the evaluation.

Day 6 had already collected successful Prisma v2.5 and v3.0 responses for `en_01`. Those saved responses were reused for the Day 7 comparison; the cache reuse did not require a new API request.

## Results

The saved results were evaluated with the existing `evaluate.py` and `guard.py` code:

| Group | Complete pairs | First model wrong (A) | Guard wrong and accepted (G) | Guard asked to confirm | Errors caught by confirmation | Needless confirmations |
|---|---:|---:|---:|---:|---:|---:|
| All | 7 | 3 | 2 | 1 | 1 | 0 |
| English | 4 | 0 | 0 | 0 | 0 | 0 |
| Kannada | 3 | 3 | 2 | 1 | 1 | 0 |

In this table, **A** means the first view, Prisma v2.5. **G** means the guard using both model transcripts. “Caught” means the guard asked for confirmation on an example where A was wrong. It does not mean the guard corrected the number.

The Hindi group has no complete pairs, so it has no evaluation row.

## What happened on the Kannada examples

### `kn_11`: expected 13,000

- Prisma v2.5 returned `911718`.
- Prisma v3.0 returned `911718`.
- Both transcripts parsed to the same value.
- The guard saw agreement and accepted `911718`, which does not match the written expected value.

### `kn_12`: expected 30,000

- Prisma v2.5 returned `₹13,000`.
- Prisma v3.0 returned `13000 ರೂಪಾಯಿ.`
- The wording and formatting differ, but both parse to 13,000.
- The guard saw agreement and accepted 13,000, which does not match the written expected value.

These are two **silent errors**: both views agreed on a parsed value, but that value did not match the dataset's expected value.

## What the guard caught

For `kn_01`, the expected value is a 10-digit number, but the two models returned amount-like transcripts for 90,000. The guard detected the wrong digit length and asked for confirmation. That is the one caught error in this pilot.

## Why agreement is not proof

The guard can detect disagreement between its views, unparseable text, and certain format problems such as an unexpected digit length. It cannot know that two agreeing transcripts are wrong if both models make the same mistake. The `kn_11` and `kn_12` examples demonstrate that limitation.

The results compare transcripts with the expected values recorded in the dataset. They do not independently prove that every recording contains its written expected value, and this small pilot is not a broad measurement of recognition accuracy.

## Day 7 request status

- Seven audio IDs have both model results: `en_01`, `en_02`, `kn_01`, `en_11`, `en_12`, `kn_11`, and `kn_12`.
- `hi_11` is incomplete: Prisma v2.5 returned HTTP 504; Prisma v3.0 was not requested.
- The pilot log records 12 successful new Day 7 requests, one HTTP 504 attempt, and one cache reuse for `en_01` Prisma v2.5.
- Day 6's two `en_01` model calls had succeeded.
- No request is pending.

## Why no new guard rule was added

The guard behaved according to its current rules: it accepted when both parsed views agreed. These two examples show that agreement can fail, but they are not enough evidence to choose a reliable general rule. For example, always asking users to confirm Kannada amounts might catch these examples, but it could also create unnecessary questions for correct amounts. The pilot is too small to measure that trade-off.

No example-specific rule was added, and no claim is made that any one rule would catch all recognition errors.

## Recommended next development stage

1. Verify the recordings and their written expected values independently before treating them as ground truth.
2. Expand the evaluation set across languages, number types, and recording conditions; keep the expected values separate from the model transcripts.
3. Measure both missed errors and unnecessary confirmation prompts on that larger set.
4. Investigate ways to obtain genuinely different evidence for the guard. Two models that make the same mistake do not provide independent confirmation.
5. Keep shared-model mistakes and incomplete results visible in reports. Do not silently count missing results as correct.

## Completion status

The Day 7 pilot evaluation is complete for the seven available model pairs. The eight-ID pilot is **partial** because `hi_11` has no complete pair. The conclusions above are limited to the saved pilot data.
