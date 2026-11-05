import csv, sys
from collections import Counter, defaultdict
from guard import decide, parse_view

VIEW_FIELDS = ("view_verbatim", "view_itn", "view_v2_5", "view_v3_0", "read_this")


def read_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def build_views(row):
    # Current dataset uses read_this, not view_verbatim/view_itn.
    views = {}
    for key in VIEW_FIELDS:
        if row.get(key) not in (None, ""):
            views[key] = row[key]
    if not views:
        return {}
    return views


def evaluate_rows(rows):
    stats = defaultdict(lambda: defaultdict(int))
    skip_reasons = Counter()
    skipped_ids = defaultdict(list)
    evaluated_rows = 0
    for row_number, row in enumerate(rows, start=1):
        truth = (row.get("truth") or "").strip()
        if not truth:
            reason = "missing_expected_value"
            skip_reasons[reason] += 1
            skipped_ids[reason].append(row.get("id") or f"row {row_number}")
            continue
        views = build_views(row)
        if not views:
            if not any(key in row for key in VIEW_FIELDS):
                reason = "missing_views"
            elif any(row.get(f"{model}_status") not in (None, "", "MISSING", "SUCCESS")
                     for model in ("v2_5", "v3_0")):
                reason = "unavailable_model_response"
            elif (
                any(row.get(f"{model}_status") == "SUCCESS"
                    for model in ("v2_5", "v3_0"))
                and any(row.get(f"{model}_status") == "MISSING"
                        for model in ("v2_5", "v3_0"))
            ):
                reason = "unavailable_model_response"
            elif any(row.get(f"{model}_status") == "SUCCESS"
                     for model in ("v2_5", "v3_0")):
                reason = "empty_transcript"
            elif any(f"{model}_status" in row for model in ("v2_5", "v3_0")):
                reason = "missing_model_responses"
            else:
                reason = "empty_transcript"
            skip_reasons[reason] += 1
            skipped_ids[reason].append(row.get("id") or f"row {row_number}")
            continue

        kind = row["kind"]
        truth_val = truth if kind == "digits" else int(truth)
        evaluated_rows += 1
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
    return {
        "input_rows": len(rows),
        "evaluated_rows": evaluated_rows,
        "skipped_rows": len(rows) - evaluated_rows,
        "skip_reasons": skip_reasons,
        "skipped_ids": skipped_ids,
        "stats": stats,
    }


def evaluate(path):
    return evaluate_rows(read_rows(path))


def run(path):
    """Keep the original metrics-only return value for existing callers."""
    return evaluate(path)["stats"]


def show(stats, accounting=None):
    if accounting is not None:
        print(
            f"Rows: input={accounting['input_rows']} "
            f"evaluated={accounting['evaluated_rows']} "
            f"skipped={accounting['skipped_rows']}"
        )
        for reason, count in sorted(accounting["skip_reasons"].items()):
            ids = ", ".join(accounting["skipped_ids"][reason])
            print(f"Skipped ({reason}): {count} [{ids}]")
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
    report = evaluate(sys.argv[1] if len(sys.argv) > 1 else "demo_results.csv")
    show(report["stats"], report)