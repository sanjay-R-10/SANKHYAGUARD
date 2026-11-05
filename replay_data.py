import csv
import re
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
PILOT_RESULTS = PROJECT_DIR / "results" / "day8_clean_pilot_results.csv"
DEMO_IDS = PROJECT_DIR / "demo_ids.txt"
DATASET = PROJECT_DIR / "dataset_script.csv"
REQUIRED_COLUMNS = {
    "id",
    "language",
    "condition",
    "kind",
    "truth",
    "expected_len",
    "v2_5_status",
    "v2_5_transcript",
    "v2_5_literal",
    "v3_0_status",
    "v3_0_transcript",
    "view_v2_5",
    "view_v3_0",
    "paired_views_status",
}
CONDITION_FOLDERS = {
    "clean": "audio",
    "snr10": "audio_snr10",
    "snr5": "audio_snr5",
    "phone": "audio_phone",
}
ID_PATTERN = re.compile(r"^[a-z]{2}_\d{2}$")


def _read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None:
            return [], set()
        return list(reader), set(reader.fieldnames)


def _read_demo_ids(path, warnings):
    if not path.is_file():
        warnings.append(
            f"Demo ID file not found: {path.name}. Showing all complete pilot rows."
        )
        return None
    tokens = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        tokens.extend(part.strip() for part in line.replace(",", " ").split())
    if not tokens:
        warnings.append(
            f"{path.name} is empty. Showing all complete pilot rows."
        )
        return None
    selected = []
    invalid = []
    for token in tokens:
        clip_id, separator, condition = token.partition(":")
        if not ID_PATTERN.fullmatch(clip_id):
            invalid.append(token)
            continue
        selected.append((clip_id, condition if separator else None))
    if invalid:
        warnings.append(
            "Ignoring invalid demo ID entries: " + ", ".join(invalid)
        )
    return selected


def load_replay_rows(
    results_path=PILOT_RESULTS,
    demo_ids_path=DEMO_IDS,
    dataset_path=DATASET,
):
    results_path = Path(results_path)
    demo_ids_path = Path(demo_ids_path)
    dataset_path = Path(dataset_path)
    warnings = []
    if not results_path.is_file():
        return [], [f"Pilot results file not found: {results_path.name}."]
    try:
        rows, columns = _read_csv(results_path)
    except (OSError, UnicodeError, csv.Error) as error:
        return [], [f"Could not read pilot results: {error}"]
    if not columns:
        return [], [f"Pilot results file is empty: {results_path.name}."]
    missing_columns = sorted(REQUIRED_COLUMNS - columns)
    if missing_columns:
        return [], [
            "Pilot results are missing required columns: "
            + ", ".join(missing_columns)
        ]
    if not rows:
        return [], [f"Pilot results contain no data rows: {results_path.name}."]

    dataset_ids = None
    if dataset_path.is_file():
        try:
            dataset_rows, dataset_columns = _read_csv(dataset_path)
            if "id" in dataset_columns:
                dataset_ids = {row["id"] for row in dataset_rows}
            else:
                warnings.append(
                    f"{dataset_path.name} has no id column; demo IDs will be checked against results only."
                )
        except (OSError, UnicodeError, csv.Error) as error:
            warnings.append(
                f"Could not validate IDs against {dataset_path.name}: {error}"
            )
    else:
        warnings.append(
            f"{dataset_path.name} not found; demo IDs will be checked against results only."
        )

    complete = []
    skipped = 0
    for row in rows:
        required_values = (
            "id",
            "language",
            "condition",
            "kind",
            "truth",
            "paired_views_status",
            "view_v2_5",
            "view_v3_0",
        )
        if any(not (row.get(field) or "").strip() for field in required_values):
            skipped += 1
            continue
        if row["paired_views_status"] != "READY":
            skipped += 1
            continue
        if row["kind"] not in ("digits", "amount") or row["language"] not in (
            "en",
            "kn",
            "hi",
        ):
            warnings.append(
                f"Skipping {row['id']}: unsupported kind or language in saved row."
            )
            skipped += 1
            continue
        if dataset_ids is not None and row["id"] not in dataset_ids:
            warnings.append(
                f"Skipping {row['id']}: ID is not present in {dataset_path.name}."
            )
            skipped += 1
            continue
        complete.append(row)
    if skipped:
        warnings.append(
            f"Excluded {skipped} incomplete or invalid row(s); replay requires a complete model pair."
        )

    selection = _read_demo_ids(demo_ids_path, warnings)
    if selection is None:
        return complete, warnings

    by_id = {row["id"]: row for row in complete}
    filtered = []
    invalid_selection = []
    for clip_id, condition in selection:
        row = by_id.get(clip_id)
        if row is None:
            invalid_selection.append(clip_id)
        elif condition is not None and condition != row["condition"]:
            invalid_selection.append(f"{clip_id}:{condition}")
        else:
            filtered.append(row)
    if invalid_selection:
        warnings.append(
            "Ignoring demo IDs without a matching complete result: "
            + ", ".join(invalid_selection)
        )
    return filtered, warnings


def audio_path_for(row, project_dir=PROJECT_DIR):
    folder = CONDITION_FOLDERS.get(row.get("condition"))
    clip_id = row.get("id", "")
    if folder is None or not ID_PATTERN.fullmatch(clip_id):
        return None
    return Path(project_dir) / folder / f"{clip_id}.wav"
