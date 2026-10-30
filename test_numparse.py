from numparse import parse_digit_string as d, parse_amount as a, HI_ALL, KN_TENS_FUSED

assert d("seven three zero four nine one six eight two five")["digits"] == "7304916825"
assert d("7 3 0 4 9 1 6 8 2 5")["digits"] == "7304916825"
assert d("98765 43210")["digits"] == "9876543210"
assert d("double five three")["digits"] == "553"
assert d("ಏಳು ಮೂರು ಸೊನ್ನೆ ನಾಲ್ಕು")["digits"] == "7304"
assert d("೭೩೦೪")["digits"] == "7304"
assert d("सात तीन शून्य चार")["digits"] == "7304"
assert d("saat teen oh char")["digits"] == "7304"
assert d("heaven three")["unknown"] == ["heaven"]

assert a("twenty five thousand")["value"] == 25000
assert a("two lakh fifty thousand")["value"] == 250000
assert a("one hundred and twenty five")["value"] == 125
assert a("one crore")["value"] == 10000000
assert a("fifteen thousand")["value"] == 15000
assert a("fifty thousand")["value"] == 50000
assert a("₹2,50,000")["value"] == 250000
assert a("1.5 lakh")["value"] == 150000
assert a("two thousand five hundred rupees")["value"] == 2500

assert a("two five zero zero zero")["value"] is None
assert a("two thousand five lakh")["value"] is None
assert a("fifty fifty")["value"] is None
assert a("")["value"] is None
assert a("hello")["value"] is None

assert len(HI_ALL) >= 100
assert KN_TENS_FUSED["ಇಪ್ಪತ್ತೈದು"] == 25
assert KN_TENS_FUSED["ತೊಂಬತ್ತೊಂಬತ್ತು"] == 99
assert a("ಎರಡು ಲಕ್ಷ ಐವತ್ತು ಸಾವಿರ")["value"] == 250000
assert a("ಇಪ್ಪತ್ತೈದು ಸಾವಿರ ರೂಪಾಯಿ")["value"] == 25000
assert a("ಹದಿನೈದು ಸಾವಿರ")["value"] == 15000
assert a("ಐದು ಸಾವಿರ ಐನೂರು")["value"] == 5500
assert a("पचास हज़ार रुपये")["value"] == 50000
assert a("पंद्रह हज़ार")["value"] == 15000
assert a("तीन लाख बीस हज़ार")["value"] == 320000
assert a("दो सौ पचास")["value"] == 250
assert a("pachaas hazaar")["value"] == 50000
print("All tests passed")