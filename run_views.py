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


def get_work_items(pilot, selected_id, languages=None):
    rows = {row["id"]: row for row in read_csv(DATASET_FILE)}
    if pilot:
        selected = read_csv(SUBSET_FILE)
        ids = [row["id"] for row in selected]
        if len(ids) != 8 or len(set(ids)) != 8:
            raise ValueError(f"{SUBSET_FILE.name} must contain exactly 8 unique IDs")
    else:
        ids = [DAY6_ID]
    if selected_id:
        if selected_id not in ids:
            raise ValueError(f"{selected_id} is not included in the selected experiment")
        ids = [selected_id]
    if languages:
        unknown = set(languages) - set(LANGUAGE_CODES)
        if unknown:
            raise ValueError(f"Unsupported language(s): {', '.join(sorted(unknown))}")
        ids = [audio_id for audio_id in ids if rows[audio_id].get("language") in languages]
        if not ids:
            raise ValueError("No clips match the selected language filter")
    items = []
    for audio_id in ids:
        if audio_id not in rows:
            raise ValueError(f"{audio_id} is missing from {DATASET_FILE.name}")
        item = rows[audio_id]
        language_code = LANGUAGE_CODES.get(item.get("language"))
        if not language_code:
            raise ValueError(f"Unsupported language for {audio_id}")
        items.append((item, language_code, AUDIO_DIR / f"{audio_id}.wav"))
    return items


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


def print_plan(items, pilot, models):
    print("Mode: DRY RUN (no network requests)")
    print("Format: transcribe")
    request_count = len(items) * len(models)
    print(f"Experiment: {'Day 7 subset' if pilot else 'Day 6 single clip'}")
    print(f"Maximum planned requests: {request_count} (sequential, one audio/model per request)")
    cache_counts = {"cached success": 0, "miss": 0, "blocked": 0}
    missing_audio = 0
    for item, language_code, audio_path in items:
        audio_id = item["id"]
        audio_state = "present" if audio_path.is_file() else "MISSING"
        missing_audio += audio_state == "MISSING"
        for model in models:
            state = cache_state(audio_id, model)
            if state == "miss":
                previous_call = prior_call_state(audio_id, model)
                if previous_call:
                    state = f"blocked by prior call log ({previous_call})"
            if state == "cached success":
                cache_counts["cached success"] += 1
            elif state == "miss":
                cache_counts["miss"] += 1
            else:
                cache_counts["blocked"] += 1
            print(
                f"Planned: {audio_id} | {model} | {language_code} | "
                f"{audio_path.relative_to(PROJECT_DIR)} | audio: {audio_state} | cache: {state}"
            )
    print(f"Cached successful responses to reuse: {cache_counts['cached success']}")
    print(f"New requests requiring approval: {cache_counts['miss']}")
    print(f"Blocked items needing manual review: {cache_counts['blocked']}")
    print(f"Missing clean audio files: {missing_audio}")
    print("A cache hit is reused and does not send a request.")
    print("Live mode prompts separately before every uncached request.")
    print("API requests submitted: 0")


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


def request_one(audio_id, language_code, audio_path, model, api_key):
    cached_path = raw_path(audio_id, model)
    state = cache_state(audio_id, model)
    if state == "cached success":
        print(f"Reusing cached success: {cached_path.relative_to(PROJECT_DIR)}")
        append_log(
            audio_id,
            model,
            language_code,
            "CACHE_HIT",
            paid_call="NO",
            raw_file=str(cached_path.relative_to(PROJECT_DIR)),
        )
        return True, 0
    if state != "miss":
        print(f"STOP: {state} for {audio_id} {model}; no duplicate request sent.")
        return False, 0
    previous_call = prior_call_state(audio_id, model)
    if previous_call:
        print(
            f"STOP: a prior request is logged as {previous_call} for {audio_id} "
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
    marker = reserve_call(audio_id, model)
    request_submitted = False
    try:
        data = {"language_code": language_code, "format": "transcribe"}
        if model == "prisma-v3.0":
            data["model"] = model
        import requests

        print(f"Sending one approved live request: {audio_id} | {model}")
        try:
            with audio_path.open("rb") as audio:
                response = requests.post(
                    API_URL,
                    headers={"X-API-Key-ID": api_key},
                    files={"audio_file": (audio_path.name, audio, "audio/wav")},
                    data=data,
                    timeout=60,
                )
            request_submitted = True
        except requests.RequestException:
            request_submitted = True
            append_log(audio_id, model, language_code, "NETWORK_ERROR", paid_call="UNKNOWN")
            print("STOP: network error; request outcome and billing are unknown. No retry was made.")
            return False, 1
        except OSError:
            append_log(audio_id, model, language_code, "LOCAL_AUDIO_READ_ERROR", paid_call="NO")
            print("STOP: audio could not be opened; no API request was sent.")
            return False, 0

        write_raw_response(cached_path, response.content)
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
            audio_id,
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
            return False, 1
        print(f"Saved successful response: {cached_path.relative_to(PROJECT_DIR)}")
        return True, 1
    finally:
        marker.unlink(missing_ok=True)
        if request_submitted:
            print("API request submitted (billing must be confirmed from balance).")


def main():
    parser = argparse.ArgumentParser(
        description="Day 6/7 Prisma runner; defaults to a no-network dry run."
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="enable paid API requests; prompts separately before each uncached request",
    )
    parser.add_argument(
        "--pilot",
        action="store_true",
        help="use all eight clean clips from subset.csv instead of only en_01",
    )
    parser.add_argument(
        "--id",
        choices=tuple(row["id"] for row in read_csv(SUBSET_FILE)),
        help="limit this run to one subset clip (or en_01 for Day 6)",
    )
    parser.add_argument(
        "--model",
        choices=MODELS,
        help="limit this run to one model",
    )
    parser.add_argument(
        "--langs",
        help="comma-separated language filter: en,kn,hi",
    )
    args = parser.parse_args()

    languages = None
    if args.langs:
        languages = {language.strip().lower() for language in args.langs.split(",") if language.strip()}
        if not languages:
            parser.error("--langs must include at least one language")
        unknown = languages - set(LANGUAGE_CODES)
        if unknown:
            parser.error(f"unsupported --langs value(s): {', '.join(sorted(unknown))}")

    items = get_work_items(args.pilot, args.id, languages)
    models = (args.model,) if args.model else MODELS
    print_plan(items, args.pilot, models)
    if not args.live:
        return 0

    missing = [path for _, _, path in items if not path.is_file()]
    if missing:
        print("STOP: no requests were sent because a clean audio file is missing:")
        for path in missing:
            print(f"  {path.relative_to(PROJECT_DIR)}")
        return 1
    for item, _, _ in items:
        for model in models:
            state = cache_state(item["id"], model)
            if state == "miss" and prior_call_state(item["id"], model):
                print(
                    f"STOP: a prior call has no reusable cache for {item['id']} "
                    f"{model}; inspect the log before any live execution."
                )
                return 1

    validate_log_file()
    from dotenv import load_dotenv

    load_dotenv(PROJECT_DIR / ".env", override=False)
    api_key = os.getenv("GNANI_API_KEY")
    if not api_key:
        print("STOP: GNANI_API_KEY is unavailable; no API request was sent.")
        return 1

    print("Live mode can spend credits. Each cache miss requires typing SEND.")
    requests_submitted = 0
    exit_code = 0
    for item, language_code, audio_path in items:
        audio_id = item["id"]
        for model in models:
            state = cache_state(audio_id, model)
            if state == "cached success":
                succeeded, submitted = request_one(
                    audio_id, language_code, audio_path, model, api_key
                )
                requests_submitted += submitted
                if not succeeded:
                    exit_code = 1
                    break
                continue
            if state != "miss":
                print(f"STOP: {state} for {audio_id} {model}; inspect before proceeding.")
                exit_code = 1
                break
            confirmation = input(
                f"Type SEND to make one paid request for {audio_id} {model}: "
            )
            if confirmation != "SEND":
                print(f"Cancelled; no request was sent for {audio_id} {model}.")
                exit_code = 1
                break
            succeeded, submitted = request_one(
                audio_id, language_code, audio_path, model, api_key
            )
            requests_submitted += submitted
            if not succeeded:
                exit_code = 1
                break
        if exit_code:
            break
    print(f"API requests submitted in this run: {requests_submitted} (billing must be confirmed from balance)")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
