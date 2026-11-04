"""Make text safe for mms-tts-ara.

The model only knows Arabic letters. Latin letters and digits are skipped or garbled,
which is the usual cause of a silent or mumbling file. So: units -> Arabic words,
numbers -> Arabic words, then drop any leftover Latin letters.
"""
import re

from num2words import num2words

# Order matters: longer / more specific patterns first.
_UNITS = [
    (re.compile(r"km\s*/\s*h", re.I), " كيلومتر في الساعة "),
    (re.compile(r"°\s*C", re.I), " درجة مئوية "),
    (re.compile(r"°"), " درجة "),
    (re.compile(r"%"), " بالمئة "),
]
_ARABIC_INDIC = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_NUMBER = re.compile(r"(-)?(\d+)(?:[.,](\d+))?")
_LATIN = re.compile(r"[A-Za-z]+")
_SPACES = re.compile(r"\s+")


def _number_to_words(m: re.Match) -> str:
    neg, whole, frac = m.group(1), m.group(2), m.group(3)
    words = num2words(int(whole), lang="ar")
    if frac:
        words += " فاصلة " + num2words(int(frac), lang="ar")
    return f" {'سالب ' if neg else ''}{words} "


def normalize_ar(text: str) -> str:
    text = text.translate(_ARABIC_INDIC)
    for pattern, repl in _UNITS:
        text = pattern.sub(repl, text)
    text = _NUMBER.sub(_number_to_words, text)
    text = _LATIN.sub(" ", text)
    return _SPACES.sub(" ", text).strip()
