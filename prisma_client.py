import os
from pathlib import Path

import requests


API_URL = "https://api.vachana.ai/stt/v3"
PROJECT_DIR = Path(__file__).resolve().parent
LANGUAGE_CODES = {"en": "en-IN", "kn": "kn-IN", "hi": "hi-IN"}
MODELS = {"v25": "prisma-v2.5", "v30": "prisma-v3.0"}
SUPPORTED_EXTENSIONS = {".wav", ".mp3", ".ogg", ".flac", ".aac", ".m4a"}
MIME_TYPES = {
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
    ".aac": "audio/aac",
    ".m4a": "audio/mp4",
}


class PrismaError(RuntimeError):
    def __init__(self, message, *, status_code=None, error_type=None, request_id=""):
        super().__init__(message)
        self.status_code = status_code
        self.error_type = error_type or ""
        self.request_id = request_id or ""


def _api_key():
    from dotenv import load_dotenv

    load_dotenv(PROJECT_DIR / ".env", override=False)
    key = os.getenv("GNANI_API_KEY")
    if not key:
        raise PrismaError(
            "GNANI_API_KEY is not configured. Add it to the project's .env file "
            "or the process environment. The API request was not sent."
        )
    return key


def _error_fields(payload):
    if not isinstance(payload, dict):
        return "", "The API returned a non-JSON error response."
    error = payload.get("error")
    if not isinstance(error, dict):
        error = payload.get("detail")
    if isinstance(error, list):
        messages = [
            item.get("msg", "")
            for item in error
            if isinstance(item, dict) and item.get("msg")
        ]
        return "VALIDATION_ERROR", "; ".join(messages) or "The request was invalid."
    if not isinstance(error, dict):
        error = payload
    error_type = error.get("type") or error.get("error_code") or payload.get("code", "")
    message = error.get("message") or payload.get("message") or "The API request failed."
    return str(error_type), str(message)


def validate_response(response):
    try:
        payload = response.json()
    except ValueError as error:
        raise PrismaError(
            f"Prisma returned HTTP {response.status_code} with an invalid JSON response.",
            status_code=response.status_code,
        ) from error

    if response.status_code != 200:
        error_type, message = _error_fields(payload)
        request_id = payload.get("request_id", "") if isinstance(payload, dict) else ""
        raise PrismaError(
            f"Prisma returned HTTP {response.status_code}"
            f"{f' ({error_type})' if error_type else ''}: {message}",
            status_code=response.status_code,
            error_type=error_type,
            request_id=request_id,
        )
    if not isinstance(payload, dict) or payload.get("success") is not True:
        error_type, message = _error_fields(payload)
        raise PrismaError(
            f"Prisma returned an unsuccessful response"
            f"{f' ({error_type})' if error_type else ''}: {message}",
            status_code=response.status_code,
            error_type=error_type,
        )
    if not isinstance(payload.get("transcript"), str):
        raise PrismaError(
            "Prisma response is missing its transcript string.",
            status_code=response.status_code,
        )
    return payload


def transcribe(audio_bytes, filename, lang_code, model="v25"):
    if not isinstance(audio_bytes, bytes) or not audio_bytes:
        raise ValueError("Recording is empty; no API request was sent.")
    if model not in MODELS:
        raise ValueError(f"Unsupported Prisma model selector: {model}")
    if lang_code not in set(LANGUAGE_CODES.values()):
        raise ValueError(f"Unsupported language code: {lang_code}")
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported audio file extension: {extension or '(none)'}")

    data = {"language_code": lang_code, "format": "transcribe"}
    if model == "v30":
        data["model"] = MODELS[model]
    headers = {"X-API-Key-ID": _api_key()}
    try:
        response = requests.post(
            API_URL,
            headers=headers,
            files={
                "audio_file": (
                    Path(filename).name,
                    audio_bytes,
                    MIME_TYPES[extension],
                )
            },
            data=data,
            timeout=60,
        )
    except requests.RequestException as error:
        raise PrismaError(
            "Network error while contacting Prisma. The request outcome may be "
            "unknown; it was not retried automatically."
        ) from error
    return validate_response(response)
