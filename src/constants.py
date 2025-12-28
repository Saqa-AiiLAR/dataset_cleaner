"""
Linguistic constants for Sakha and Russian language detection.
"""
from typing import Set, List

# Sakha anchor characters (KEEP words with these)
# These characters are unique to Sakha language
SAKHA_ANCHOR_CHARS: Set[str] = {'ҕ', 'ҥ', 'ө', 'һ', 'ү'}

# Sakha diphthongs (KEEP words with these)
# Characteristic vowel combinations in Sakha
SAKHA_DIPHTHONGS: List[str] = ['уо', 'иэ', 'ыа', 'үө']

# Russian marker characters (DELETE words with these)
# These characters are unique to Russian or very rare in Sakha
# Note: 'в' is included but can be disabled via config
RUSSIAN_MARKER_CHARS: Set[str] = {'щ', 'ц', 'ъ', 'ф', 'в'}

# Russian morphological patterns (DELETE words ending with these)
# Verb endings
RUSSIAN_VERB_PATTERNS: List[str] = ['ться', 'тся', 'ешь', 'ишь']

# Adjective endings
RUSSIAN_ADJ_PATTERNS: List[str] = ['ий', 'ый', 'ая', 'ое', 'ые']

# Noun endings
RUSSIAN_NOUN_PATTERNS: List[str] = ['ость', 'ение', 'ание']

# Sakha morphological patterns (KEEP words ending with these)
# Plural suffixes with vowel harmony variations
SAKHA_PLURAL_PATTERNS: List[str] = [
    'лар', 'лер', 'лор', 'лөр',
    'тар', 'тэр', 'тор', 'төр',
    'дар', 'дэр', 'дор', 'дөр',
    'нар', 'нер', 'нор', 'нөр'
]

# Possessive suffixes
SAKHA_POSSESSIVE_PATTERNS: List[str] = ['та', 'тэ', 'тын', 'быт']

