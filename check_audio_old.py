from pathlib import Path
import csv

PROJECT_DIR = Path(__file__).parent
AUDIO_DIR = PROJECT_DIR / "audio_mp3"
TRUTH_FILE = PROJECT_DIR / "truth.csv"

# Map the answer-key names to your actual audio filenames
filename_map = {
    "en_1": "en_01.mp3",
    "en_2": "en_02.mp3",
    "en_3": "en_03.mp3",
    "en_4": "en_04.mp3",
    "ka_1": "kn_01.mp3",
    "ka_2": "kn_02.mp3",
    "ka_3": "kn_03.mp3",
}

print("\n=== SankhyaGuard: Audio File Check ===\n")

with open(TRUTH_FILE, "r", newline="", encoding="utf-8") as file:
    rows = list(csv.DictReader(file))

all_ok = True

for row in rows:
    name = row["file"]
    filename = filename_map.get(name, name + ".mp3")
    audio_path = AUDIO_DIR / filename

    if audio_path.exists():
        size_kb = audio_path.stat().st_size / 1024
        print(f"OK   | {filename} | {size_kb:.1f} KB")
    else:
        print(f"MISS | {filename} | File not found")
        all_ok = False

print("\n------------------------------")
print("SUCCESS: All audio files are present!" if all_ok else
      "WARNING: Some files are missing. Check the filenames.")
print(f"Total recordings in truth.csv: {len(rows)}")