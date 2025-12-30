"""
Linguistic constants for Sakha and Russian language detection.
"""

from typing import Set, List

# Sakha anchor characters (KEEP words with these)
# These characters are unique to Sakha language
SAKHA_ANCHOR_CHARS: Set[str] = {"ҕ", "ҥ", "ө", "һ", "ү"}

# Sakha diphthongs (KEEP words with these)
# Characteristic vowel combinations in Sakha
SAKHA_DIPHTHONGS: List[str] = ["уо", "иэ", "ыа", "үө"]

# Russian marker characters (DELETE words with these)
# These characters are unique to Russian or very rare in Sakha
# Note: 'в' is included but can be disabled via config
RUSSIAN_MARKER_CHARS: Set[str] = {"щ", "ц", "ъ", "ф", "в"}

# Russian morphological patterns (DELETE words ending with these)
# Verb endings
RUSSIAN_VERB_PATTERNS: List[str] = ["ться", "тся", "ешь", "ишь"]

# Adjective endings
RUSSIAN_ADJ_PATTERNS: List[str] = ["ий", "ый", "ая", "ое", "ые"]

# Noun endings
RUSSIAN_NOUN_PATTERNS: List[str] = ["ость", "ение", "ание"]

# Sakha morphological patterns (KEEP words ending with these)
# Plural suffixes with vowel harmony variations
SAKHA_PLURAL_PATTERNS: List[str] = [
    "лар",
    "лер",
    "лор",
    "лөр",
    "тар",
    "тэр",
    "тор",
    "төр",
    "дар",
    "дэр",
    "дор",
    "дөр",
    "нар",
    "нер",
    "нор",
    "нөр",
]

# Possessive suffixes
SAKHA_POSSESSIVE_PATTERNS: List[str] = ["та", "тэ", "тын", "быт"]

# Sakha normalization map for OCR character errors
# Maps common OCR mistakes to correct Sakha characters
# WARNING: Only include mappings that are safe and won't corrupt legitimate Russian words
SAKHA_NORMALIZATION_MAP: dict = {
    "6": "ҕ",  # Digit 6 often confused with ҕ (safe: digits in Cyrillic context are rare)
    "h": "һ",  # Latin h -> Sakha һ (safe: Latin letters in Cyrillic text are OCR errors)
    "H": "Һ",  # Latin H -> Sakha Һ (uppercase) (safe: Latin letters in Cyrillic text are OCR errors)
    "o": "ө",  # Latin o -> Sakha ө (safe: Latin letters in Cyrillic text are OCR errors)
    "O": "Ө",  # Latin O -> Sakha Ө (uppercase) (safe: Latin letters in Cyrillic text are OCR errors)
    "y": "ү",  # Latin y -> Sakha ү (safe: Latin letters in Cyrillic text are OCR errors)
    "Y": "Ү",  # Latin Y -> Sakha Ү (uppercase) (safe: Latin letters in Cyrillic text are OCR errors)
    "8": "ө",  # Digit 8 sometimes resembles ө (safe: digits in Cyrillic context are rare)
    # Note: 'б' -> 'ҕ' removed - too risky, can corrupt Russian words (было, быть, объект, etc.)
    # Note: 'н' -> 'ҥ' is context-dependent and handled separately
}

# All Sakha-specific characters (anchor chars + uppercase variants)
SAKHA_ALL_CHARS: Set[str] = SAKHA_ANCHOR_CHARS | {
    "Һ",  # Uppercase һ
    "Ө",  # Uppercase ө
    "Ү",  # Uppercase ү
    "Ҕ",  # Uppercase ҕ
    "Ҥ",  # Uppercase ҥ
}

# Built-in exceptions for word healer
# Words/patterns that should NOT be merged or repaired
WORD_HEALER_EXCEPTIONS: List[str] = [
    "г.",  # Abbreviation: город (city)
    "стр.",  # Abbreviation: страница (page)
    "т.д.",  # Abbreviation: так далее (etc.)
    "и т.д.",  # Abbreviation: и так далее (and etc.)
    # Note: Short words like 'бу', 'уо', 'ити' are context-dependent
    # and handled with word boundary protection
]

# Word healer boundary and validation constants
WORD_BLOCK_MARKER: str = "[[BLOCK]]"  # Marker for multi-space word boundaries

# Sakha vowels (Cyrillic + Sakha-specific vowels and their uppercase variants)
SAKHA_VOWELS: Set[str] = {
    "а",
    "э",
    "и",
    "о",
    "у",
    "ы",
    "е",
    "ё",
    "ю",
    "я",  # Standard Cyrillic vowels
    "ө",
    "ү",  # Sakha-specific vowels
    "А",
    "Э",
    "И",
    "О",
    "У",
    "Ы",
    "Е",
    "Ё",
    "Ю",
    "Я",  # Uppercase Cyrillic
    "Ө",
    "Ү",  # Uppercase Sakha vowels
}

# Word healer validation limits
MAX_WORD_LENGTH: int = 25  # Maximum word length during merging
MAX_CONSONANT_SEQUENCE: int = 10  # Maximum consecutive consonants before rollback
