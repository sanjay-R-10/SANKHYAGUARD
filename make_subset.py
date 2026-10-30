import csv

CHOSEN = ["en_01", "en_02", "kn_01", "en_11", "en_12", "kn_11", "kn_12", "hi_11"]
rows = {r["id"]: r for r in csv.DictReader(open("dataset_script.csv", encoding="utf-8"))}
with open("subset.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id", "language", "kind", "expected_len", "truth", "read_this"])
    for i in CHOSEN:
        r = rows[i]
        w.writerow([i, r["language"], r["kind"], r["expected_len"], r["truth"], r["read_this"]])
        print(i, "|", r["kind"], "|", r["read_this"])
print("Wrote subset.csv")
