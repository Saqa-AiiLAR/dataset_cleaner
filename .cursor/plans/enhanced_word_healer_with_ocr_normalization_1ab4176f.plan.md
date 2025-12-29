---
name: Enhanced Word Healer with OCR normalization
overview: "Add a comprehensive Word Healer module that repairs OCR-broken words with smart character normalization, word boundary protection, adaptive PDF extraction, and exception handling. Addresses critical issues: character hallucinations (6->ҕ, h->һ), word merging safety, and layout-aware PDF processing."
todos: []
---

# Enhanced

Word Healer Module with OCR Normalization

## Problem Analysis

OCR breaks Sakha words with spaces ("оҕолор" -> "о ҕ о л о р"), causing classification failures. Additionally, OCR introduces character hallucinations (6->ҕ, h->һ, o->ө) that prevent word recognition.

## Critical Issues Addressed

1. **Character Hallucinations**: OCR confuses similar characters (ө->о, һ->h, ҕ->6)
2. **Word Boundary Safety**: Aggressive merging could combine separate short Sakha words
3. **PDF Layout Sensitivity**: High tolerance values can merge text from different columns
4. **Infinite Loop Prevention**: Multiple passes need early termination checks

## Implementation Plan

### Phase 1: Add Normalization Map to Constants

**Update `src/constants.py`:**

- Add `SAKHA_NORMALIZATION_MAP`: Dictionary mapping OCR errors to correct Sakha characters
- `'6' -> 'ҕ'`, `'б' -> 'ҕ'` (common confusion)
- `'h' -> 'һ'`, `'H' -> 'Һ'` (Latin h -> Sakha һ)
- `'o' -> 'ө'`, `'O' -> 'Ө'` (Latin o -> Sakha ө)
- `'y' -> 'ү'`, `'Y' -> 'Ү'` (Latin y -> Sakha ү)
- `'8' -> 'ө'` (sometimes 8 resembles ө)
- `'н' -> 'ҥ'` (context-dependent, handled separately)
- Add `SAKHA_ALL_CHARS`: Set of all Sakha-specific characters for pattern matching
- Union of `SAKHA_ANCHOR_CHARS` plus uppercase variants
- Add `WORD_HEALER_EXCEPTIONS`: Built-in list of words/patterns that should NOT be merged
- Abbreviations: `'г.', 'стр.', 'т.д.', 'и т.д.'`
- Common short words that might be adjacent: `'бу', 'уо', 'ити'` (only if context suggests separation)

### Phase 2: Create Word Healer Module

**Create `src/word_healer.py`:Class: `WordHealer`Methods:**

1. **`smart_normalize(text: str) -> str`**

- Normalize OCR character errors BEFORE word repair
- Protect numeric sequences (dates, phone numbers, page numbers, ISBN)
- Only replace characters when surrounded by Cyrillic letters
- Pattern: `(Cyrillic)(space?)(wrong_char)(space?)(Cyrillic)` -> replace wrong_char
- Use regex to detect numeric contexts and skip normalization in those areas

2. **`protect_word_boundaries(text: str) -> str`**

- Mark double/multiple spaces as word boundaries
- Replace multiple spaces with a special marker (e.g., `__WORD_BOUNDARY__`)
- Restore after word repair

3. **`repair_broken_words(text: str, max_passes: int = 5) -> str`**

- Merge single letters separated by single spaces
- Pattern: `([Cyrillic])\s+(?=[Cyrillic])` -> merge if context suggests Sakha word
- Early termination: Check if text length stops decreasing (prevent infinite loops)
- Validate merged words: Check if result contains Sakha anchor characters
- Multiple passes with decreasing aggressiveness

4. **`remove_false_hyphens(text: str) -> str`**

- Pattern: `(\w)-\s+(\w)` -> merge if both parts contain Sakha characters
- Only merge if hyphen appears to be a line break artifact

5. **`check_exceptions(word: str) -> bool`**

- Check if word matches exception patterns (built-in + file-based)
- Load exceptions from `exceptions.txt` if file exists (optional)
- Return True if word should NOT be merged/repaired

6. **`heal_text(text: str) -> str`** (main entry point)

- Order of operations:

    1. Protect word boundaries (mark double spaces)
    1. Smart normalize (fix character hallucinations)
    1. Check exceptions (skip repair for known exceptions)
    1. Repair broken words (merge single letters)
    1. Remove false hyphens
    2. Restore word boundaries
    1. Final cleanup (strip, normalize spaces)

**Configuration Integration:**

- Use `config.word_healer_enabled` to enable/disable
- Use `config.word_healer_passes` for max repair iterations
- Use `config.word_healer_exceptions_file` for optional exceptions file path

### Phase 3: Improve PDF Extraction with Adaptive Tolerance

**Update `src/pdf_processor.py`:Modify `extract_text_from_pdf()` method:**

- Add `layout=True` parameter to `extract_text()` for better layout detection
- Implement adaptive tolerance strategy:

1. First attempt: Extract with `x_tolerance=1, y_tolerance=1` (conservative)
2. Calculate "badness score": Ratio of single-character "words" to total words
3. If badness score > threshold (e.g., 0.3), retry with higher tolerance
4. Progressive tolerance: Try `x_tolerance=3, y_tolerance=3`, then `5, 5` if needed
5. Log which tolerance level was used for each page

**Add to `src/config.py`:**

- `pdf_x_tolerance: int = 3` (default horizontal tolerance)
- `pdf_y_tolerance: int = 3` (default vertical tolerance)
- `pdf_adaptive_tolerance: bool = True` (enable adaptive strategy)
- `pdf_badness_threshold: float = 0.3` (threshold for retry with higher tolerance)
- `pdf_layout_mode: bool = True` (use layout-aware extraction)

### Phase 4: Integrate Word Healer into Text Cleaner

**Update `src/text_cleaner.py`:Modify `clean_text()` method:**

- Add word healing step BEFORE Russian word removal
- Order: `remove_special_characters` -> `heal_text` -> `remove_russian_words`
- Ensure proper text normalization after healing (strip, normalize spaces)

**Integration:**

```python
# In clean_text() method:
text_no_special = self.remove_special_characters(input_text)

# NEW: Word healing step
if config.word_healer_enabled:
    from .word_healer import WordHealer
    healer = WordHealer()
    text_no_special = healer.heal_text(text_no_special)
    logger.info("Applied word healing to repair OCR-broken words")

cleaned_text = self.remove_russian_words(text_no_special)
```



### Phase 5: Add Exception Dictionary Support

**Create optional `exceptions.txt` file format:**

- One word/pattern per line
- Support regex patterns (optional, marked with prefix)
- Comments with `#`

**Example:**

```javascript
# Abbreviations that should not be merged
г.
стр.
т.д.
и т.д.

# Short words (context-dependent)
бу
уо
```

**Update `WordHealer.check_exceptions()`:**

- Load from file if `config.word_healer_exceptions_file` exists
- Cache loaded exceptions
- Match against word and context

### Phase 6: Testing

**Create `tests/test_word_healer.py`:Test Cases:**

1. **Character Normalization:**

- `"о 6 о л о р"` -> `"о ҕ о л о р"` (6 -> ҕ)
- `"баhар"` -> `"баһар"` (h -> һ)
- `"2006 год"` -> `"2006 год"` (6 in date NOT changed)
- `"тел. 123-456"` -> `"тел. 123-456"` (numbers protected)

2. **Word Boundary Protection:**

- `"бу  кинигэ"` -> `"бу кинигэ"` (double space preserved)
- `"о ҕ о л о р  баҕар"` -> `"оҕолор баҕар"` (single spaces merged, double preserved)

3. **Broken Word Repair:**

- `"о ҕ о л о р"` -> `"оҕолор"`
- `"б а ҕ а р"` -> `"баҕар"`
- Early termination test (length stops decreasing)

4. **Exception Handling:**

- `"г. Якутск"` -> `"г. Якутск"` (not merged)
- `"стр. 5"` -> `"стр. 5"` (not merged)

5. **False Hyphen Removal:**

- `"оҕо-лор"` -> `"оҕолор"` (if both parts Sakha)
- `"рус-ский"` -> `"рус-ский"` (keep if Russian compound)

6. **Integration Test:**

- Full pipeline: `"о 6 о л о р  привет"` -> normalize -> repair -> remove Russian -> `"оҕолор"`

### Phase 7: Update Configuration

**Update `src/config.py`:**Add new configuration options:

```python
# Word healer settings
word_healer_enabled: bool = True
word_healer_passes: int = 5
word_healer_exceptions_file: Optional[Path] = None

# PDF extraction settings
pdf_x_tolerance: int = 3
pdf_y_tolerance: int = 3
pdf_adaptive_tolerance: bool = True
pdf_badness_threshold: float = 0.3
pdf_layout_mode: bool = True
```



### Phase 8: Documentation and Export

**Update `src/__init__.py`:**

- Export `WordHealer` class
- Export `SAKHA_NORMALIZATION_MAP` from constants

**Update `README.md`:**

- Add "Word Healer" section explaining OCR repair
- Document normalization map
- Explain adaptive PDF extraction
- Document exception dictionary format

## Technical Implementation Details

### Normalization Regex Pattern

```python
# Pattern to protect numeric sequences
NUMERIC_PROTECTION = r'\d+[\s\-\.]?\d*'  # Matches numbers, dates, phone numbers

# Pattern for character replacement (only in Cyrillic context)
CYRILLIC_CONTEXT = rf"([а-яё{SAKHA_ALL_CHARS}])\s*{wrong_char}\s*([а-яё{SAKHA_ALL_CHARS}])"
```



### Badness Score Calculation

```python
def calculate_badness_score(text: str) -> float:
    words = text.split()
    single_char_words = sum(1 for w in words if len(w) == 1)
    return single_char_words / len(words) if words else 0.0
```



### Early Termination Check

```python
previous_length = len(text)
for pass_num in range(max_passes):
    text = repair_pass(text)
    current_length = len(text)
    if current_length >= previous_length:  # No improvement
        break
    previous_length = current_length
```



## Files to Create/Modify

**Create:**

- `src/word_healer.py` - Main word healer module
- `tests/test_word_healer.py` - Test suite
- `exceptions.txt` (optional, user-created) - Exception dictionary

**Modify:**

- `src/constants.py` - Add normalization map and exceptions
- `src/pdf_processor.py` - Add adaptive tolerance extraction
- `src/text_cleaner.py` - Integrate word healer
- `src/config.py` - Add word healer and PDF settings
- `src/__init__.py` - Export word healer
- `README.md` - Document new features

## Expected Behavior

**Before:**

- Input: `"о 6 о л о р  баhар  привет"`
- Output: `"о 6 о л о р  баhар"` (broken, unrecognized)

**After:**

- Step 1 (Normalize): `"о ҕ о л о р  баһар  привет"`
- Step 2 (Repair): `"оҕолор  баһар  привет"`
- Step 3 (Remove Russian): `"оҕолор баһар"` (both Sakha words preserved)

## Integration Points

1. **In `text_cleaner.py`**: Call `heal_text()` after `remove_special_characters()` and before `remove_russian_words()`