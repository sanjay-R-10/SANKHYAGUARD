import csv, random

random.seed(42)
LANGS = {"en": "English", "kn": "Kannada", "hi": "Hindi"}


def indian_format(n):
    s = str(n)
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:]); head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts + [tail])


HARD = [13000, 30000, 14000, 40000, 15000, 50000, 16000, 60000,
        17000, 70000, 18000, 80000, 19000, 90000]

rows = []
for code, name in LANGS.items():
    n = 0
    for _ in range(6):
        n += 1
        num = str(random.choice("6789")) + "".join(random.choice("0123456789") for _ in range(9))
        rows.append([f"{code}_{n:02d}", code, "digits", 10, num,
                     " ".join(num), f"Say these 10 digits one by one in {name}"])
    for _ in range(4):
        n += 1
        num = "".join(random.choice("0123456789") for _ in range(6))
        rows.append([f"{code}_{n:02d}", code, "digits", 6, num,
                     " ".join(num), f"Say these 6 digits one by one in {name}"])
    for amt in HARD:
        n += 1
        rows.append([f"{code}_{n:02d}", code, "amount", "", amt,
                     "Rs. " + indian_format(amt), f"Say this amount in {name}, the way you normally would"])

with open("dataset_script.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id", "language", "kind", "expected_len", "truth", "read_this", "instruction"])
    w.writerows(rows)
print(len(rows), "items written to dataset_script.csv")