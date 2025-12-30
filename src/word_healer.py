"""
Word Healer module for repairing OCR-broken Sakha words.

This module handles:
- Character normalization (fixing OCR hallucinations like 6->ҕ, h->һ)
- Word boundary protection (preventing merging of separate words)
- Broken word repair (merging single letters separated by spaces)
- False hyphen removal (fixing line break artifacts)
- Exception handling (skipping repair for known patterns)
"""

from __future__ import annotations

import re
import logging
from pathlib import Path
from typing import List, Set, Optional, Match

from .config import config
from .constants import (
    SAKHA_NORMALIZATION_MAP,
    SAKHA_ALL_CHARS,
    SAKHA_ANCHOR_CHARS,
    WORD_HEALER_EXCEPTIONS,
    WORD_BLOCK_MARKER,
    SAKHA_VOWELS,
    MAX_WORD_LENGTH,
    MAX_CONSONANT_SEQUENCE,
)
from .progress import ProgressBar

logger = logging.getLogger("SaqaParser.word_healer")

# Special marker for word boundaries (must be unique and unlikely to appear in text)
WORD_BOUNDARY_MARKER = "__WORD_BOUNDARY__"

# Pre-compiled regex patterns for performance
_MULTI_SPACE_PATTERN = re.compile(r"\s{2,}")
_WHITESPACE_PATTERN = re.compile(r"\s+")
_NUMERIC_PATTERN = re.compile(r"\d+[\s\-\.]?\d*")

# Build Cyrillic pattern once
_cyrillic_chars = "".join(SAKHA_ALL_CHARS)
_CYRILLIC_PATTERN = re.compile(rf"[а-яё{re.escape(_cyrillic_chars)}]", re.IGNORECASE)
# Pattern to match Cyrillic sequences separated by spaces
# Matches: Cyrillic sequence + whitespace + Cyrillic sequence
# The validation function ensures we're merging broken words (not separate words)
_STRICT_MERGE_PATTERN = re.compile(
    rf"([а-яё{re.escape(_cyrillic_chars)}]+)\s+([а-яё{re.escape(_cyrillic_chars)}]+)",
    re.IGNORECASE,
)
# Pattern for line-break hyphens: word-hyphen-newline(s)-word (OCR artifact)
# Does NOT match word-word (legitimate hyphenated compound words)
_FALSE_HYPHEN_PATTERN = re.compile(r"(\w+)-\n+(\w+)")


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

        Replaces multiple spaces with [[BLOCK]] marker that will be restored
        after word repair to prevent merging separate words.

        Args:
            text: Input text

        Returns:
            Text with word boundaries marked
        """
        # Replace 2+ spaces with [[BLOCK]] marker
        text = _MULTI_SPACE_PATTERN.sub(f" {WORD_BLOCK_MARKER} ", text)
        return text

    def restore_word_boundaries(self, text: str) -> str:
        """
        Restore word boundaries by replacing markers with single space.

        Handles both [[BLOCK]] and __WORD_BOUNDARY__ markers for backward compatibility.

        Args:
            text: Text with word boundary markers

        Returns:
            Text with boundaries restored
        """
        # Replace [[BLOCK]] marker with single space
        text = text.replace(WORD_BLOCK_MARKER, "")
        # Replace old __WORD_BOUNDARY__ marker for backward compatibility
        text = text.replace(WORD_BOUNDARY_MARKER, "")
        # Normalize multiple spaces to single space
        text = _WHITESPACE_PATTERN.sub(" ", text)
        return text

    def _has_nearby_digits(self, position: int, text: str, max_distance: int = 2) -> bool:
        """
        Check for digits near a position (ignoring spaces).

        Args:
            position: Position to check around
            text: Text to analyze
            max_distance: Maximum distance to search (default 2)

        Returns:
            True if nearby digits are found
        """
        # Check before position (up to max_distance chars, ignoring spaces)
        chars_checked = 0
        for j in range(position - 1, -1, -1):
            if j < 0 or j >= len(text):
                break
            char = text[j]
            if char.isspace():
                continue  # Skip spaces
            if char.isdigit():
                return True
            chars_checked += 1
            if chars_checked >= max_distance:
                break

        # Check after position (up to max_distance chars, ignoring spaces)
        chars_checked = 0
        for j in range(position + 1, len(text)):
            char = text[j]
            if char.isspace():
                continue  # Skip spaces
            if char.isdigit():
                return True
            chars_checked += 1
            if chars_checked >= max_distance:
                break

        return False

    def _classify_numeric_match(self, match: Match[str], text: str) -> bool:
        """
        Determine if a numeric match should be protected.

        Args:
            match: Regex match object for numeric sequence
            text: Full text containing the match

        Returns:
            True if should protect, False if not
        """
        matched_text = match.group(0)
        start_pos = match.start()
        end_pos = match.end()

        # Count digits in the match
        digit_count = sum(1 for char in matched_text if char.isdigit())

        # Category A: Multi-digit numbers (2+ digits) -> protect
        if digit_count >= 2:
            return True

        # Category A: Numbers with separators -> protect
        if any(sep in matched_text for sep in ["-", ".", "/", " "]):
            return True

        # Single digit case
        if digit_count == 1:
            # Find the digit character in the match (pattern always starts with digits)
            digit_char = None
            for char in matched_text:
                if char.isdigit():
                    digit_char = char
                    break
            
            if digit_char is None:
                # Should not happen, but protect for safety
                return True

            # For single "6" or "8", check if part of numeric context
            if digit_char in ("6", "8"):
                # Check for nearby digits (within 2 chars, ignoring spaces)
                if self._has_nearby_digits(start_pos, text, max_distance=2):
                    # Has nearby digits -> part of number -> protect
                    return True
                # No nearby digits -> allow normalization (don't protect)
                return False

            # Other single digits -> protect for safety
            return True

        # Default: protect (should not reach here)
        return True

    def smart_normalize(self, text: str) -> str:
        """
        Normalize OCR character errors BEFORE word repair.

        Protects numeric sequences (dates, phone numbers, etc.) and only
        replaces characters when surrounded by Cyrillic letters.

        Single "6" and "8" digits are not protected if they are not part of
        a numeric context, allowing normalization in Cyrillic text.

        Args:
            text: Input text with potential OCR errors

        Returns:
            Text with normalized characters
        """
        # First, identify all numeric sequences
        # Pattern matches numbers, dates, phone numbers, ISBN, etc.
        numeric_matches = list(_NUMERIC_PATTERN.finditer(text))

        # Create a set of protected character positions
        # Only protect matches that are classified as "should protect"
        protected_positions: Set[int] = set()
        for match in numeric_matches:
            if self._classify_numeric_match(match, text):
                # Add all positions from this match to protected set
                protected_positions.update(range(match.start(), match.end()))

        # Apply normalization for each character in the map
        result_chars = list(text)

        for wrong_char, correct_char in SAKHA_NORMALIZATION_MAP.items():
            # Find all occurrences of wrong_char
            for i, char in enumerate(result_chars):
                if char == wrong_char and i not in protected_positions:
                    # Check if surrounded by Cyrillic letters (with optional spaces)
                    # Look before and after, skipping spaces and stopping at punctuation
                    before_match = False
                    after_match = False

                    # Check before (look back up to 5 chars, skipping spaces)
                    # Stop if we hit punctuation (.,;:!?) - not a valid context
                    chars_checked = 0
                    for j in range(i - 1, -1, -1):
                        if j < 0 or j >= len(result_chars):
                            break
                        check_char = result_chars[j]
                        # Stop at punctuation (not a valid context for normalization)
                        if check_char in ".,;:!?":
                            break
                        if check_char.isspace():
                            continue  # Skip spaces
                        if _CYRILLIC_PATTERN.match(check_char):
                            before_match = True
                            break
                        chars_checked += 1
                        if chars_checked >= 5:
                            break

                    # Check after (look ahead up to 5 chars, skipping spaces)
                    # Stop if we hit punctuation (.,;:!?) - not a valid context
                    chars_checked = 0
                    for j in range(i + 1, len(result_chars)):
                        check_char = result_chars[j]
                        # Stop at punctuation (not a valid context for normalization)
                        if check_char in ".,;:!?":
                            break
                        if check_char.isspace():
                            continue  # Skip spaces
                        if _CYRILLIC_PATTERN.match(check_char):
                            after_match = True
                            break
                        chars_checked += 1
                        if chars_checked >= 5:
                            break

                    # Replace if in Cyrillic context (need at least one Cyrillic letter nearby)
                    if before_match or after_match:
                        result_chars[i] = correct_char
                        logger.debug(
                            f"Normalized '{wrong_char}' -> '{correct_char}' at position {i}"
                        )

        return "".join(result_chars)

    def _is_vowel(self, char: str) -> bool:
        """
        Check if a character is a vowel.

        Args:
            char: Character to check

        Returns:
            True if character is a vowel
        """
        return char in SAKHA_VOWELS

    def _count_consonants_in_sequence(self, text: str, start_pos: int) -> int:
        """
        Count consecutive consonants starting from a position.

        Args:
            text: Text to analyze
            start_pos: Starting position

        Returns:
            Number of consecutive consonants
        """
        count = 0

        for i in range(start_pos, len(text)):
            char = text[i]
            # Only count Cyrillic letters (not spaces, punctuation, etc.)
            if _CYRILLIC_PATTERN.match(char):
                if not self._is_vowel(char):
                    count += 1
                else:
                    break  # Stop at first vowel
            else:
                # Non-letter character - stop counting
                break

        return count

    def _check_phonetic_validity(self, word: str) -> bool:
        """
        Check if word has valid phonetics (not too many consecutive consonants).

        Args:
            word: Word to check

        Returns:
            True if word has valid phonetics (no 10+ consecutive consonants)
        """
        for i in range(len(word)):
            consonant_count = self._count_consonants_in_sequence(word, i)
            if consonant_count >= MAX_CONSONANT_SEQUENCE:
                logger.debug(
                    f"Phonetic check failed: {consonant_count} consecutive consonants in '{word}'"
                )
                return False
        return True

    def _check_length_validity(self, word: str) -> bool:
        """
        Check if word length is within limits.

        Bypasses check if word contains Sakha anchor characters.

        Args:
            word: Word to check

        Returns:
            True if word length is valid (<= 25) or contains Sakha anchor characters
        """
        # Bypass length check if word contains Sakha anchor characters
        if any(char in word for char in SAKHA_ANCHOR_CHARS):
            return True

        if len(word) > MAX_WORD_LENGTH:
            logger.debug(f"Length check failed: word '{word}' exceeds {MAX_WORD_LENGTH} characters")
            return False

        return True

    def repair_broken_words(self, text: str, max_passes: Optional[int] = None) -> str:
        """
        Merge single letters separated by single spaces using strict word boundaries.

        Only merges standalone single characters (not complete words).
        Validates merged words with length and phonetic checks.
        Processes text in blocks separated by [[BLOCK]] markers.

        Args:
            text: Input text with potentially broken words
            max_passes: Maximum number of repair passes (defaults to config)

        Returns:
            Text with broken words repaired
        """
        if max_passes is None:
            max_passes = config.word_healer_passes

        # Split text into blocks by [[BLOCK]] marker
        blocks = text.split(WORD_BLOCK_MARKER)
        processed_blocks = []

        total_blocks = len(blocks)
        progress = ProgressBar(total=total_blocks, desc="Healing words")

        for block_idx, block in enumerate(blocks, 1):
            block_text = block
            previous_length = len(block_text)
            last_pass_num = 0

            for pass_num in range(max_passes):
                last_pass_num = pass_num

                def create_merge_function(current_block_text: str):
                    """Create a merge function that captures block_text explicitly."""
                    def merge_with_validation(match: Match[str]) -> str:
                        """Merge single characters with validation."""
                        char1 = match.group(1)
                        char2 = match.group(2)

                        # Get the position in the current block_text
                        match_start = match.start()
                        match_end = match.end()

                        # Check if we're merging separate words (should not merge)
                        # Look backwards: if there's a non-space char immediately before seq1, it's part of a longer word
                        if match_start > 0:
                            prev_char = current_block_text[match_start - 1]
                            if not prev_char.isspace() and _CYRILLIC_PATTERN.match(prev_char):
                                # seq1 is part of a longer word (not separated by space), don't merge
                                return match.group(0)

                        # Look forwards: if there's a non-space char immediately after seq2, it's part of a longer word
                        if match_end < len(current_block_text):
                            next_char = current_block_text[match_end]
                            if not next_char.isspace() and _CYRILLIC_PATTERN.match(next_char):
                                # seq2 is part of a longer word (not separated by space), don't merge
                                return match.group(0)
                        
                        # Check if there are multiple spaces between the sequences (word boundary)
                        # This prevents merging separate words like "саха тыла"
                        match_text = current_block_text[match_start:match_end]
                        if "  " in match_text or "\n" in match_text:
                            # Multiple spaces or newline indicates word boundary, don't merge
                            return match.group(0)

                        # Find word boundaries: look for the full word that would contain this merge
                        # Look backwards for word start (stop at space or non-Cyrillic)
                        word_start = match_start
                        for i in range(match_start - 1, -1, -1):
                            if i < len(current_block_text):
                                char = current_block_text[i]
                                if char.isspace():
                                    break  # Stop at space (word boundary)
                                if _CYRILLIC_PATTERN.match(char):
                                    word_start = i
                                else:
                                    break  # Stop at non-Cyrillic

                        # Look forwards for word end (stop at space or non-Cyrillic)
                        word_end = match_end
                        for i in range(match_end, len(current_block_text)):
                            if i < len(current_block_text):
                                char = current_block_text[i]
                                if char.isspace():
                                    break  # Stop at space (word boundary)
                                if _CYRILLIC_PATTERN.match(char):
                                    word_end = i + 1
                                else:
                                    break  # Stop at non-Cyrillic

                        # Simulate the merge: replace the matched pattern with merged chars
                        # The match consumed: char1 + spaces + char2
                        # We want to replace it with: char1 + char2 (no spaces)
                        merged_chars = char1 + char2
                        # Build the potential word with the merge applied
                        potential_word_with_spaces = (
                            current_block_text[word_start:match_start]
                            + merged_chars
                            + current_block_text[match_end:word_end]
                        )

                        # Remove all spaces to get the clean word for validation
                        potential_word_clean = re.sub(r"\s+", "", potential_word_with_spaces)

                        # Skip validation if word is empty or too short
                        if len(potential_word_clean) <= 1:
                            return merged_chars

                        # Check validity
                        if not self._check_length_validity(potential_word_clean):
                            logger.debug(f"Rollback: length check failed for '{potential_word_clean}'")
                            return match.group(0)  # Don't merge - return original

                        if not self._check_phonetic_validity(potential_word_clean):
                            logger.debug(
                                f"Rollback: phonetic check failed for '{potential_word_clean}'"
                            )
                            return match.group(0)  # Don't merge - return original

                        # Merge is valid - return merged chars (char2 was consumed by pattern, so no duplication)
                        return merged_chars

                    return merge_with_validation

                # Apply strict merge pattern with validation
                block_text = _STRICT_MERGE_PATTERN.sub(
                    create_merge_function(block_text), block_text
                )

                current_length = len(block_text)

                # Early termination: if length stopped decreasing, no more improvement
                if current_length >= previous_length:
                    logger.debug(f"Early termination at pass {pass_num + 1} (no length change)")
                    break

                previous_length = current_length

            processed_blocks.append(block_text)

            # Update progress after each block
            progress.update(block_idx, suffix=f"Pass {last_pass_num + 1}/{max_passes}")

        # Finish progress bar
        progress.finish()

        # Join blocks back together with [[BLOCK]] marker
        return WORD_BLOCK_MARKER.join(processed_blocks)

    def remove_false_hyphens(self, text: str) -> str:
        """
        Remove false hyphens (line break artifacts in OCR).

        Merges words separated by hyphen-newline(s) if both parts contain Cyrillic characters.
        Preserves legitimate hyphenated compound words (word-word without newline).

        Args:
            text: Input text with potential false hyphens

        Returns:
            Text with false hyphens removed, legitimate hyphens preserved
        """
        # Pattern: word-hyphen-newline(s)-word (line break artifact)
        # Only merge if both parts contain Sakha/Cyrillic characters

        def should_merge(match) -> bool:
            part1, part2 = match.groups()
            # Check if both parts contain Cyrillic characters (broader than just Sakha anchors)
            has_cyrillic1 = _CYRILLIC_PATTERN.search(part1) is not None
            has_cyrillic2 = _CYRILLIC_PATTERN.search(part2) is not None

            # Only merge if both parts contain Cyrillic (likely a broken Sakha word)
            return bool(has_cyrillic1 and has_cyrillic2)

        def replace_hyphen(match: Match[str]) -> str:
            if should_merge(match):
                # Merge directly without hyphen or space (it's one word split across lines)
                return match.group(1) + match.group(2)
            return match.group(0)  # Keep original

        text = _FALSE_HYPHEN_PATTERN.sub(replace_hyphen, text)
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
        text = " ".join(text.split())
        text = text.strip()

        final_length = len(text)
        if original_length != final_length:
            logger.debug(f"Word healing: {original_length} -> {final_length} chars")

        return text
