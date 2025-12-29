---
name: Add Word Healer module for OCR broken words repair
overview: Add a word healing module to repair OCR-broken words (like "о ҕ о л о р" -> "оҕолор") before Russian word removal. Also improve PDF text extraction with x_tolerance/y_tolerance parameters.
todos: []
---

# Add Word Healer Module for OCR Broken Words Repair

## Problem

OCR can break words with spaces, turning "оҕолор" into "о ҕ о л о р". Current classification system fails because:

1. Level 1 sees single "ҕ" but doesn't recognize it as part of a word
2. Level 2 and 3 skip single-letter "words"
3. Result: garbage text with single letters instead of clean Sakha words

## Solution

Add a "Word Healer" module that repairs broken words BEFORE Russian word removal.

## Implementation Plan

### Phase 1: Create Word Healer Module

**Create `src/word_healer.py`:**

- Function to detect and repair broken Sakha words
- Merge single letters separated by spaces
- Remove false hyphens (line breaks in OCR)
- Validate repaired words using Sakha character detection
- Multiple pass approach for long broken words

**Key Features:**

- Pattern matching for broken words (single letters with spaces)
- Sakha character validation after merging
- Length-based heuristics (Sakha words are typically longer)
- Configurable number of repair passes

### Phase 2: Improve PDF Extraction

**Update `src/pdf_processor.py`:**

- Add `x_tolerance` and `y_tolerance` parameters to `extract_text()`
- Allow configuration of tolerance values
- These parameters help pdfplumber merge characters that are slightly separated

**Configuration:**

- Add to `src/config.py`: `pdf_x_tolerance`, `pdf_y_tolerance` (default: 3)

### Phase 3: Integrate Word Healer

**Update `src/text_cleaner.py`:**

- Call word healer BEFORE removing Russian words
- Add repair step in `clean_text()` method
- Ensure repaired text is validated

**Update `src/base_processor.py` (optional):**

- Add word healing as a utility method if needed by multiple processors

### Phase 4: Testing

**Create `tests/test_word_healer.py`:**

- Test broken word repair
- Test false hyphen removal
- Test multiple pass repair
- Test edge cases

## Technical Details

### Word Healer Algorithm

1. **Merge by Pattern:**

- Find sequences: `letter - space - letter`
- Merge if contains Sakha characters
- Repeat multiple times for long words

2. **Remove False Hyphens:**

- Pattern: `word - space + newline + word`
- Merge if both parts contain Sakha characters

3. **Validation:**

- Check if merged word contains Sakha anchors
- Check if merged word has reasonable length
- Keep merge if validation passes

### PDF Extraction Improvement

```python
# In pdf_processor.py
page.extract_text(x_tolerance=3, y_tolerance=3)
```



- `x_tolerance`: Horizontal spacing tolerance (default: 3)
- `y_tolerance`: Vertical spacing tolerance (default: 3)
- Higher values = more aggressive merging of separated characters

## Files to Create/Modify

**Create:**

- `src/word_healer.py` - Word repair module

**Modify:**

- `src/pdf_processor.py` - Add tolerance parameters
- `src/text_cleaner.py` - Integrate word healer
- `src/config.py` - Add PDF tolerance settings
- `src/__init__.py` - Export word healer
- `tests/test_word_healer.py` - Add tests

## Expected Behavior

**Before:**

- Input: "о ҕ о л о р баҕар привет"
- Output: "о ҕ о л о р баҕар" (broken word not repaired, Russian removed)

**After:**

- Input: "о ҕ о л о р баҕар привет"
- After healing: "оҕолор баҕар привет"
- After cleaning: "оҕолор баҕар" (both Sakha words preserved)

## Integration Points

1. **In `text_cleaner.py`:** Call healer before `remove_russian_words()`
2. **In `pdf_processor.py`:** Use tolerance parameters during extraction
3. **Optional:** Add as preprocessing step in base processor

## Configuration Options

Add to `config.py`:

- `word_healer_enabled: bool = True`
- `word_healer_passes: int = 5` (number of repair iterations)