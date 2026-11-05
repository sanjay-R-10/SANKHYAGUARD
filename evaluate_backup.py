import csv, sys
from collections import defaultdict
from guard import decide, parse_view


def run(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    stats = defaultdict(lambda: defaultdict(int))
    for row in rows:
        kind = row["kind"]
        truth = row["truth"].strip()
        truth_val = truth if kind == "digits" else int(truth)
        views = {k: v for k, v in row.items() if k.startswith("view_") and v is not None and v != ""}
        first_value, _ = parse_view(kind, next(iter(views.values())))
        a_wrong = first_value != truth_val
        exp = int(row["expected_len"]) if row.get("expected_len") else None
        g = decide(kind, views, expected_len=exp)
        for key in ("ALL", row.get("language", "?"), row.get("condition", "?")):
            s = stats[key]
            s["n"] += 1
            s["A_errors"] += a_wrong
            if g["decision"] == "ACCEPT":
                s["G_silent_errors"] += (g["value"] != truth_val)
            else:
                s["G_confirms"] += 1
                s["G_caught"] += a_wrong
                s["G_unneeded"] += (not a_wrong)
    return stats


def show(stats):
    print(f"{'group':14}{'n':>4}{'A: wrong':>10}{'G: wrong':>10}{'G: asks':>9}{'caught':>8}{'needless':>9}")
    for key in sorted(stats, key=lambda k: (k != "ALL", k)):
        s = stats[key]
        print(f"{key:14}{s['n']:>4}{s['A_errors']:>10}{s['G_silent_errors']:>10}"
              f"{s['G_confirms']:>9}{s['G_caught']:>8}{s['G_unneeded']:>9}")
    s = stats["ALL"]
    if s["n"]:
        print(f"\nG wrong-and-silent: {s['G_silent_errors']}/{s['n']}  |  G asks on {s['G_confirms']}/{s['n']}"
              f"  |  A's errors caught by G: {s['G_caught']}/{s['A_errors']}")


if __name__ == "__main__":
    show(run(sys.argv[1] if len(sys.argv) > 1 else "demo_results.csv"))