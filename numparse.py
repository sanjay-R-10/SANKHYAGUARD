"""SankhyaGuard number parser (v2)."""
import re
import unicodedata

# ---------------- English
EN_UNITS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9}
EN_ZERO = {"zero": 0, "oh": 0}
EN_TEENS = {"ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
            "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19}
EN_TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
           "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}

# ---------------- Kannada
KN_UNITS = {"ಒಂದು": 1, "ಎರಡು": 2, "ಮೂರು": 3, "ನಾಲ್ಕು": 4, "ಐದು": 5,
            "ಆರು": 6, "ಏಳು": 7, "ಎಂಟು": 8, "ಒಂಬತ್ತು": 9}
KN_ZERO = {"ಸೊನ್ನೆ": 0, "ಜೀರೋ": 0}
KN_TEENS = {"ಹತ್ತು": 10, "ಹನ್ನೊಂದು": 11, "ಹನ್ನೆರಡು": 12, "ಹದಿಮೂರು": 13,
            "ಹದಿನಾಲ್ಕು": 14, "ಹದಿನೈದು": 15, "ಹದಿನಾರು": 16, "ಹದಿನೇಳು": 17,
            "ಹದಿನೆಂಟು": 18, "ಹತ್ತೊಂಬತ್ತು": 19}
_KN_STEMS = {"ಇಪ್ಪ": 20, "ಮೂವ": 30, "ನಲವ": 40, "ಐವ": 50,
             "ಅರವ": 60, "ಎಪ್ಪ": 70, "ಎಂಬ": 80, "ತೊಂಬ": 90}
_KN_ENDINGS = {"ತ್ತು": 0, "ತ್ತೊಂದು": 1, "ತ್ತೆರಡು": 2, "ತ್ತಮೂರು": 3, "ತ್ತನಾಲ್ಕು": 4,
               "ತ್ತೈದು": 5, "ತ್ತಾರು": 6, "ತ್ತೇಳು": 7, "ತ್ತೆಂಟು": 8, "ತ್ತೊಂಬತ್ತು": 9}
KN_TENS_FUSED = {stem + end: base + add
                 for stem, base in _KN_STEMS.items()
                 for end, add in _KN_ENDINGS.items()}
KN_HUNDREDS = {"ಇನ್ನೂರು": 200, "ಮುನ್ನೂರು": 300, "ನಾನೂರು": 400, "ಐನೂರು": 500,
               "ಆರುನೂರು": 600, "ಏಳುನೂರು": 700, "ಎಳ್ನೂರು": 700,
               "ಎಂಟುನೂರು": 800, "ಒಂಬೈನೂರು": 900, "ಒಂಬತ್ತುನೂರು": 900}

# ---------------- Hindi (Devanagari), 0..99 in order
_HI_LIST = """
शून्य एक दो तीन चार पाँच छह सात आठ नौ
दस ग्यारह बारह तेरह चौदह पंद्रह सोलह सत्रह अठारह उन्नीस
बीस इक्कीस बाईस तेईस चौबीस पच्चीस छब्बीस सत्ताईस अट्ठाईस उनतीस
तीस इकतीस बत्तीस तैंतीस चौंतीस पैंतीस छत्तीस सैंतीस अड़तीस उनतालीस
चालीस इकतालीस बयालीस तैंतालीस चौवालीस पैंतालीस छियालीस सैंतालीस अड़तालीस उनचास
पचास इक्यावन बावन तिरपन चौवन पचपन छप्पन सत्तावन अट्ठावन उनसठ
साठ इकसठ बासठ तिरसठ चौंसठ पैंसठ छियासठ सड़सठ अड़सठ उनहत्तर
सत्तर इकहत्तर बहत्तर तिहत्तर चौहत्तर पचहत्तर छिहत्तर सतहत्तर अठहत्तर उनासी
अस्सी इक्यासी बयासी तिरासी चौरासी पचासी छियासी सत्तासी अट्ठासी नवासी
नब्बे इक्यानवे बानवे तिरानवे चौरानवे पचानवे छियानवे सत्तानवे अट्ठानवे निन्यानवे
""".split()
HI_ALL = {w: i for i, w in enumerate(_HI_LIST)}
HI_ALL.update({"पांच": 5, "छः": 6, "छे": 6, "पन्द्रह": 15, "तिरेपन": 53})

# ---------------- Hindi in Latin letters (add spellings you see in real output)
ROMAN_HI = {"ek": 1, "do": 2, "teen": 3, "char": 4, "chaar": 4, "paanch": 5, "panch": 5,
            "chhe": 6, "chhah": 6, "chah": 6, "saat": 7, "aath": 8, "nau": 9, "das": 10,
            "bees": 20, "tees": 30, "chalis": 40, "chaalis": 40, "pachas": 50, "pachaas": 50,
            "saath": 60, "sattar": 70, "assi": 80, "nabbe": 90}

# ---------------- word groups
ALL_ZERO = {**EN_ZERO, **KN_ZERO, "शून्य": 0}
ALL_UNITS = {**EN_UNITS, **KN_UNITS,
             **{w: v for w, v in HI_ALL.items() if 1 <= v <= 9},
             **{w: v for w, v in ROMAN_HI.items() if 1 <= v <= 9}}
ALL_BIG = {**EN_TEENS, **EN_TENS, **KN_TEENS, **KN_TENS_FUSED,
           **{w: v for w, v in HI_ALL.items() if v >= 10},
           **{w: v for w, v in ROMAN_HI.items() if v >= 10}}
ALL_HUNDREDS = dict(KN_HUNDREDS)
HUNDRED = {"hundred", "ನೂರು", "सौ", "sau", "सो"}
SCALE = {"thousand": 1000, "lakh": 100000, "lakhs": 100000, "lac": 100000,
         "crore": 10**7, "crores": 10**7,
         "हज़ार": 1000, "हजार": 1000, "hazaar": 1000, "hazar": 1000, "hajar": 1000, "hajaar": 1000,
         "लाख": 100000, "करोड़": 10**7, "करोड": 10**7,
         "ಸಾವಿರ": 1000, "ಲಕ್ಷ": 100000, "ಕೋಟಿ": 10**7}
MULT = {"double": 2, "triple": 3, "डबल": 2, "ट्रिपल": 3, "ಡಬಲ್": 2, "ಟ್ರಿಪಲ್": 3}
FILLER = {"and", "only", "a", "rupees", "rupee", "rupaye", "rupaiye", "rs", "inr",
          "रुपये", "रुपए", "रुपया", "रुपयों", "ರೂಪಾಯಿ", "ರೂಪಾಯಿಗಳು", "ರೂ", "रु", "₹"}


def _n(s):
    return unicodedata.normalize("NFC", s)


def _nd(d):
    return {_n(k): v for k, v in d.items()}


ALL_ZERO, ALL_UNITS, ALL_BIG = _nd(ALL_ZERO), _nd(ALL_UNITS), _nd(ALL_BIG)
ALL_HUNDREDS, SCALE, MULT = _nd(ALL_HUNDREDS), _nd(SCALE), _nd(MULT)
HUNDRED = {_n(w) for w in HUNDRED}
FILLER = {_n(w) for w in FILLER}

NUMERALS = str.maketrans("೦೧೨೩೪೫೬೭೮೯०१२३४५६७८९", "0123456789" * 2)


def tokenise(text):
    t = _n(text).lower().translate(NUMERALS)
    t = re.sub(r"(?<=\d),(?=\d)", "", t)                 # 2,50,000 -> 250000
    t = t.replace("₹", " ₹ ")
    t = re.sub(r"(?<!\d)\.|\.(?!\d)", " ", t)            # sentence dots, keep 1.5
    t = re.sub(r"[,;:!?|।\-]", " ", t)
    return [tok for tok in t.split() if tok not in FILLER]


def _is_number_token(tok):
    return bool(re.fullmatch(r"\d+(\.\d+)?", tok))


# ---------------- digit strings (phone, PIN)
def parse_digit_string(text):
    out, unknown, repeat = [], [], 1
    for tok in tokenise(text):
        if tok in MULT:
            repeat = MULT[tok]
        elif re.fullmatch(r"\d+", tok):
            out.append(tok if len(tok) > 1 else tok * repeat)
            repeat = 1
        elif tok in ALL_ZERO:
            out.append(str(ALL_ZERO[tok]) * repeat)
            repeat = 1
        elif tok in ALL_UNITS:
            out.append(str(ALL_UNITS[tok]) * repeat)
            repeat = 1
        else:
            unknown.append(tok)
    return {"digits": "".join(out), "unknown": unknown}


# ---------------- amounts
def _cls(v):
    if v == 0:
        return "Z"
    if 1 <= v <= 9:
        return "U"
    if 10 <= v <= 19:
        return "T"
    if 20 <= v <= 90 and v % 10 == 0:
        return "Y"
    if 21 <= v <= 99:
        return "F"
    return "?"


def _group_value(tokens):
    if len(tokens) == 1 and _is_number_token(tokens[0]):
        v = float(tokens[0])
        return int(v) if v == int(v) else v
    classes, vals = "", []
    for tok in tokens:
        if tok in HUNDRED:
            classes += "H"; vals.append(100)
        elif tok in ALL_HUNDREDS:
            classes += "K"; vals.append(ALL_HUNDREDS[tok])
        elif tok in ALL_ZERO:
            classes += "Z"; vals.append(0)
        elif tok in ALL_UNITS:
            classes += "U"; vals.append(ALL_UNITS[tok])
        elif tok in ALL_BIG:
            classes += _cls(ALL_BIG[tok]); vals.append(ALL_BIG[tok])
        else:
            return None
    if classes == "Z":
        return 0
    if not re.fullmatch(r"(UH|H|K)?(YU|Y|F|T|U)?", classes) or not classes:
        return None
    total, i = 0, 0
    while i < len(vals):
        if classes[i] == "U" and i + 1 < len(vals) and classes[i + 1] == "H":
            total += vals[i] * 100; i += 2
        else:
            total += vals[i]; i += 1
    return total


def parse_amount(text):
    toks = tokenise(text)
    unknown = [t for t in toks if not (_is_number_token(t) or t in ALL_ZERO or t in ALL_UNITS
               or t in ALL_BIG or t in ALL_HUNDREDS or t in HUNDRED or t in SCALE)]
    if unknown:
        return {"value": None, "unknown": unknown, "reason": "unknown_words"}
    if not toks:
        return {"value": None, "unknown": [], "reason": "empty"}
    total, group, last_scale = 0, [], None
    for tok in toks:
        if tok in SCALE:
            if last_scale is not None and SCALE[tok] >= last_scale:
                return {"value": None, "unknown": [], "reason": "scale_order"}
            gv = 1 if not group else _group_value(group)
            if gv is None:
                return {"value": None, "unknown": [], "reason": "invalid_words"}
            total += gv * SCALE[tok]
            last_scale = SCALE[tok]
            group = []
        else:
            group.append(tok)
    if group:
        gv = _group_value(group)
        if gv is None:
            return {"value": None, "unknown": [], "reason": "invalid_words"}
        total += gv
    if isinstance(total, float) and total == int(total):
        total = int(total)
    return {"value": total, "unknown": [], "reason": "ok"}