import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
SUBSET_FILE = PROJECT_DIR / "subset.csv"
DATASET_FILE = PROJECT_DIR / "dataset_script.csv"
AUDIO_DIR = PROJECT_DIR / "audio"
RESULTS_DIR = PROJECT_DIR / "results"
RAW_DIR = RESULTS_DIR / "raw"
PENDING_DIR = RESULTS_DIR / "pending"
CALLS_LOG = RESULTS_DIR / "calls_log.csv"
API_URL = "https://api.vachana.ai/stt/v3"
LANGUAGE_CODES = {"en": "en-IN", "kn": "kn-IN", "hi": "hi-IN"}
MODELS = ("prisma-v2.5", "prisma-v3.0")
DAY6_ID = "en_01"
LOG_FIELDS = (
    "timestamp_utc",
    "id",
    "model",
    "language_code",
    "status",
    "http_status",
    "request_id",
    "paid_call",
    "raw_file",
)


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def get_day6_item():
    rows = {row["id"]: row for row in read_csv(DATASET_FILE)}
    if DAY6_ID not in rows:
        raise ValueError(f"{DAY6_ID} is missing from {DATASET_FILE.name}")
    item = rows[DAY6_ID]
    language_code = LANGUAGE_CODES.get(item.get("language"))
    if not language_code:
        raise ValueError(f"Unsupported language for {DAY6_ID}")
    audio_path = AUDIO_DIR / f"{DAY6_ID}.wav"
    return item, language_code, audio_path


def raw_path(audio_id, model):
    return RAW_DIR / f"{audio_id}__{model}.json"


def load_response(path):
    try:
        with path.open(encoding="utf-8") as stream:
            return json.load(stream)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def is_successful_response(data):
    return (
        isinstance(data, dict)
        and data.get("success") is True
        and isinstance(data.get("transcript"), str)
    )


def cache_state(audio_id, model):
    path = raw_path(audio_id, model)
    if not path.exists():
        return "miss"
    response = load_response(path)
    if is_successful_response(response):
        return "cached success"
    return "existing response; manual review required"


def prior_call_state(audio_id, model):
    if not CALLS_LOG.exists():
        return None
    validate_log_file()
    with CALLS_LOG.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            if row.get("id") == audio_id and row.get("model") == model:
                if row.get("paid_call") in ("YES", "UNKNOWN"):
                    return row.get("status", "previous request")
    return None


def print_plan(item, language_code, audio_path):
    print("Mode: DRY RUN (no network requests)")
    print(f"Audio ID: {DAY6_ID}")
    print(f"Audio file: {audio_path.relative_to(PROJECT_DIR)}")
    print(f"Language: {language_code}")
    print("Format: transcribe")
    print("Maximum planned requests: 2 (sequential, one audio/model per request)")
    for model in MODELS:
        state = cache_state(DAY6_ID, model)
        if state == "miss":
            previous_call = prior_call_state(DAY6_ID, model)
            if previous_call:
                state = f"blocked by prior call log ({previous_call})"
        print(f"Planned: {DAY6_ID} | {model} | cache: {state}")
    print("A cache hit is reused and does not send a request.")
    if not audio_path.is_file():
        print("Audio check: MISSING; live mode will stop before any request.")
    else:
        print("Audio check: present")
    if item.get("truth"):
        print("Expected label: present in dataset (not treated as a transcript)")
    print("Paid calls made: 0")


def validate_log_file():
    if not CALLS_LOG.exists():
        return
    with CALLS_LOG.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        header = next(reader, None)
    if tuple(header or ()) != LOG_FIELDS:
        raise RuntimeError(
            f"{CALLS_LOG.relative_to(PROJECT_DIR)} exists with an unexpected format; "
            "it was not changed."
        )


def append_log(audio_id, model, language_code, status, http_status="", request_id="", paid_call="YES", raw_file=""):
    validate_log_file()
    is_new = not CALLS_LOG.exists()
    with CALLS_LOG.open("a", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=LOG_FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "id": audio_id,
                "model": model,
                "language_code": language_code,
                "status": status,
                "http_status": http_status,
                "request_id": request_id,
                "paid_call": paid_call,
                "raw_file": raw_file,
            }
        )


def reserve_call(audio_id, model):
    marker = PENDING_DIR / f"{audio_id}__{model}.pending"
    try:
        with marker.open("x", encoding="ascii") as stream:
            stream.write("Request outcome may be unknown if the process stops.\n")
    except FileExistsError as error:
        raise RuntimeError(
            f"A pending marker already exists for {audio_id} {model}; "
            "inspect it and the call log before retrying."
        ) from error
    return marker


def write_raw_response(path, content):
    with path.open("xb") as stream:
        stream.write(content)


def request_one(language_code, audio_path, model):
    cached_path = raw_path(DAY6_ID, model)
    state = cache_state(DAY6_ID, model)
    if state == "cached success":
        print(f"Reusing cached success: {cached_path.relative_to(PROJECT_DIR)}")
        append_log(
            DAY6_ID, model, language_code, "CACHE_HIT",
            paid_call="NO", raw_file=str(cached_path.relative_to(PROJECT_DIR)),
        )
        return True, 0
    if state != "miss":
        print(f"STOP: {state} for {DAY6_ID} {model}; no duplicate request sent.")
        return False, 0
    previous_call = prior_call_state(DAY6_ID, model)
    if previous_call:
        print(
            f"STOP: a prior request is logged as {previous_call} for {DAY6_ID} "
            f"{model}, but no reusable cache exists. Inspect before retrying."
        )
        return False, 0
    if not audio_path.is_file():
        print(f"STOP: audio file is missing: {audio_path.relative_to(PROJECT_DIR)}")
        return False, 0
    if cached_path.exists():
        print("STOP: raw response path already exists; it was not overwritten.")
        return False, 0

    validate_log_file()
    RESULTS_DIR.mkdir(exist_ok=True)
    RAW_DIR.mkdir(exist_ok=True)
    PENDING_DIR.mkdir(exist_ok=True)
    marker = reserve_call(DAY6_ID, model)
    paid_calls = 0
    try:
        import requests
        from dotenv import load_dotenv

        load_dotenv(PROJECT_DIR / ".env", override=False)
        current_key = os.getenv("GNANI_API_KEY")
        if not current_key:
            print("STOP: GNANI_API_KEY is unavailable; no API request was sent.")
            append_log(DAY6_ID, model, language_code, "MISSING_CREDENTIAL", paid_call="NO")
            return False, 0

        data = {"language_code": language_code, "format": "transcribe"}
        if model == "prisma-v3.0":
            data["model"] = model
        print(f"Sending one approved live request: {DAY6_ID} | {model}")
        try:
            with audio_path.open("rb") as audio:
                response = requests.post(
                    API_URL,
                    headers={"X-API-Key-ID": current_key},
                    files={"audio_file": (audio_path.name, audio, "audio/wav")},
                    data=data,
                    timeout=60,
                )
            paid_calls = 1
        except requests.RequestException:
            paid_calls = 1
            append_log(DAY6_ID, model, language_code, "NETWORK_ERROR", paid_call="UNKNOWN")
            print("STOP: network error; request outcome and billing are unknown. No retry was made.")
            return False, paid_calls
        except OSError:
            append_log(DAY6_ID, model, language_code, "LOCAL_AUDIO_READ_ERROR", paid_call="NO")
            print("STOP: audio could not be opened; no API request was sent.")
            return False, 0

        body = response.content
        write_raw_response(cached_path, body)
        try:
            result = response.json()
        except ValueError:
            result = None

        request_id = result.get("request_id", "") if isinstance(result, dict) else ""
        status = "HTTP_ERROR"
        if response.status_code == 429:
            status = "RATE_LIMITED"
        elif response.status_code == 402:
            status = "INSUFFICIENT_CREDIT"
        elif response.status_code == 403:
            status = "FORBIDDEN_SCOPE"
        elif response.ok and is_successful_response(result):
            status = "SUCCESS"
        elif response.ok:
            status = "INVALID_RESPONSE"
        append_log(
            DAY6_ID,
            model,
            language_code,
            status,
            http_status=response.status_code,
            request_id=request_id,
            paid_call="YES",
            raw_file=str(cached_path.relative_to(PROJECT_DIR)),
        )
        if status != "SUCCESS":
            print(f"STOP: request returned {status} (HTTP {response.status_code}). No retry was made.")
            return False, paid_calls
        print(f"Saved successful response: {cached_path.relative_to(PROJECT_DIR)}")
        return True, paid_calls
    finally:
        marker.unlink(missing_ok=True)
        if paid_calls:
            print(f"API requests submitted in this step: {paid_calls} (billing may be unknown)")


def main():
    parser = argparse.ArgumentParser(
        description="Day 6 Prisma model comparison; defaults to a no-network dry run."
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="enable paid API requests; prompts separately before each uncached request",
    )
    args = parser.parse_args()

    item, language_code, audio_path = get_day6_item()
    print_plan(item, language_code, audio_path)
    if not args.live:
        return 0

    if not audio_path.is_file():
        print("STOP: no requests were sent because the audio file is missing.")
        return 1
    print("Live mode can spend credits. Each cache miss requires typing SEND.")
    requests_submitted = 0
    exit_code = 0
    for model in MODELS:
        state = cache_state(DAY6_ID, model)
        if state == "cached success":
            succeeded, submitted = request_one(language_code, audio_path, model)
            requests_submitted += submitted
            if not succeeded:
                return 1
            continue
        if state != "miss":
            print(f"STOP: {state} for {DAY6_ID} {model}; inspect before proceeding.")
            exit_code = 1
            break
        confirmation = input(f"Type SEND to make one paid request for {DAY6_ID} {model}: ")
        if confirmation != "SEND":
            print("Cancelled; no request was sent for this model.")
            break
        succeeded, submitted = request_one(language_code, audio_path, model)
        requests_submitted += submitted
        if not succeeded:
            exit_code = 1
            break
    print(f"API requests submitted in this run: {requests_submitted} (billing must be confirmed from balance)")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
