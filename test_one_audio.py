import os
from pathlib import Path

import requests
from dotenv import load_dotenv

# Project settings
PROJECT_DIR = Path(__file__).parent
AUDIO_DIR = PROJECT_DIR / "audio_mp3"
AUDIO_FILE = AUDIO_DIR / "ka_1.mp3"

load_dotenv(PROJECT_DIR / ".env")

API_KEY = os.getenv("GNANI_API_KEY")
API_URL = "https://api.vachana.ai/stt/v3"

# Check the setup before sending anything
if not API_KEY:
    raise SystemExit("ERROR: GNANI_API_KEY not found in .env")

if not AUDIO_FILE.is_file():
    raise SystemExit(f"ERROR: Audio file not found: {AUDIO_FILE}")

print("File:", AUDIO_FILE.name)
print("Language: Kannada (kn-IN)")
print("Sending one recording to Gnani...")

try:
    with AUDIO_FILE.open("rb") as audio:
        response = requests.post(
            API_URL,
            headers={"X-API-Key-ID": API_KEY},
            files={
                "audio_file": (
                    AUDIO_FILE.name,
                    audio,
                    "audio/mpeg",
                )
            },
            data={
                "language_code": "kn-IN",
                "format": "transcribe",
            },
            timeout=60,
        )

    print("\nHTTP status:", response.status_code)

    try:
        result = response.json()
    except ValueError:
        print("The server returned a non-JSON response.")
        print(response.text[:500])
        raise SystemExit

    if response.ok and result.get("success"):
        print("\nGnani transcription:")
        print(result.get("transcript", "No transcript returned"))
    else:
        print("\nAPI returned an error:")
        print(result)

except requests.RequestException as error:
    print("\nConnection error:", error)
