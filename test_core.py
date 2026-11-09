from core import analyse, parse_reply

# disagreement -> ask, with two candidates and highlighted positions
r = analyse("digits", {"v2.5 number": "9001338908", "v2.5 words": "nine zero zero one three three eight nine zero eight",
                       "v3.0": "9001338980"}, 10, "en")
assert r["decision"] == "CONFIRM" and r["positions"] == [9, 10], r
assert [c["value"] for c in r["candidates"]] == ["9001338908", "9001338980"]
assert r["readback_text"].startswith("I heard two possible values")
assert r["normal_value"] == "9001338908"

# agreement -> accept, no read-back text
r = analyse("amount", {"v2.5 number": "₹50,000", "v2.5 words": "fifty thousand rupees", "v3.0": "₹50,000"}, None, "en")
assert r["decision"] == "ACCEPT" and r["value"] == "50000" and r["value_pretty"] == "₹50,000" and r["readback_text"] is None

# nothing understood -> ask to repeat
r = analyse("digits", {"v2.5 number": "<EMPTY>"}, 10, "en")
assert r["decision"] == "CONFIRM" and r["candidates"] == [] and "again" in r["readback_text"]

# spoken replies
for text, want in [("one", "1"), ("Two.", "2"), ("number two please", "2"), ("yes", "yes"), ("No", "no"),
                   ("ಎರಡು", "2"), ("ಒಂದು", "1"), ("ಹೌದು", "yes"), ("ಇಲ್ಲ", "no"),
                   ("एक", "1"), ("दो", "2"), ("हाँ", "yes"), ("नहीं", "no"),
                   ("no, the second one is two", "2"), ("hmm", None), ("", None)]:
    assert parse_reply(text) == want, (text, parse_reply(text), want)
print("Core tests passed")
