"""
Language detection and word classification module.
Handles detection of Russian vs Sakha words using multiple strategies.
"""
from typing import Optional
import regex
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

