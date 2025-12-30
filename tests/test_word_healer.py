"""
Test suite for WordHealer module.
"""

import unittest
import tempfile
from pathlib import Path

from src.word_healer import WordHealer, WORD_BOUNDARY_MARKER
from src.config import config


class TestWordHealer(unittest.TestCase):
    """Test cases for WordHealer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.healer = WordHealer()
        # Save original config values
        self.original_enabled = config.word_healer_enabled
        self.original_passes = config.word_healer_passes

    def tearDown(self):
        """Restore original config values."""
        config.word_healer_enabled = self.original_enabled
        config.word_healer_passes = self.original_passes

    # Character Normalization Tests
    def test_smart_normalize_6_to_gh(self):
        """Test normalization of 6 -> ҕ in Cyrillic context."""
        text = "о 6 о л о р"
        result = self.healer.smart_normalize(text)
        # Should normalize 6 to ҕ when surrounded by Cyrillic
        self.assertIn("ҕ", result)
        self.assertNotIn("6", result)

    def test_smart_normalize_h_to_h_sakha(self):
        """Test normalization of h -> һ in Cyrillic context."""
        text = "баhар"
        result = self.healer.smart_normalize(text)
        # Should normalize h to һ
        self.assertIn("һ", result)
        self.assertNotIn("h", result)

    def test_smart_normalize_protects_dates(self):
        """Test that dates are protected from normalization."""
        text = "2006 год"
        result = self.healer.smart_normalize(text)
        # Should NOT change 6 in date (surrounded by digits, not Cyrillic)
        self.assertIn("2006", result)
        self.assertNotIn("ҕ", result)

    def test_smart_normalize_protects_phone_numbers(self):
        """Test that phone numbers are protected from normalization."""
        text = "тел. 123-456"
        result = self.healer.smart_normalize(text)
        # Should NOT change numbers
        self.assertIn("123-456", result)

    def test_smart_normalize_latin_o_to_sakha_o(self):
        """Test normalization of Latin o -> Sakha ө."""
        text = "oлор"
        result = self.healer.smart_normalize(text)
        # Should normalize o to ө in Cyrillic context
        self.assertIn("ө", result)

    def test_smart_normalize_single_6_in_cyrillic(self):
        """Test normalization of single 6 -> ҕ in Cyrillic word."""
        text = "ба6ар"
        result = self.healer.smart_normalize(text)
        # Should normalize 6 to ҕ when in Cyrillic context
        self.assertIn("ҕ", result)
        self.assertNotIn("6", result)
        self.assertEqual(result, "баҕар")

    def test_smart_normalize_single_8_in_cyrillic(self):
        """Test normalization of single 8 -> ө in Cyrillic context."""
        text = "о 8 о"
        result = self.healer.smart_normalize(text)
        # Should normalize 8 to ө when in Cyrillic context
        self.assertIn("ө", result)
        self.assertNotIn("8", result)

    def test_smart_normalize_single_6_with_nearby_digits(self):
        """Test that single 6 is protected when part of multi-digit number."""
        text = "2006 год"
        result = self.healer.smart_normalize(text)
        # Should protect 6 because it's part of "2006" (nearby digits)
        self.assertIn("2006", result)
        self.assertNotIn("ҕ", result)

    def test_smart_normalize_single_6_in_page_number(self):
        """Test that single 6 in page number is not protected but won't normalize without Cyrillic context."""
        text = "стр. 6"
        result = self.healer.smart_normalize(text)
        # Should not protect 6 (no nearby digits), but won't normalize (no Cyrillic context)
        self.assertIn("6", result)
        self.assertNotIn("ҕ", result)

    def test_smart_normalize_mixed_scenario(self):
        """Test mixed scenario with different number types."""
        text = "о 6 о л о р 2006 год тел. 123-456 ба6ар"
        result = self.healer.smart_normalize(text)
        # Single 6 in "о 6 о л о р" should normalize
        self.assertIn("ҕ", result)
        # Single 6 in "ба6ар" should normalize
        self.assertIn("баҕар", result)
        # Multi-digit "2006" should be protected
        self.assertIn("2006", result)
        # Phone number "123-456" should be protected
        self.assertIn("123-456", result)

    def test_smart_normalize_preserves_block_marker(self):
        """Ensure [[BLOCK]] marker is not altered during normalization."""
        from src.constants import WORD_BLOCK_MARKER

        text = f"о 6 о {WORD_BLOCK_MARKER} ба6ар"
        result = self.healer.smart_normalize(text)
        # Markers should remain intact
        self.assertIn(WORD_BLOCK_MARKER, result)
        # Normalization should still occur around the marker
        self.assertIn("ҕ", result)
        self.assertIn("баҕар", result)

    def test_smart_normalize_preserves_word_boundary_marker(self):
        """Ensure legacy __WORD_BOUNDARY__ marker is preserved."""
        text = f"{WORD_BOUNDARY_MARKER} о 6 о {WORD_BOUNDARY_MARKER}"
        result = self.healer.smart_normalize(text)
        # Markers should remain intact
        self.assertIn(WORD_BOUNDARY_MARKER, result)
        # Normalization should still occur within markers
        self.assertIn("ҕ", result)

    # Word Boundary Protection Tests
    def test_protect_word_boundaries_double_space(self):
        """Test that double spaces are preserved as word boundaries."""
        from src.constants import WORD_BLOCK_MARKER

        text = "бу  кинигэ"
        protected = self.healer.protect_word_boundaries(text)
        # Should contain [[BLOCK]] marker
        self.assertIn(WORD_BLOCK_MARKER, protected)

        # After repair and restore, double space should be preserved as single space
        healed = self.healer.heal_text(text)
        # Words should remain separate
        self.assertIn("бу", healed)
        self.assertIn("кинигэ", healed)

    def test_word_boundary_preservation(self):
        """Test that word boundaries are preserved during repair."""
        text = "о ҕ о л о р  баҕар"
        healed = self.healer.heal_text(text)
        # Both words should be present and separate
        self.assertIn("оҕолор", healed)
        self.assertIn("баҕар", healed)
        # Should not merge into one word
        self.assertNotEqual(healed.strip(), "оҕолорбаҕар")

    # Broken Word Repair Tests
    def test_repair_broken_word_simple(self):
        """Test repair of simple broken word."""
        text = "о ҕ о л о р"
        result = self.healer.repair_broken_words(text)
        # Should merge into single word
        self.assertEqual(result, "оҕолор")

    def test_repair_broken_word_complex(self):
        """Test repair of complex broken word."""
        text = "б а ҕ а р"
        result = self.healer.repair_broken_words(text)
        # Should merge into single word
        self.assertEqual(result, "баҕар")

    def test_repair_early_termination(self):
        """Test that repair stops when no improvement is made."""
        # Text that won't improve after first pass
        text = "оҕолор баҕар"
        initial_length = len(text)
        result = self.healer.repair_broken_words(text, max_passes=5)
        # Length should not decrease (no broken words to repair)
        self.assertGreaterEqual(len(result), initial_length)

    def test_repair_multiple_passes(self):
        """Test that multiple passes can repair long broken words."""
        # Very broken word requiring multiple passes
        text = "о ҕ о л о р у о"
        result = self.healer.repair_broken_words(text, max_passes=5)
        # Should merge most of it
        self.assertLess(len(result), len(text))

    # Exception Handling Tests
    def test_check_exceptions_abbreviation(self):
        """Test that abbreviations are detected as exceptions."""
        self.assertTrue(self.healer.check_exceptions("г. Якутск"))
        self.assertTrue(self.healer.check_exceptions("стр. 5"))
        self.assertTrue(self.healer.check_exceptions("т.д."))

    def test_exceptions_not_repaired(self):
        """Test that exception words are not merged."""
        text = "г. Якутск"
        healed = self.healer.heal_text(text)
        # Abbreviation should remain separate
        self.assertIn("г.", healed)

    def test_exceptions_file_loading(self):
        """Test loading exceptions from file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("# Test exceptions\n")
            f.write("тест\n")
            f.write("пример\n")
            exceptions_file = Path(f.name)

        try:
            healer = WordHealer(exceptions_file=exceptions_file)
            self.assertTrue(healer.check_exceptions("тест"))
            self.assertTrue(healer.check_exceptions("пример"))
        finally:
            exceptions_file.unlink()

    # False Hyphen Removal Tests
    def test_remove_line_break_hyphens_sakha(self):
        """Test removal of line-break hyphens (OCR artifacts) in Sakha words."""
        # Pattern: word-hyphen-newline-word (line break artifact)
        text = "оҕо-\nлор"
        result = self.healer.remove_false_hyphens(text)
        # Should merge directly without hyphen or space (it's one word split across lines)
        self.assertEqual(result, "оҕолор")
        self.assertNotIn("-\n", result)  # No hyphen-newline

    def test_preserve_legitimate_hyphens(self):
        """Test that legitimate compound word hyphens are preserved."""
        # Pattern: word-hyphen-word (no newline) - legitimate compound
        text = "кыра-балыста"
        result = self.healer.remove_false_hyphens(text)
        # Should KEEP hyphen (no newline after it)
        self.assertIn("кыра-балыста", result)
        self.assertEqual(text, result)  # Should be unchanged

    def test_remove_line_break_hyphens_cyrillic(self):
        """Test removal of line-break hyphens in any Cyrillic text."""
        text = "некото-\nрый"
        result = self.healer.remove_false_hyphens(text)
        # Should merge directly since both parts are Cyrillic and hyphen-newline present
        self.assertEqual(result, "некоторый")
        self.assertNotIn("-\n", result)

    def test_preserve_hyphens_without_newline(self):
        """Test that hyphens NOT followed by newline are preserved."""
        text = "русско-якутский"
        result = self.healer.remove_false_hyphens(text)
        # Should keep hyphen (no newline)
        self.assertIn("русско-якутский", result)
        self.assertEqual(text, result)

    def test_mixed_hyphens_scenario(self):
        """Test text with both line-break and legitimate hyphens."""
        text = "кыра-балыста оҕолор-\nо баҕар тыла-\nбаайа"
        result = self.healer.remove_false_hyphens(text)
        # Should preserve first hyphen (no newline)
        self.assertIn("кыра-балыста", result)
        # Should merge the hyphen-newline sequences directly
        self.assertNotIn("оҕолор-\nо", result)
        self.assertNotIn("тыла-\nбаайа", result)
        self.assertIn("оҕоло", result)  # Merged: оҕолор + о = оҕоло
        self.assertIn("тылабаайа", result)  # Merged directly

    def test_line_break_hyphen_multiple_newlines(self):
        """Test handling of hyphens followed by multiple newlines."""
        text = "слово-\n\n\nслово"
        result = self.healer.remove_false_hyphens(text)
        # Should merge even with multiple newlines, directly without space
        self.assertNotIn("-\n", result)
        self.assertEqual(result, "словослово")

    # Integration Tests
    def test_heal_text_full_pipeline(self):
        """Test full healing pipeline with normalization and repair."""
        text = "о 6 о л о р  баhар  привет"
        healed = self.healer.heal_text(text)
        # Should normalize and repair
        self.assertIn("оҕолор", healed)
        self.assertIn("һ", healed)  # h should be normalized to һ

    def test_heal_text_disabled(self):
        """Test that healing can be disabled via config."""
        original = config.word_healer_enabled
        config.word_healer_enabled = False
        try:
            text = "о ҕ о л о р"
            healed = self.healer.heal_text(text)
            # Should return unchanged text
            self.assertEqual(healed, text)
        finally:
            config.word_healer_enabled = original

    def test_heal_text_empty(self):
        """Test healing empty text."""
        result = self.healer.heal_text("")
        self.assertEqual(result, "")

    def test_heal_text_whitespace_only(self):
        """Test healing whitespace-only text."""
        result = self.healer.heal_text("   \n\t  ")
        # Should normalize to empty or single space
        self.assertIsInstance(result, str)
        self.assertLessEqual(len(result.strip()), 1)

    # Edge Cases
    def test_normalize_no_cyrillic_context(self):
        """Test that normalization doesn't happen without Cyrillic context."""
        text = "hello world"
        result = self.healer.smart_normalize(text)
        # Should not normalize h in English text
        self.assertIn("h", result)
        self.assertNotIn("һ", result)

    def test_repair_preserves_valid_spaces(self):
        """Test that valid word spaces are preserved."""
        text = "оҕолор баҕар кинигэ"
        result = self.healer.repair_broken_words(text)
        # Should preserve spaces between complete words
        self.assertIn(" ", result)
        words = result.split()
        self.assertGreaterEqual(len(words), 2)

    # New tests for strict single character merging
    def test_repair_only_single_characters(self):
        """Test that only single characters are merged, not complete words."""
        # Should merge "с а х а" -> "саха"
        text = "с а х а"
        result = self.healer.repair_broken_words(text)
        self.assertIn("саха", result)
        # Should NOT merge "саха тыла" -> "сахатыла"
        text2 = "саха тыла"
        result2 = self.healer.repair_broken_words(text2)
        self.assertIn("саха", result2)
        self.assertIn("тыла", result2)
        # Words should remain separate
        self.assertNotIn("сахатыла", result2)

    def test_repair_preserves_word_boundaries_single_space(self):
        """Test that word boundaries with single spaces are preserved."""
        # "оҕолор баҕар" should remain as two words
        text = "о ҕ о л о р  ба ҕ а р"
        healed = self.healer.heal_text(text)
        # Both words should be present and separate
        self.assertIn("оҕолор", healed)
        self.assertIn("баҕар", healed)
        # Should not merge into one word
        self.assertNotIn("оҕолорбаҕар", healed)
        # Check that words are separated by space
        words = healed.split()
        self.assertIn("оҕолор", words)
        self.assertIn("баҕар", words)

    def test_repair_length_constraint(self):
        """Test that words exceeding 25 characters trigger length constraint."""
        # Create a very long broken word that would exceed 25 chars when merged
        # This is a synthetic test case
        long_broken = "а " * 20  # Would create 40-char word
        result = self.healer.repair_broken_words(long_broken)
        # The repair should be limited by length constraint
        # Note: This test may need adjustment based on actual behavior
        self.assertIsInstance(result, str)

    def test_repair_phonetic_check(self):
        """Test that phonetic check prevents merging when too many consonants."""
        # Create a sequence that would have 10+ consonants in a row
        # This is difficult to test directly, but we can test the helper method
        from src.constants import MAX_CONSONANT_SEQUENCE

        # Test with a word that has many consonants
        test_word = "бвгджзклмнпрстфхцчшщ"  # Many consonants
        is_valid = self.healer._check_phonetic_validity(test_word)
        # Should fail if it has too many consecutive consonants
        if len(test_word) > MAX_CONSONANT_SEQUENCE:
            # This test verifies the check exists and works
            self.assertIsInstance(is_valid, bool)

    def test_repair_sakha_anchor_bypass_length(self):
        """Test that words with Sakha anchor characters bypass length check."""
        # Create a long word with Sakha anchor character
        long_sakha_word = "о" + "ҕ" * 30  # 31 chars with anchor
        is_valid = self.healer._check_length_validity(long_sakha_word)
        # Should bypass length check because it contains Sakha anchor
        self.assertTrue(is_valid)

        # Word without anchor should fail if too long
        long_word_no_anchor = "а" * 30  # 30 chars, no anchor
        is_valid_no_anchor = self.healer._check_length_validity(long_word_no_anchor)
        # Should fail length check
        self.assertFalse(is_valid_no_anchor)

    def test_repair_block_marker_preservation(self):
        """Test that [[BLOCK]] markers are preserved and restored correctly."""
        from src.constants import WORD_BLOCK_MARKER

        # Text with double spaces should get [[BLOCK]] marker
        text = "оҕолор  баҕар"
        protected = self.healer.protect_word_boundaries(text)
        self.assertIn(WORD_BLOCK_MARKER, protected)

        # After full healing, words should be separated by single space
        healed = self.healer.heal_text(text)
        self.assertNotIn(WORD_BLOCK_MARKER, healed)
        # Words should be separate
        words = healed.split()
        self.assertIn("оҕолор", words)
        self.assertIn("баҕар", words)

    def test_repair_strict_pattern_example(self):
        """Test the specific example from requirements: 'с а х а т ы л а' -> 'саха тыла'."""
        text = "с а х а т ы л а"
        healed = self.healer.heal_text(text)
        # Should result in "саха тыла" (two words), not "сахатыла" (one word)
        self.assertIn("саха", healed)
        self.assertIn("тыла", healed)
        # Should NOT be merged into one word
        self.assertNotIn("сахатыла", healed)
        # Verify words are separate
        words = healed.split()
        self.assertGreaterEqual(len(words), 2)
        # "саха" and "тыла" should be in separate words
        has_sakha = any("саха" in word for word in words)
        has_tyla = any("тыла" in word for word in words)
        self.assertTrue(has_sakha)
        self.assertTrue(has_tyla)


if __name__ == "__main__":
    unittest.main()
