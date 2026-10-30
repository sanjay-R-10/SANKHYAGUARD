import csv, sys
from collections import defaultdict
from guard import decide, parse_view


def read_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def build_views(row):
    # Current dataset uses read_this, not view_verbatim/view_itn.
    views = {}
    for key in ("view_verbatim", "view_itn", "read_this"):
        if row.get(key) not in (None, ""):
            views[key] = row[key]
    if not views:
        return {}
    return views


def run(path):
    rows = read_rows(path)
    stats = defaultdict(lambda: defaultdict(int))
    for row in rows:
        kind = row["kind"]
        truth = row["truth"].strip()
        truth_val = truth if kind == "digits" else int(truth)
        views = build_views(row)
        if not views:
            continue
        first_value, _ = parse_view(kind, next(iter(views.values())))
        a_wrong = first_value != truth_val
        exp = int(row["expected_len"]) if row.get("expected_len") else None
        g = decide(kind, views, expected_len=exp)
        for key in ("ALL", row.get("language", "?")):
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