import argparse
import csv
import json
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
SUBSET_FILE = PROJECT_DIR / "subset.csv"
RAW_DIR = PROJECT_DIR / "results" / "raw"
DEFAULT_OUTPUT = PROJECT_DIR / "results" / "day6_results.csv"
MODELS = ("prisma-v2.5", "prisma-v3.0")
FIELDS = (
    "id",
    "language",
    "condition",
    "kind",
    "truth",
    "expected_len",
    "model",
    "response_model",
    "status",
    "transcript",
    "output_literal",
    "detected_language_code",
    "request_id",
    "processing_time",
    "end_to_end_latency",
    "truncated",
    "http_status",
    "error_type",
    "error_message",
    "raw_file",
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


def make_result(item, model, log_row):
    raw_path = RAW_DIR / f"{item['id']}__{model}.json"
    payload = read_raw_response(raw_path) if raw_path.is_file() else None
    success = (
        isinstance(payload, dict)
        and payload.get("success") is True
        and isinstance(payload.get("transcript"), str)
    )
    error = payload.get("error", {}) if isinstance(payload, dict) else {}
    if not error and isinstance(payload, dict):
        error = payload.get("detail", {})
    if not isinstance(error, dict):
        error = {}
    status = "SUCCESS" if success else (log_row.get("status", "MISSING") if log_row else "MISSING")
    if payload is not None and not success and status == "SUCCESS":
        status = "INVALID_RESPONSE"
    return {
        "id": item.get("id", ""),
        "language": item.get("language", ""),
        "condition": "clean",
        "kind": item.get("kind", ""),
        "truth": item.get("truth", ""),
        "expected_len": item.get("expected_len", ""),
        "model": model,
        "response_model": payload.get("model", "") if success else "",
        "status": status,
        "transcript": payload.get("transcript", "") if success else "",
        "output_literal": (payload.get("output") or {}).get("literal", "")
        if success and isinstance(payload.get("output"), dict)
        else "",
        "detected_language_code": payload.get("detected_language_code", "") if success else "",
        "request_id": (
            payload.get("request_id", "")
            if isinstance(payload, dict)
            else (log_row.get("request_id", "") if log_row else "")
        ),
        "processing_time": payload.get("processing_time", "") if success else "",
        "end_to_end_latency": payload.get("end_to_end_latency", "") if success else "",
        "truncated": payload.get("truncated", "") if success else "",
        "http_status": log_row.get("http_status", "") if log_row else "",
        "error_type": error.get("type", error.get("error_code", "")),
        "error_message": error.get("message", ""),
        "raw_file": str(raw_path.relative_to(PROJECT_DIR)) if raw_path.is_file() else "",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Build a CSV from cached responses only; never makes API requests."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="output CSV path; existing files are never overwritten",
    )
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else PROJECT_DIR / args.output
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing file: {output}")

    items = read_rows(SUBSET_FILE)
    statuses = load_statuses()
    rows = [
        make_result(item, model, statuses.get((item.get("id", ""), model)))
        for item in items
        for model in MODELS
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows from cached responses only: {output}")
    print("Missing or failed responses are marked in the status column; raw files were not changed.")


if __name__ == "__main__":
    main()
