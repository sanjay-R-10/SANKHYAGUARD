import csv
from numparse import parse_amount

TRANSCRIPTS_FILE = "transcripts.csv"
TRUTH_FILE = "truth.csv"


def read_csv(filename):
    with open(filename, "r", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


transcripts = read_csv(TRANSCRIPTS_FILE)
truth = read_csv(TRUTH_FILE)

truth_values = {}

for row in truth:
    filename = row.get("file", "").strip()
    true_number = row.get("true_value", "").strip()
    if filename:
        truth_values[filename] = true_number


print("\nSANKHYAGUARD NUMBER COMPARISON")
print("-" * 40)

for row in transcripts:
    filename = row.get("file", "").strip()
    transcript = row.get("transcript", "").strip()

    if not filename:
        continue

    expected = truth_values.get(filename, "")

    if not transcript:
        print(f"{filename}: Transcript missing")
        continue

    predicted = parse_amount(transcript)

    print(f"\nAudio: {filename}")
    print(f"Gnani transcript: {transcript}")
    print(f"Parsed number: {predicted}")
    print(f"Truth number: {expected}")

    parsed_value = predicted["value"]

    if str(parsed_value) == str(expected):
     print("RESULT: MATCH ✅")
    else:
     print("RESULT: MISMATCH ❌")