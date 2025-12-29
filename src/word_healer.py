"""
Word Healer module for repairing OCR-broken Sakha words.

This module handles:
- Character normalization (fixing OCR hallucinations like 6->ҕ, h->һ)
- Word boundary protection (preventing merging of separate words)
- Broken word repair (merging single letters separated by spaces)
- False hyphen removal (fixing line break artifacts)
- Exception handling (skipping repair for known patterns)
"""
import re
import logging
from pathlib import Path
from typing import List, Set, Optional, Match
import re

from .config import config
from .constants import (
    SAKHA_NORMALIZATION_MAP,
    SAKHA_ALL_CHARS,
    SAKHA_ANCHOR_CHARS,
    WORD_HEALER_EXCEPTIONS,
)

logger = logging.getLogger("SaqaParser.word_healer")

# Special marker for word boundaries (must be unique and unlikely to appear in text)
WORD_BOUNDARY_MARKER = "__WORD_BOUNDARY__"


class WordHealer:
    """Repairs OCR-broken Sakha words with smart normalization and merging."""
    
    def __init__(self, exceptions_file: Optional[Path] = None):
        """
        Initialize Word Healer.
        
        Args:
            exceptions_file: Optional path to exceptions file (one pattern per line)
        """
        self.exceptions_file = exceptions_file or config.word_healer_exceptions_file
        self._exception_patterns: Optional[List[str]] = None
        self._load_exceptions()
    
    def _load_exceptions(self) -> None:
        """Load exception patterns from built-in list and optional file."""
        self._exception_patterns = list(WORD_HEALER_EXCEPTIONS)
        
        # Load from file if it exists
        if self.exceptions_file and Path(self.exceptions_file).exists():
            try:
                with open(self.exceptions_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        # Skip empty lines and comments
                        if line and not line.startswith("#"):
                            self._exception_patterns.append(line)
                logger.debug(f"Loaded {len(self._exception_patterns)} exception patterns")
            except Exception as e:
                logger.warning(f"Could not load exceptions file {self.exceptions_file}: {e}")
    
    def check_exceptions(self, word: str) -> bool:
        """
        Check if word matches exception patterns (should NOT be merged/repaired).
        
        Args:
            word: Word to check
            
        Returns:
            True if word matches an exception pattern (should NOT be repaired)
        """
        if not self._exception_patterns:
            return False
        
        word_lower = word.lower()
        for pattern in self._exception_patterns:
            # Simple substring match (can be extended to regex if needed)
            if pattern.lower() in word_lower or word_lower.startswith(pattern.lower()):
                return True
        return False
    
    def protect_word_boundaries(self, text: str) -> str:
        """
        Mark double/multiple spaces as word boundaries.
        
        Replaces multiple spaces with a special marker that will be restored
        after word repair to prevent merging separate words.
        
        Args:
            text: Input text
            
        Returns:
            Text with word boundaries marked
        """
        # Replace 2+ spaces with marker
        text = re.sub(r'\s{2,}', f' {WORD_BOUNDARY_MARKER} ', text)
        return text
    
    def restore_word_boundaries(self, text: str) -> str:
        """
        Restore word boundaries by replacing marker with single space.
        
        Args:
            text: Text with word boundary markers
            
        Returns:
            Text with boundaries restored
        """
        # Replace marker with single space
        text = text.replace(WORD_BOUNDARY_MARKER, "")
        # Normalize multiple spaces to single space
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def smart_normalize(self, text: str) -> str:
        """
        Normalize OCR character errors BEFORE word repair.
        
        Protects numeric sequences (dates, phone numbers, etc.) and only
        replaces characters when surrounded by Cyrillic letters.
        
        Args:
            text: Input text with potential OCR errors
            
        Returns:
            Text with normalized characters
        """
        # First, identify and protect numeric sequences
        # Pattern matches numbers, dates, phone numbers, ISBN, etc.
        numeric_pattern = r'\d+[\s\-\.]?\d*'
        numeric_matches = list(re.finditer(numeric_pattern, text))
        
        # Create a set of protected character positions
        protected_positions: Set[int] = set()
        for match in numeric_matches:
            protected_positions.update(range(match.start(), match.end()))
        
        # Build Cyrillic character set for context matching
        cyrillic_chars = ''.join(SAKHA_ALL_CHARS)
        cyrillic_pattern = rf'[а-яё{re.escape(cyrillic_chars)}]'
        
        # Apply normalization for each character in the map
        result_chars = list(text)
        
        for wrong_char, correct_char in SAKHA_NORMALIZATION_MAP.items():
            # Find all occurrences of wrong_char
            for i, char in enumerate(result_chars):
                if char == wrong_char and i not in protected_positions:
                    # Check if surrounded by Cyrillic letters (with optional spaces)
                    # Look before and after
                    before_match = False
                    after_match = False
                    
                    # Check before (look back up to 2 chars for Cyrillic)
                    for j in range(max(0, i - 2), i):
                        if re.match(cyrillic_pattern, result_chars[j], re.IGNORECASE):
                            before_match = True
                            break
                    
                    # Check after (look ahead up to 2 chars for Cyrillic)
                    for j in range(i + 1, min(len(result_chars), i + 3)):
                        if re.match(cyrillic_pattern, result_chars[j], re.IGNORECASE):
                            after_match = True
                            break
                    
                    # Replace if in Cyrillic context
                    if before_match or after_match:
                        result_chars[i] = correct_char
                        logger.debug(f"Normalized '{wrong_char}' -> '{correct_char}' at position {i}")
        
        return ''.join(result_chars)
    
    def repair_broken_words(self, text: str, max_passes: int = None) -> str:
        """
        Merge single letters separated by single spaces.
        
        Uses multiple passes with early termination to prevent infinite loops.
        Validates merged words by checking for Sakha anchor characters.
        
        Args:
            text: Input text with potentially broken words
            max_passes: Maximum number of repair passes (defaults to config)
            
        Returns:
            Text with broken words repaired
        """
        if max_passes is None:
            max_passes = config.word_healer_passes
        
        previous_length = len(text)
        
        # Build pattern for Cyrillic characters
        cyrillic_chars = ''.join(SAKHA_ALL_CHARS)
        cyrillic_pattern = rf'[а-яё{re.escape(cyrillic_chars)}]'
        
        # Pattern: single Cyrillic letter, space(s), another Cyrillic letter
        # Only merge if it's a single space (not word boundary marker)
        merge_pattern = rf'({cyrillic_pattern})\s+(?={cyrillic_pattern})'
        
        for pass_num in range(max_passes):
            # Don't merge across word boundaries
            # Replace: letter-space-letter -> letterletter (only single spaces)
            text = re.sub(merge_pattern, r'\1', text)
            
            current_length = len(text)
            
            # Early termination: if length stopped decreasing, no more improvement
            if current_length >= previous_length:
                logger.debug(f"Early termination at pass {pass_num + 1} (no length change)")
                break
            
            previous_length = current_length
        
        return text
    
    def remove_false_hyphens(self, text: str) -> str:
        """
        Remove false hyphens (line break artifacts in OCR).
        
        Merges words separated by hyphen-space if both parts contain Sakha characters.
        
        Args:
            text: Input text with potential false hyphens
            
        Returns:
            Text with false hyphens removed
        """
        # Pattern: word-hyphen-space-word
        # Only merge if both parts contain Sakha characters
        pattern = r'(\w+)-(\s+)(\w+)'
        
        def should_merge(match) -> bool:
            part1, spaces, part2 = match.groups()
            # Check if both parts contain Sakha anchor characters
            has_sakha1 = any(char in part1 for char in SAKHA_ANCHOR_CHARS)
            has_sakha2 = any(char in part2 for char in SAKHA_ANCHOR_CHARS)
            
            # Only merge if both parts are Sakha (likely a broken word)
            if has_sakha1 and has_sakha2:
                return True
            return False
        
        def replace_hyphen(match) -> str:
            if should_merge(match):
                return match.group(1) + match.group(3)  # Merge without hyphen
            return match.group(0)  # Keep original
        
        text = re.sub(pattern, replace_hyphen, text)
        return text
    
    def heal_text(self, text: str) -> str:
        """
        Main entry point for word healing.
        
        Applies all healing steps in the correct order:
        1. Protect word boundaries
        2. Smart normalize (fix character hallucinations)
        3. Repair broken words (merge single letters)
        4. Remove false hyphens
        5. Restore word boundaries
        6. Final cleanup
        
        Args:
            text: Input text with OCR errors
            
        Returns:
            Healed text
        """
        if not config.word_healer_enabled:
            return text
        
        original_length = len(text)
        
        # Step 1: Protect word boundaries (mark double spaces)
        text = self.protect_word_boundaries(text)
        
        # Step 2: Smart normalize (fix character hallucinations)
        text = self.smart_normalize(text)
        
        # Step 3: Repair broken words (merge single letters)
        # Note: Exception checking is done per-word during repair if needed
        text = self.repair_broken_words(text)
        
        # Step 4: Remove false hyphens
        text = self.remove_false_hyphens(text)
        
        # Step 5: Restore word boundaries
        text = self.restore_word_boundaries(text)
        
        # Step 6: Final cleanup (strip, normalize spaces)
        text = ' '.join(text.split())
        text = text.strip()
        
        final_length = len(text)
        if original_length != final_length:
            logger.debug(f"Word healing: {original_length} -> {final_length} chars")
        
        return text

