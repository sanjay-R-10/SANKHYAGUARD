import re

# English digit words
EN_DIGITS = {
    "zero": 0,
    "oh": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
}

EN_TEENS = {
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
}

EN_TENS = {
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}

# Kannada digit words
KN_DIGITS = {
    "ಸೊನ್ನೆ": 0,
    "ಒಂದು": 1,
    "ಎರಡು": 2,
    "ಮೂರು": 3,
    "ನಾಲ್ಕು": 4,
    "ಐದು": 5,
    "ಆರು": 6,
    "ಏಳು": 7,
    "ಎಂಟು": 8,
    "ಒಂಬತ್ತು": 9,
}

KN_TENS = {
    "ಹತ್ತು": 10,
    "ಇಪ್ಪತ್ತು": 20,
    "ಮೂವತ್ತು": 30,
    "ನಲವತ್ತು": 40,
    "ಐವತ್ತು": 50,
    "ಅರವತ್ತು": 60,
    "ಎಪ್ಪತ್ತು": 70,
    "ಎಂಬತ್ತು": 80,
    "ತೊಂಬತ್ತು": 90,
}

DIGIT_WORDS = {
    **EN_DIGITS,
    **KN_DIGITS,
}

NUMBER_WORDS = {
    **EN_DIGITS,
    **EN_TEENS,
    **EN_TENS,
    **KN_DIGITS,
    **KN_TENS,
}

HUNDRED = {
    "hundred",
    "ನೂರು",
}

SCALE = {
    "thousand": 1000,
    "lakh": 100000,
    "lakhs": 100000,
    "crore": 10000000,
    "crores": 10000000,
    "ಸಾವಿರ": 1000,
    "ಲಕ್ಷ": 100000,
    "ಕೋಟಿ": 10000000,
}

MULT = {
    "double": 2,
    "triple": 3,
}

FILLER = {
    "and",
    "only",
}

# Convert Kannada and Devanagari numerals into English digits
NUMERALS = str.maketrans(
    "೦೧೨೩೪೫೬೭೮೯०१२३४५६७८९",
    "01234567890123456789",
)


def tokenise(text):
    text = text.lower().translate(NUMERALS)

    # Remove commas inside numbers
    text = re.sub(r"(?<=\d),(?=\d)", "", text)

    # Remove currency words and symbols
    text = re.sub(
        r"₹|\brs\b\.?|\brupees?\b|\brupaye\b|ರೂಪಾಯಿ",
        " ",
        text,
    )

    # Remove punctuation
    text = re.sub(r"[.,;:!?|।\-]", " ", text)

    return text.split()


def parse_digit_string(text):
    output = []
    unknown = []
    repeat = 1

    for token in tokenise(text):

        if token in MULT:
            repeat = MULT[token]

        elif token.isdigit():
            output.append(token if len(token) > 1 else token * repeat)
            repeat = 1

        elif token in DIGIT_WORDS:
            output.append(str(DIGIT_WORDS[token]) * repeat)
            repeat = 1

        else:
            unknown.append(token)

    return {
        "digits": "".join(output),
        "unknown": unknown,
    }


def parse_amount(text):
    total = 0
    current = 0
    unknown = []
    seen = False

    for token in tokenise(text):

        if token in FILLER:
            continue

        elif token.isdigit():
            current += int(token)
            seen = True

        elif token in NUMBER_WORDS:
            current += NUMBER_WORDS[token]
            seen = True

        elif token in HUNDRED:
            current = (current or 1) * 100
            seen = True

        elif token in SCALE:
            total += (current or 1) * SCALE[token]
            current = 0
            seen = True

        else:
            unknown.append(token)

    value = total + current

    return {
        "value": value if (seen and not unknown) else None,
        "unknown": unknown,
    }