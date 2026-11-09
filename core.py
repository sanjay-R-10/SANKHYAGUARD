"""Logic shared by the web server: turn views into a decision, and understand a spoken reply."""
from guard import decide, parse_view
from numparse import tokenise
from ui_helpers import friendly_reasons, indian
import readback


def pretty(kind, value):
    if value is None:
        return None
    return " ".join(str(value)) if kind == "digits" else f"₹{indian(value)}"


def analyse(kind, views, expected_len, lang):
    if kind not in ("digits", "amount"):
        raise ValueError("Choose digits or amount for number type.")
    if lang not in ("en", "kn", "hi"):
        raise ValueError("Choose English, Kannada, or Hindi.")
    if not isinstance(views, dict) or not views:
        raise ValueError("At least one transcript view is required.")
    if any(not isinstance(text, str) for text in views.values()):
        raise ValueError("Transcript views must be text.")
    shown = []
    for name, text in views.items():
        value, _ = parse_view(kind, text)
        shown.append({"name": name, "text": text,
                      "value": None if value is None else str(value), "pretty": pretty(kind, value)})
    first, _ = parse_view(kind, next(iter(views.values())))
    d = decide(kind, views, expected_len=expected_len)
    cands = [{"value": c, "pretty": pretty(kind, c if kind == "digits" else int(c))} for c in d["candidates"]]
    return {
        "kind": kind, "lang": lang, "views": shown,
        "normal_value": None if first is None else str(first),
        "normal_pretty": pretty(kind, first),
        "decision": d["decision"],
        "value": None if d["value"] is None else str(d["value"]),
        "value_pretty": pretty(kind, d["value"]),
        "candidates": cands,
        "positions": d["disputed_positions"],
        "reasons": friendly_reasons(d["reasons"]),
        "readback_text": readback.readback_text(kind, [c["value"] for c in cands], lang)
        if d["decision"] == "CONFIRM" else None,
    }


ONE = {"one", "1", "first", "ek", "pehla", "एक", "पहला", "पहली", "ಒಂದು", "ಮೊದಲನೆಯದು", "ಮೊದಲ", "ಮೊದಲು"}
TWO = {"two", "2", "second", "dusra", "दो", "दूसरा", "दूसरी", "ಎರಡು", "ಎರಡನೆಯದು", "ಎರಡನೇ"}
YES = {"yes", "yeah", "yep", "correct", "right", "haan", "han", "ji", "हाँ", "हां", "जी", "सही", "ಹೌದು", "ಸರಿ"}
NO = {"no", "nope", "wrong", "nahi", "नहीं", "नही", "गलत", "ಇಲ್ಲ", "ತಪ್ಪು", "ಅಲ್ಲ"}


def parse_reply(text):
    """Returns '1', '2', 'yes', 'no' or None. A number beats yes/no; the last thing said wins."""
    choice = yn = None
    for tok in tokenise(text):
        if tok in ONE:
            choice = "1"
        elif tok in TWO:
            choice = "2"
        elif tok in YES:
            yn = "yes"
        elif tok in NO:
            yn = "no"
    return choice or yn
