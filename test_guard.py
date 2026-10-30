from guard import decide

r = decide("digits", {"verbatim": "seven three zero four nine one six eight two five",
                      "itn": "7304916825"}, expected_len=10)
assert r["decision"] == "ACCEPT" and r["value"] == "7304916825", r

r = decide("digits", {"verbatim": "seven three zero four nine one six eight two five",
                      "itn": "7304916852"}, expected_len=10)
assert r["decision"] == "CONFIRM" and "views_disagree" in r["reasons"], r
assert r["disputed_positions"] == [9, 10], r

r = decide("digits", {"itn": "730491682"}, expected_len=10)
assert r["decision"] == "CONFIRM" and "wrong_length" in r["reasons"], r

r = decide("digits", {"verbatim": "seven three zero heaven nine one six eight two five"}, expected_len=10)
assert r["decision"] == "CONFIRM", r

r = decide("digits", {"verbatim": "my number is seven three zero four nine one six eight two five"}, expected_len=10)
assert r["decision"] == "ACCEPT", r

assert decide("amount", {"verbatim": "fifty thousand", "itn": "50,000"})["decision"] == "ACCEPT"
r = decide("amount", {"verbatim": "fifteen thousand", "itn": "50,000"})
assert r["decision"] == "CONFIRM" and r["candidates"] == ["15000", "50000"], r

assert decide("amount", {"verbatim": "hmm okay"})["decision"] == "CONFIRM"
print("Guard tests passed")