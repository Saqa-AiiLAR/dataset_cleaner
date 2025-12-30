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
# Numeric sequences to protect from OCR normalization.
# Intentionally requires at least TWO digits so single-digit OCR errors like "о 6 о"
# can still be normalized (6->ҕ) in Cyrillic context.
_NUMERIC_PROTECT_PATTERN = re.compile(r"(?:\d[\d\s\-./]*\d)")
_LATIN_LETTER_PATTERN = re.compile(r"[A-Za-z]")

# Build Cyrillic pattern once
_cyrillic_chars = "".join(SAKHA_ALL_CHARS)
_CYRILLIC_PATTERN = re.compile(rf"[а-яё{re.escape(_cyrillic_chars)}]", re.IGNORECASE)
# Pattern to match Cyrillic sequences separated by spaces
# Matches: Cyrillic sequence + whitespace + Cyrillic sequence
# The validation function ensures we're merging broken words (not separate words)
_SINGLE_CYRILLIC_CHAR_PATTERN = re.compile(
    rf"^[а-яё{re.escape(_cyrillic_chars)}]$",
    re.IGNORECASE,
)
_CYRILLIC_TOKEN_PATTERN = re.compile(
    rf"^[а-яё{re.escape(_cyrillic_chars)}]+$",
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
        text = text.replace(WORD_BLOCK_MARKER, " ")
        # Replace old __WORD_BOUNDARY__ marker for backward compatibility
        text = text.replace(WORD_BOUNDARY_MARKER, " ")
        # Normalize multiple spaces to single space
        text = _WHITESPACE_PATTERN.sub(" ", text)
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
        # First, identify and protect numeric sequences (dates, phone numbers, IDs, etc.)
        # We protect sequences that contain at least two digits (optionally separated by spaces/punctuation).
        numeric_matches = list(_NUMERIC_PROTECT_PATTERN.finditer(text))

        # Create a set of protected character positions
        protected_positions: Set[int] = set()
        for match in numeric_matches:
            protected_positions.update(range(match.start(), match.end()))

        # Apply normalization for each character in the map
        result_chars = list(text)

        for wrong_char, correct_char in SAKHA_NORMALIZATION_MAP.items():
            # Find all occurrences of wrong_char
            for i, char in enumerate(result_chars):
                if char == wrong_char and i not in protected_positions:
                    # Check if surrounded by Cyrillic letters (with optional spaces)
                    # Look before and after, skipping spaces
                    before_match = False
                    after_match = False

                    # Check before (look back up to 5 chars, skipping spaces)
                    for j in range(max(0, i - 5), i):
                        if j < len(result_chars) and _CYRILLIC_PATTERN.match(result_chars[j]):
                            before_match = True
                            break

                    # Check after (look ahead up to 5 chars, skipping spaces)
                    for j in range(i + 1, min(len(result_chars), i + 6)):
                        if j < len(result_chars) and _CYRILLIC_PATTERN.match(result_chars[j]):
                            after_match = True
                            break

                    # Replace if in Cyrillic context (need at least one Cyrillic letter nearby)
                    if before_match or after_match:
                        result_chars[i] = correct_char
                        logger.debug(
                            f"Normalized '{wrong_char}' -> '{correct_char}' at position {i}"
                        )

        # Extra OCR heuristic:
        # If a Cyrillic 'о/О' appears adjacent to Latin letters, it's very often a mis-OCR of Sakha 'ө/Ө'.
        # Keep this narrow to avoid corrupting normal Cyrillic text.
        for i, char in enumerate(result_chars):
            if char not in {"о", "О"} or i in protected_positions:
                continue

            window_start = max(0, i - 2)
            window_end = min(len(result_chars), i + 3)
            window = "".join(result_chars[window_start:window_end])
            if _LATIN_LETTER_PATTERN.search(window) is None:
                continue

            # Ensure we're still in Cyrillic context (same logic as above).
            before_match = any(
                _CYRILLIC_PATTERN.match(result_chars[j]) for j in range(max(0, i - 5), i)
            )
            after_match = any(
                _CYRILLIC_PATTERN.match(result_chars[j]) for j in range(i + 1, min(len(result_chars), i + 6))
            )
            if before_match or after_match:
                result_chars[i] = "Ө" if char == "О" else "ө"

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

        def _split_long_merged_run_if_needed(merged: str) -> str:
            """
            Heuristic split for long merged single-letter runs.

            Some OCR outputs emit *every* character as a token. Merging those tokens blindly can
            accidentally collapse multiple words into one (e.g., "с а х а т ы л а" -> "сахатыла").

            When a merged candidate is long and has no Sakha anchor characters, try to split it into
            two valid-looking words, preferring balanced splits.
            """
            # Keep short candidates as-is: we don't want to split common words like "кинигэ".
            if len(merged) < 8:
                return merged

            # If there's an anchor character, we assume it's a single Sakha word and keep it whole.
            if any(ch in merged for ch in SAKHA_ANCHOR_CHARS):
                return merged

            # Both parts must contain at least one vowel and pass phonetic/length checks.
            best_split: Optional[tuple[int, str]] = None  # (score, text)
            for split_at in range(2, len(merged) - 1):
                left = merged[:split_at]
                right = merged[split_at:]

                if not any(ch in left for ch in SAKHA_VOWELS) or not any(ch in right for ch in SAKHA_VOWELS):
                    continue

                if not self._check_length_validity(left) or not self._check_length_validity(right):
                    continue
                if not self._check_phonetic_validity(left) or not self._check_phonetic_validity(right):
                    continue

                # Prefer balanced splits (minimize length difference).
                score = -abs(len(left) - len(right))
                candidate = f"{left} {right}"
                if best_split is None or score > best_split[0]:
                    best_split = (score, candidate)

            return best_split[1] if best_split else merged

        def _merge_single_letter_runs(block_text: str) -> str:
            # Split on whitespace; we intentionally normalize intra-block whitespace here.
            # Word boundaries (double spaces) are handled outside via [[BLOCK]] splitting.
            tokens = block_text.split()
            if not tokens:
                return block_text

            merged_tokens: list[str] = []
            i = 0
            while i < len(tokens):
                token = tokens[i]

                if _CYRILLIC_TOKEN_PATTERN.match(token):
                    # Merge a run of Cyrillic-only tokens *only* if it contains at least one
                    # single-character token. This fixes OCR outputs like "ба ҕ а р" while
                    # preserving valid word boundaries like "саха тыла".
                    run_tokens: list[str] = []
                    while i < len(tokens) and _CYRILLIC_TOKEN_PATTERN.match(tokens[i]):
                        run_tokens.append(tokens[i])
                        i += 1

                    if any(_SINGLE_CYRILLIC_CHAR_PATTERN.match(t) for t in run_tokens):
                        merged = "".join(run_tokens)
                        merged_tokens.append(_split_long_merged_run_if_needed(merged))
                    else:
                        merged_tokens.extend(run_tokens)
                    continue

                merged_tokens.append(token)
                i += 1

            return " ".join(merged_tokens)

        for block_idx, block in enumerate(blocks, 1):
            block_text = block
            previous_text = None
            last_pass_num = 0

            for pass_num in range(max_passes):
                last_pass_num = pass_num
                if previous_text is not None and block_text == previous_text:
                    logger.debug(f"Early termination at pass {pass_num + 1} (no change)")
                    break
                previous_text = block_text
                block_text = _merge_single_letter_runs(block_text)

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
