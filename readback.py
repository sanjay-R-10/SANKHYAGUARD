import hashlib
import os
from pathlib import Path

import requests

from ui_helpers import indian


TTS_URL = "https://api.vachana.ai/api/v1/tts/inference"
LANG = {"en": "en-IN", "kn": "kn-IN", "hi": "hi-IN"}
CACHE = str(Path(__file__).resolve().parent / "tts_cache")
TEMPLATES = {
    "en": {
        "two": "I heard two possible values. First: {a}. Second: {b}. Which one is correct? Say one or two.",
        "one": "I heard {a}. Is that correct? Say yes or no.",
        "none": "Sorry, I could not understand the number clearly. Please say it again.",
    },
    "kn": {
        "two": "ನನಗೆ ಎರಡು ಸಾಧ್ಯತೆಗಳು ಕೇಳಿಸಿದವು. ಮೊದಲನೆಯದು: {a}. ಎರಡನೆಯದು: {b}. ಯಾವುದು ಸರಿ? ಒಂದು ಅಥವಾ ಎರಡು ಎಂದು ಹೇಳಿ.",
        "one": "ನನಗೆ {a} ಎಂದು ಕೇಳಿಸಿತು. ಇದು ಸರಿಯೇ? ಹೌದು ಅಥವಾ ಇಲ್ಲ ಎಂದು ಹೇಳಿ.",
        "none": "ಕ್ಷಮಿಸಿ, ಸಂಖ್ಯೆ ಸ್ಪಷ್ಟವಾಗಿ ಅರ್ಥವಾಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೊಮ್ಮೆ ಹೇಳಿ.",
    },
    "hi": {
        "two": "मुझे दो संभावित मान सुनाई दिए। पहला: {a}। दूसरा: {b}। कौन सा सही है? एक या दो कहिए।",
        "one": "मुझे {a} सुनाई दिया। क्या यह सही है? हाँ या नहीं बोलिए।",
        "none": "माफ़ कीजिए, मैं संख्या साफ़ नहीं समझ पाया। कृपया दोबारा बोलिए।",
    },
}


def spoken_value(kind, value):
    return " ".join(str(value)) if kind == "digits" else f"₹{indian(value)}"


def readback_text(kind, candidates, lang):
    template = TEMPLATES[lang]
    if not candidates:
        return template["none"]
    if len(candidates) == 1:
        return template["one"].format(a=spoken_value(kind, candidates[0]))
    return template["two"].format(
        a=spoken_value(kind, candidates[0]),
        b=spoken_value(kind, candidates[1]),
    )


def cache_path(text, lang, voice="Shivani", model="timbre-v3.0"):
    key = hashlib.sha1(
        f"{model}|{voice}|{LANG[lang]}|{text}".encode("utf-8")
    ).hexdigest()[:16]
    return os.path.join(CACHE, key + ".wav")


def synthesize(text, lang, voice="Shivani", model="timbre-v3.0"):
    path = cache_path(text, lang, voice, model)
    if os.path.isfile(path):
        return path
    raise RuntimeError(
        "Timbre synthesis is disabled in this offline Replay Mode build. "
        "No API request was sent."
    )
