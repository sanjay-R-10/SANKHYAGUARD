import argparse
import csv
import json
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
SUBSET_FILE = PROJECT_DIR / "subset.csv"
RAW_DIR = PROJECT_DIR / "results" / "raw"
DEFAULT_OUTPUT = PROJECT_DIR / "results" / "day7_results.csv"
MODELS = ("prisma-v2.5", "prisma-v3.0")
FIELDS = (
    "id",
    "language",
    "condition",
    "kind",
    "truth",
    "expected_len",
    "v2_5_status",
    "v2_5_transcript",
    "v2_5_literal",
    "v2_5_response_model",
    "v2_5_request_id",
    "v2_5_http_status",
    "v2_5_error_type",
    "v2_5_error_message",
    "v2_5_processing_time",
    "v3_0_status",
    "v3_0_transcript",
    "v3_0_response_model",
    "v3_0_detected_language_code",
    "v3_0_request_id",
    "v3_0_http_status",
    "v3_0_error_type",
    "v3_0_error_message",
    "v3_0_processing_time",
    "view_v2_5",
    "view_v3_0",
    "paired_views_status",
)


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def read_raw_response(path):
    try:
        with path.open(encoding="utf-8") as stream:
            payload = json.load(stream)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def load_statuses():
    log_path = RAW_DIR.parent / "calls_log.csv"
    statuses = {}
    if not log_path.is_file():
        return statuses
    try:
        for row in read_rows(log_path):
            key = (row.get("id", ""), row.get("model", ""))
            statuses[key] = row
    except (OSError, csv.Error):
        return statuses
    return statuses


def response_fields(item, model, log_row, raw_dir=RAW_DIR):
    path = raw_dir / f"{item['id']}__{model}.json"
    payload = read_raw_response(path) if path.is_file() else None
    success = (
        isinstance(payload, dict)
        and payload.get("success") is True
        and isinstance(payload.get("transcript"), str)
    )
    has_transcript = success and bool(payload["transcript"].strip())
    error = payload.get("error", {}) if isinstance(payload, dict) else {}
    if not error and isinstance(payload, dict):
        error = payload.get("detail", {})
    if not isinstance(error, dict):
        error = {}
    error_type = error.get("type", error.get("error_code", ""))
    error_message = error.get("message", "")
    if isinstance(payload, dict):
        error_type = error_type or payload.get("code", "")
        error_message = error_message or payload.get("message", "")

    logged_status = log_row.get("status", "MISSING") if log_row else "MISSING"
    if has_transcript:
        status = "SUCCESS"
    elif success:
        status = "EMPTY_TRANSCRIPT"
    elif payload is None:
        status = logged_status if logged_status not in ("SUCCESS", "CACHE_HIT") else "MISSING_RESPONSE"
    else:
        status = logged_status if logged_status not in ("SUCCESS", "CACHE_HIT") else "INVALID_RESPONSE"

    fields = {
        "status": status,
        "transcript": payload.get("transcript", "") if success else "",
        "literal": "",
        "response_model": payload.get("model", "") if success else "",
        "detected_language_code": payload.get("detected_language_code", "") if success else "",
        "request_id": (
            payload.get("request_id", "")
            if isinstance(payload, dict)
            else (log_row.get("request_id", "") if log_row else "")
        ),
        "http_status": log_row.get("http_status", "") if log_row else "",
        "error_type": error_type,
        "error_message": error_message,
        "processing_time": payload.get("processing_time", "") if success else "",
        "raw_exists": path.is_file(),
    }
    if success and isinstance(payload.get("output"), dict):
        fields["literal"] = payload["output"].get("literal", "")
    return fields


def make_result(item, statuses, raw_dir=RAW_DIR):
    audio_id = item["id"]
    v25 = response_fields(
        item, MODELS[0], statuses.get((audio_id, MODELS[0])), raw_dir
    )
    v30 = response_fields(
        item, MODELS[1], statuses.get((audio_id, MODELS[1])), raw_dir
    )
    paired = v25["status"] == "SUCCESS" and v30["status"] == "SUCCESS"
    return {
        "id": audio_id,
        "language": item.get("language", ""),
        "condition": "clean",
        "kind": item.get("kind", ""),
        "truth": item.get("truth", ""),
        "expected_len": item.get("expected_len", ""),
        "v2_5_status": v25["status"],
        "v2_5_transcript": v25["transcript"],
        "v2_5_literal": v25["literal"],
        "v2_5_response_model": v25["response_model"],
        "v2_5_request_id": v25["request_id"],
        "v2_5_http_status": v25["http_status"],
        "v2_5_error_type": v25["error_type"],
        "v2_5_error_message": v25["error_message"],
        "v2_5_processing_time": v25["processing_time"],
        "v3_0_status": v30["status"],
        "v3_0_transcript": v30["transcript"],
        "v3_0_response_model": v30["response_model"],
        "v3_0_detected_language_code": v30["detected_language_code"],
        "v3_0_request_id": v30["request_id"],
        "v3_0_http_status": v30["http_status"],
        "v3_0_error_type": v30["error_type"],
        "v3_0_error_message": v30["error_message"],
        "v3_0_processing_time": v30["processing_time"],
        "view_v2_5": v25["transcript"] if paired else "",
        "view_v3_0": v30["transcript"] if paired else "",
        "paired_views_status": "READY" if paired else "INCOMPLETE",
    }


def write_results(items, statuses, output, raw_dir=RAW_DIR):
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing file: {output}")
    rows = [make_result(item, statuses, raw_dir) for item in items]
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main():
    parser = argparse.ArgumentParser(
        description="Build a paired results CSV from cached responses only."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="include all dataset rows instead of only the pilot subset",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="output CSV path; existing files are never overwritten",
    )
    args = parser.parse_args()
    default_output = (
        PROJECT_DIR / "results" / "all_results.csv"
        if args.all
        else DEFAULT_OUTPUT
    )
    output = args.output or default_output
    if not output.is_absolute():
        output = PROJECT_DIR / output

    source = PROJECT_DIR / "dataset_script.csv" if args.all else SUBSET_FILE
    items = read_rows(source)
    statuses = load_statuses()
    rows = write_results(items, statuses, output)
    successes = sum(row["paired_views_status"] == "READY" for row in rows)
    print(f"Wrote {len(rows)} {'dataset' if args.all else 'subset'} rows from cached responses only: {output}")
    print(f"Complete v2.5/v3.0 response pairs: {successes}")
    print("Incomplete results have blank evaluation views; raw responses were not changed.")


if __name__ == "__main__":
    main()
