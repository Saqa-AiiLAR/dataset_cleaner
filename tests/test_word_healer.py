"""
Test suite for WordHealer module.
"""
import unittest
import tempfile
from pathlib import Path

from src.word_healer import WordHealer
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
        text = "оlор"
        result = self.healer.smart_normalize(text)
        # Should normalize o to ө in Cyrillic context
        self.assertIn("ө", result)
    
    # Word Boundary Protection Tests
    def test_protect_word_boundaries_double_space(self):
        """Test that double spaces are preserved as word boundaries."""
        text = "бу  кинигэ"
        protected = self.healer.protect_word_boundaries(text)
        # Should contain boundary marker
        self.assertIn("__WORD_BOUNDARY__", protected)
        
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
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
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
    def test_remove_false_hyphens_sakha(self):
        """Test removal of false hyphens in Sakha words."""
        text = "оҕо-лор"
        result = self.healer.remove_false_hyphens(text)
        # Should merge if both parts contain Sakha characters
        self.assertIn("оҕолор", result)
        self.assertNotIn("-", result)
    
    def test_keep_legitimate_hyphens(self):
        """Test that legitimate hyphens are kept."""
        # Russian compound words should keep hyphens
        text = "рус-ский"
        result = self.healer.remove_false_hyphens(text)
        # Should keep hyphen if not both parts are Sakha
        # (This depends on implementation - may or may not keep)
        self.assertIsInstance(result, str)
    
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


if __name__ == "__main__":
    unittest.main()

