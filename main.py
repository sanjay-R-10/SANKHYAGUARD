
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

# Load the API key from .env
load_dotenv()

API_KEY = os.getenv("GNANI_API_KEY")
API_URL = "https://api.vachana.ai/stt/v3"

# Use the converted MP3 file directly
audio_path = Path("audio") / "clip1.mp3"

if not audio_path.is_file():
    print("ERROR: audio/clip1.mp3 not found.")
    raise SystemExit

if not API_KEY:
    print("ERROR: Gnani API key not found.")
    raise SystemExit

print("Audio found:", audio_path.name)
print("Sending audio to Gnani...")

try:
    with audio_path.open("rb") as audio:
        response = requests.post(
            API_URL,
            headers={"X-API-Key-ID": API_KEY},
            files={
                "audio_file": (
                    audio_path.name,
                    audio,
                    "audio/mpeg"
                )
            },
            data={
                "language_code": "en-IN",
                "format": "transcribe"
            },
            timeout=60
        )

    print("HTTP status:", response.status_code)

    try:
        result = response.json()
    except ValueError:
        print("Gnani returned a non-JSON response:")
        print(response.text[:1000])
        raise SystemExit

    if response.ok and result.get("success"):
        print("\nRecognized text:")
        print(result.get("transcript", "No transcript returned."))
    else:
        print("Gnani returned an error:")
        print(result)

except requests.RequestException as error:
    print("Connection error:", error)
