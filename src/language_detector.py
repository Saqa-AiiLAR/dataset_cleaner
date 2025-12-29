"""
Language detection and word classification module.
Handles detection of Russian vs Sakha words using multiple strategies.
"""
from typing import Optional, Set
from pathlib import Path
import regex
import logging
from langdetect import detect
import pymorphy2
from natasha import (
    Segmenter,
    MorphVocab,
    NamesExtractor
)

from .config import config
from .constants import (
    SAKHA_ANCHOR_CHARS,
    SAKHA_DIPHTHONGS,
    RUSSIAN_MARKER_CHARS,
    RUSSIAN_VERB_PATTERNS,
    RUSSIAN_ADJ_PATTERNS,
    RUSSIAN_NOUN_PATTERNS,
    SAKHA_PLURAL_PATTERNS,
    SAKHA_POSSESSIVE_PATTERNS,
)

_CYRILLIC_RE = regex.compile(r'\p{IsCyrillic}+')
logger = logging.getLogger("SaqaParser.language_detector")


class AdditionalRulesLoader:
    """
    Loads words and their stems from text files in the additional folder.
    
    Words from additional folder are treated as Russian words (to be removed).
    """
    
    def __init__(self, additional_folder: Optional[Path] = None):
        """
        Initialize the rules loader.
        
        Args:
            additional_folder: Path to additional folder (defaults to config.additional_folder)
        """
        self.additional_folder = additional_folder or config.additional_folder
        self.words: Set[str] = set()
        self.stems: Set[str] = set()
        self._load_rules()
    
    def _extract_stems(self, word: str) -> Set[str]:
        """
        Extract stems from a word by removing common suffixes.
        
        Args:
            word: Word to extract stems from
            
        Returns:
            Set of possible stems (including the original word)
        """
        stems = {word.lower()}  # Always include the full word
        word_lower = word.lower()
        
        # Minimum stem length
        MIN_STEM_LENGTH = 2
        
        # All suffixes to try removing (longest first for better matching)
        all_suffixes = (
            # Russian suffixes
            RUSSIAN_VERB_PATTERNS + 
            RUSSIAN_ADJ_PATTERNS + 
            RUSSIAN_NOUN_PATTERNS +
            # Sakha suffixes
            SAKHA_PLURAL_PATTERNS + 
            SAKHA_POSSESSIVE_PATTERNS
        )
        
        # Sort by length (longest first) to try longer suffixes first
        all_suffixes_sorted = sorted(set(all_suffixes), key=len, reverse=True)
        
        # Try removing each suffix
        for suffix in all_suffixes_sorted:
            if word_lower.endswith(suffix):
                stem = word_lower[:-len(suffix)]
                if len(stem) >= MIN_STEM_LENGTH:
                    stems.add(stem)
        
        return stems
    
    def _load_rules(self) -> None:
        """
        Load words from all .txt files in the additional folder.
        
        Reads each line as a word, ignores empty lines and comments (lines starting with #).
        Extracts stems for each word.
        """
        if not self.additional_folder.exists():
            logger.warning(
                f"Additional folder does not exist: {self.additional_folder}. "
                "Skipping additional rules."
            )
            return
        
        if not self.additional_folder.is_dir():
            logger.warning(
                f"Additional folder path is not a directory: {self.additional_folder}. "
                "Skipping additional rules."
            )
            return
        
        # Find all .txt files
        txt_files = list(self.additional_folder.glob("*.txt"))
        
        if not txt_files:
            logger.debug(f"No .txt files found in additional folder: {self.additional_folder}")
            return
        
        total_words: int = 0
        total_stems: int = 0
        
        for txt_file in txt_files:
            try:
                with open(txt_file, "r", encoding="utf-8") as f:
                    file_words = 0
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        
                        # Skip empty lines and comments
                        if not line or line.startswith("#"):
                            continue
                        
                        # Add word and its stems
                        word_stems = self._extract_stems(line)
                        self.words.add(line.lower())
                        self.stems.update(word_stems)
                        file_words += 1
                        total_stems += len(word_stems)
                    
                    if file_words > 0:
                        logger.debug(f"Loaded {file_words} word(s) from {txt_file.name}")
                    total_words += file_words
                    
            except IOError as e:
                logger.error(f"Error reading file {txt_file.name}: {e}. Skipping file.")
                continue
            except Exception as e:
                logger.error(f"Unexpected error reading file {txt_file.name}: {e}. Skipping file.")
                continue
        
        if total_words > 0:
            logger.info(f"Loaded {total_words} word(s) and {len(self.stems)} unique stem(s) from additional folder")
        else:
            logger.warning(f"No valid words found in additional folder: {self.additional_folder}")
    
    def matches_word_or_stem(self, word: str) -> bool:
        """
        Check if word or its stem matches any word/stem from additional rules.
        
        Args:
            word: Word to check
            
        Returns:
            True if word or its stem matches additional rules (should be removed)
        """
        word_lower = word.lower()
        
        # Check if word itself matches
        if word_lower in self.words:
            return True
        
        # Check if word's stem matches
        word_stems = self._extract_stems(word)
        if word_stems & self.stems:  # Intersection check
            return True
        
        # Check if any stem from additional rules matches the beginning of the word
        # This allows matching "сахалар" when stem is "саха"
        for stem in self.stems:
            if word_lower.startswith(stem) and len(stem) >= 2:
                # If word exactly matches stem, it's a match
                if len(word_lower) == len(stem):
                    return True
                # If word starts with stem, check if remaining part looks like a suffix
                remaining = word_lower[len(stem):]
                # If remaining part is empty or starts with a known suffix pattern, it's likely a match
                # This allows "сахалар" (stem "саха" + suffix "лар")
                if remaining:
                    # Check if remaining part matches any known suffix pattern
                    all_suffixes = SAKHA_PLURAL_PATTERNS + SAKHA_POSSESSIVE_PATTERNS
                    for suffix in all_suffixes:
                        if remaining.startswith(suffix) or remaining == suffix:
                            return True
                    # Also allow if remaining is just a few characters (likely a suffix)
                    # This is a heuristic - might have some false positives but catches most cases
                    if len(remaining) <= 5:  # Most suffixes are short
                        return True
        
        return False


class WordClassifier:
    """
    Classifies words as Russian or Sakha using multi-layer priority rules.
    
    Uses lazy loading for Russian language tools to improve startup performance.
    """
    
    def __init__(self):
        """Initialize the word classifier with lazy-loaded tools."""
        self._morph: Optional[pymorphy2.MorphAnalyzer] = None
        self._segmenter: Optional[Segmenter] = None
        self._morph_vocab: Optional[MorphVocab] = None
        self._names_extractor: Optional[NamesExtractor] = None
        self._additional_rules: Optional[AdditionalRulesLoader] = None
    
    @property
    def morph(self) -> pymorphy2.MorphAnalyzer:
        """Lazy-load pymorphy2 MorphAnalyzer."""
        if self._morph is None:
            self._morph = pymorphy2.MorphAnalyzer()
        return self._morph
    
    @property
    def segmenter(self) -> Segmenter:
        """Lazy-load Natasha Segmenter."""
        if self._segmenter is None:
            self._segmenter = Segmenter()
        return self._segmenter
    
    @property
    def morph_vocab(self) -> MorphVocab:
        """Lazy-load Natasha MorphVocab."""
        if self._morph_vocab is None:
            self._morph_vocab = MorphVocab()
        return self._morph_vocab
    
    @property
    def names_extractor(self) -> NamesExtractor:
        """Lazy-load Natasha NamesExtractor."""
        if self._names_extractor is None:
            self._names_extractor = NamesExtractor(self.morph_vocab)
        return self._names_extractor
    
    @property
    def additional_rules(self) -> AdditionalRulesLoader:
        """Lazy-load additional rules from additional folder."""
        if self._additional_rules is None:
            self._additional_rules = AdditionalRulesLoader()
        return self._additional_rules
    
    @staticmethod
    def has_sakha_anchor_chars(word: str) -> bool:
        """
        Check if word contains Sakha-specific anchor characters.
        
        Args:
            word: Word to check
        
        Returns:
            True if word contains Sakha anchor characters
        """
        return any(char in word for char in SAKHA_ANCHOR_CHARS)
    
    @staticmethod
    def has_sakha_diphthongs(word: str) -> bool:
        """
        Check if word contains Sakha diphthongs.
        
        Args:
            word: Word to check
        
        Returns:
            True if word contains Sakha diphthongs
        """
        return any(diphthong in word for diphthong in SAKHA_DIPHTHONGS)
    
    @staticmethod
    def has_russian_marker_chars(word: str) -> bool:
        """
        Check if word contains Russian marker characters.
        
        Args:
            word: Word to check
        
        Returns:
            True if word contains Russian marker characters
        """
        markers = RUSSIAN_MARKER_CHARS.copy()
        # Remove 'в' if disabled in config
        if not config.use_v_as_russian_marker:
            markers.discard('в')
        return any(char in word for char in markers)
    
    @staticmethod
    def matches_russian_patterns(word: str) -> bool:
        """
        Check if word matches Russian morphological patterns.
        
        Args:
            word: Word to check
        
        Returns:
            True if word matches Russian patterns
        """
        word_lower = word.lower()
        
        # Check verb patterns
        for pattern in RUSSIAN_VERB_PATTERNS:
            if word_lower.endswith(pattern):
                return True
        
        # Check adjective patterns
        for pattern in RUSSIAN_ADJ_PATTERNS:
            if word_lower.endswith(pattern):
                return True
        
        # Check noun patterns
        for pattern in RUSSIAN_NOUN_PATTERNS:
            if word_lower.endswith(pattern):
                return True
        
        return False
    
    @staticmethod
    def matches_sakha_patterns(word: str) -> bool:
        """
        Check if word matches Sakha morphological patterns.
        
        Args:
            word: Word to check
        
        Returns:
            True if word matches Sakha patterns
        """
        word_lower = word.lower()
        
        # Check plural patterns
        for pattern in SAKHA_PLURAL_PATTERNS:
            if word_lower.endswith(pattern):
                return True
        
        # Check possessive patterns
        for pattern in SAKHA_POSSESSIVE_PATTERNS:
            if word_lower.endswith(pattern):
                return True
        
        return False
    
    def is_russian_word(self, word: str) -> bool:
        """
        Check if a word is Russian using multi-layer priority rules.
        
        Priority order:
        1. Sakha anchors (highest - always keep)
        1.5. Additional rules (high - delete if matches words/stems from additional folder)
        2. Russian markers (high - always delete, unless Sakha anchor present)
        3. Morphological patterns (medium - pattern matching)
        4. Language detection and morphology (fallback)
        
        Args:
            word: Word to check
            
        Returns:
            True if word is Russian (should be deleted), False otherwise (keep word)
        """
        word = word.strip()
        
        if not word:
            return False
        
        # LAYER 1: Sakha Anchor Rules (HIGHEST PRIORITY - KEEP)
        # If word contains Sakha-specific characters or diphthongs, keep it
        if self.has_sakha_anchor_chars(word):
            return False  # Keep word (not Russian)
        
        if self.has_sakha_diphthongs(word):
            return False  # Keep word (not Russian)
        
        # LAYER 1.5: Additional Rules (HIGH PRIORITY - DELETE)
        # Check if word matches rules from additional folder
        if self.additional_rules.matches_word_or_stem(word):
            return True  # Delete word (matches additional rules)
        
        # LAYER 2: Russian Marker Rules (HIGH PRIORITY - DELETE)
        # If word contains Russian-specific characters, delete it
        if self.has_russian_marker_chars(word):
            return True  # Delete word (Russian)
        
        # LAYER 3: Morphological Pattern Rules
        # Check Sakha patterns first (if matches, keep)
        if self.matches_sakha_patterns(word):
            return False  # Keep word (Sakha pattern)
        
        # Check Russian patterns (if matches, delete)
        if self.matches_russian_patterns(word):
            return True  # Delete word (Russian pattern)
        
        # LAYER 4: Fallback to Existing Logic
        # Language detection - should distinguish Russian from Sakha
        detected_lang = None
        try:
            detected_lang = detect(word)
            if detected_lang == config.primary_language:
                # Language detection says it's Russian - trust this
                return True
            elif detected_lang and detected_lang != config.primary_language:
                # Language detection says it's NOT Russian (e.g., Sakha) - trust this
                return False
        except Exception:
            pass
        
        # Russian names & surnames
        matches = self.names_extractor(word)
        if matches:
            return True
        
        # Morphological analysis - only trust if language detection was inconclusive
        # pymorphy2 is specifically for Russian morphology, but it might parse Sakha words too
        # So we need to be more strict
        try:
            parses = self.morph.parse(word)
            if parses:
                # Only trust morphological analysis if:
                # - Language detection didn't work (detected_lang is None)
                # - AND we get high-confidence parses (not just any parse)
                for p in parses:
                    if p.tag is not None and str(p.tag) != 'UNKN':
                        # Check if it's a high-confidence parse (normalized form exists)
                        if p.normal_form and p.normal_form != word.lower():
                            # This suggests it's a real Russian word with morphology
                            # But only if language detection didn't say it's NOT Russian
                            if detected_lang is None:
                                return True
        except Exception:
            pass
        
        # Cyrillic check - only as absolute last resort
        # Only use if language detection failed AND morphological analysis suggests Russian
        if _CYRILLIC_RE.search(word) and detected_lang is None:
            try:
                parses = self.morph.parse(word)
                if parses and any(p.tag is not None and str(p.tag) != 'UNKN' for p in parses):
                    # Only if we have a normalized form (suggests real Russian word)
                    if any(p.normal_form and p.normal_form != word.lower() for p in parses):
                        return True
            except Exception:
                pass
        
        return False


# Global instance for convenience (lazy-loaded)
_classifier_instance: Optional[WordClassifier] = None


def get_classifier() -> WordClassifier:
    """
    Get the global WordClassifier instance (singleton pattern).
    
    Returns:
        WordClassifier instance
    """
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = WordClassifier()
    return _classifier_instance

