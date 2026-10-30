"""Decide ACCEPT or CONFIRM for a spoken number."""
from collections import Counter
from numparse import parse_digit_string, parse_amount


def parse_view(kind, text):
    if kind == "digits":
        r = parse_digit_string(text)
        problems = ["unknown_words"] if r["unknown"] else []
        if not r["digits"]:
            return None, problems + ["no_digits"]
        return r["digits"], problems
    r = parse_amount(text)
    if r["value"] is None:
        return None, [r["reason"]]
    return r["value"], []


def disputed_positions(values):
    if len({len(v) for v in values}) != 1:
        return []
    return [i + 1 for i in range(len(values[0])) if len({v[i] for v in values}) > 1]


def decide(kind, views, expected_len=None):
    parsed, reasons = {}, []
    for name, text in views.items():
        value, problems = parse_view(kind, text)
        parsed[name] = value
        if value is None:
            reasons.append(f"{name}:unparseable")
        if "unknown_words" in problems:
            reasons.append(f"{name}:unknown_words")
    values = [v for v in parsed.values() if v is not None]
    if len(set(values)) > 1:
        reasons.append("views_disagree")
    if kind == "digits" and expected_len:
        if any(len(v) != expected_len for v in values):
            reasons.append("wrong_length")
    best = Counter(values).most_common(1)[0][0] if values else None
    blocking = [r for r in reasons if not r.endswith(":unknown_words")]
    if kind == "digits" and any(r.endswith(":unknown_words") for r in reasons) and expected_len is None:
        blocking.append("unknown_words_and_no_length_check")
    decision = "CONFIRM" if (blocking or best is None) else "ACCEPT"
    return {
        "decision": decision,
        "value": best,
        "candidates": sorted({str(v) for v in values}),
        "reasons": reasons,
        "disputed_positions": disputed_positions([v for v in values if isinstance(v, str)]),
    }