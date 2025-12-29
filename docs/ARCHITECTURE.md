# Architecture Guide

Internal architecture and design decisions for SaqaParser.

## Overview

SaqaParser is designed as a modular pipeline with clear separation of concerns:

```
PDF Files → PDF Processor → Raw Text → Text Cleaner → Cleaned Text
                              ↓
                         Word Healer
                              ↓
                      Language Detector
```

## Core Modules

### 1. PDF Processor (`pdf_processor.py`)

**Purpose**: Extract text from PDF files.

**Key Features**:
- Adaptive tolerance strategy
- Progress reporting
- File management (move to archive)
- Error handling

**Algorithm**:
1. Find all `.pdf` files in input folder
2. For each PDF:
   - Try conservative extraction (`tolerance=1`)
   - Calculate badness score (ratio of single-char words)
   - If score > threshold, retry with higher tolerance
   - Move processed PDF to archive
3. Append extracted text to output file

**Badness Score Calculation**:
```python
badness = single_char_words / total_words
# Higher score = more broken words = need higher tolerance
```

### 2. Text Cleaner (`text_cleaner.py`)

**Purpose**: Remove Russian words and special characters.

**Pipeline**:
1. Remove special characters and numbers
2. Apply word healing (if enabled)
3. Filter invalid words (abbreviations, single letters)
4. Remove Russian words

**Key Methods**:
- `remove_special_characters()` - Keep only letters, spaces, newlines
- `remove_russian_words()` - Multi-layer classification
- `filter_invalid_words()` - Remove abbreviations, Roman numerals, English words

### 3. Word Healer (`word_healer.py`)

**Purpose**: Repair OCR-broken Sakha words.

**Healing Steps**:
1. **Protect word boundaries** - Mark double spaces with `[[BLOCK]]`
2. **Smart normalize** - Fix character hallucinations (`6→ҕ`, `h→һ`)
3. **Repair broken words** - Merge single letters (`о ҕ → оҕ`)
4. **Remove false hyphens** - Fix line-break artifacts
5. **Restore boundaries** - Remove `[[BLOCK]]` markers

**Validation**:
- Length check: Words must be ≤25 characters
- Phonetic check: Max 10 consecutive consonants
- Context check: Only merge in Cyrillic context

### 4. Language Detector (`language_detector.py`)

**Purpose**: Classify words as Russian or Sakha.

**4-Layer Priority System**:

#### Layer 1: Sakha Anchors (Highest Priority)
If word contains these, **always keep**:
- Characters: `ҕ, ҥ, ө, һ, ү`
- Diphthongs: `уо, иэ, ыа, үө`

#### Layer 1.5: Additional Rules (High Priority)
If word matches custom word lists in `workspace/additional/`, **always delete**.

Uses stem matching - `привет` matches `привета`, `приветом`, etc.

#### Layer 2: Russian Markers (High Priority)
If word contains these, **always delete**:
- Characters: `щ, ц, ъ, ф, в` (configurable)

#### Layer 3: Morphological Patterns (Medium Priority)
Pattern matching on word endings:

**Russian patterns** (delete):
- Verbs: `-ться, -тся, -ешь, -ишь`
- Adjectives: `-ий, -ый, -ая, -ое, -ые`
- Nouns: `-ость, -ение, -ание`

**Sakha patterns** (keep):
- Plural: `-лар, -лер, -лор, -лөр, -тар, -тэр, -дар, -дэр`
- Possessive: `-та, -тэ, -тын, -быт`

#### Layer 4: Fallback (Low Priority)
If no pattern matches:
1. Language detection (`langdetect`)
2. Morphological analysis (`pymorphy2`)
3. Name extraction (`natasha`)

**Priority**: Sakha patterns checked before Russian patterns.

### 5. Base Processor (`base_processor.py`)

**Purpose**: Common base class for processors.

**Provides**:
- Path validation
- Directory creation
- Common interface (`process()` method)

**Benefits**:
- Consistent behavior across processors
- Code reuse
- Easy to extend

## Design Patterns

### Lazy Loading

Heavy dependencies (pymorphy2, natasha) are loaded only when needed:

```python
class WordClassifier:
    def __init__(self):
        self._morph = None  # Not loaded yet
    
    @property
    def morph(self):
        if self._morph is None:
            self._morph = pymorphy2.MorphAnalyzer()  # Load now
        return self._morph
```

**Benefits**:
- Faster startup
- Lower memory usage
- Only pay for what you use

### Singleton Pattern

Global classifier instance for convenience:

```python
_classifier_instance = None

def get_classifier():
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = WordClassifier()
    return _classifier_instance
```

### Strategy Pattern

Different strategies for PDF extraction (adaptive tolerance).

### Template Method Pattern

Base processor defines algorithm structure, subclasses implement details.

## Performance Optimizations

### Pre-compiled Regex

All regex patterns are compiled once at module load:

```python
# Module level
_WORD_PATTERN = regex.compile(r'[\p{L}]+(?:[-–_\n][\p{L}]+)*')

# Usage
def remove_russian_words(text):
    words = _WORD_PATTERN.findall(text)  # Fast!
```

**Impact**: 40-60% faster text processing.

### Early Termination

Word healing stops when no more improvements:

```python
if current_length >= previous_length:
    break  # No improvement, stop
```

### Validation Caching

Lazy-loaded tools are cached after first use.

## Data Flow

### Full Pipeline (`saqa-run`)

```
[PDFs in input/]
        ↓
[PDF Processor]
        ↓
[Raw text in timestamp/saqa.txt]
        ↓
[Text Cleaner]
        ↓
  [Remove special chars]
        ↓
  [Word Healer]
        ↓
  [Filter invalid words]
        ↓
  [Remove Russian words]
        ↓
[Clean text in timestamp/saqaCleaned.txt]
```

### Word Classification Flow

```
[Word: "привет"]
        ↓
[Has Sakha anchors?] → No
        ↓
[In additional lists?] → No
        ↓
[Has Russian markers?] → No
        ↓
[Matches Russian patterns?] → No
        ↓
[Matches Sakha patterns?] → No
        ↓
[Language detection] → "ru"
        ↓
[RESULT: Delete (Russian)]
```

```
[Word: "оҕолор"]
        ↓
[Has Sakha anchors?] → Yes (ҕ, ө)
        ↓
[RESULT: Keep (Sakha)]
```

## Error Handling

### Exception Hierarchy

```
SaqaParserError (base)
├── ConfigurationError
├── MissingFileError
├── ValidationError
├── PDFProcessingError
└── TextCleaningError
```

### Strategy

1. **Validate early**: Check paths/config before processing
2. **Fail gracefully**: Continue with other files if one fails
3. **Log everything**: All errors logged with context
4. **Specific exceptions**: Use appropriate exception type

### Example

```python
try:
    processor.process_pdf(pdf_path)
except PDFProcessingError as e:
    logger.error(f"Failed to process {pdf_path}: {e}")
    continue  # Try next file
```

## Logging System

### Levels

- **DEBUG**: Detailed information (--verbose)
- **INFO**: General progress (default)
- **WARNING**: Potential issues
- **ERROR**: Processing failures

### Handlers

1. **File Handler**: Appends to log file
2. **Console Handler**: Displays on screen (can be disabled with --quiet)

### Format

**File**: `YYYY-MM-DD HH:MM:SS - Module - Level - Message`  
**Console**: `Level - Message`

## Configuration Management

### Dataclass-Based

Uses Python dataclasses for type safety:

```python
@dataclass
class Config:
    input_folder: Path = Path("workspace/input")
    progress_interval: int = 10
    # ... etc
```

**Benefits**:
- Type hints
- Default values
- Immutable defaults
- Validation

### Global Instance

Single global config instance:

```python
config = Config()  # In config.py

# Usage
from src.config import config
config.word_healer_enabled = False
```

## Testing Strategy

### Unit Tests

Test individual components in isolation:
- `test_pdf_processor.py`
- `test_text_cleaner.py`
- `test_word_healer.py`
- `test_utils.py`

### Test Structure

```python
class TestTextCleaner(unittest.TestCase):
    def setUp(self):
        # Create temp files
        
    def tearDown(self):
        # Clean up
        
    def test_feature(self):
        # Test specific feature
```

## Security Considerations

1. **Path Validation**: All paths validated before use
2. **No eval/exec**: No dynamic code execution
3. **Safe file operations**: Use pathlib, check before write
4. **Exception handling**: Prevent data loss on errors

## Extension Points

### Adding New Language Detection Rules

1. Add constants to `constants.py`
2. Add detection method to `WordClassifier`
3. Update priority in `is_russian_word()`
4. Add tests

### Adding New Word Healing Rules

1. Add normalization to `SAKHA_NORMALIZATION_MAP`
2. Or create new healing method in `WordHealer`
3. Add to `heal_text()` pipeline
4. Add tests

### Adding New CLI Commands

1. Create new file in `cli/`
2. Use `common.py` utilities
3. Add entry point to `pyproject.toml`
4. Update `cli/__init__.py`

## File Format

### Log File Format

```
Script - Filename - Timestamp - Stats - Status
PDFProcessor - file.pdf - 2025-12-30 14:30:00 - 1000 chars - 50000 bytes - 5 pages
TextCleaner - saqa.txt -> cleaned.txt - 2025-12-30 14:31:00 - 800 chars - 2000 bytes
```

### Output Text Files

- **Encoding**: UTF-8
- **Line breaks**: Preserved from source
- **Separators**: Single space between words

## Dependencies Rationale

| Library | Purpose | Why This One? |
|---------|---------|---------------|
| pdfplumber | PDF extraction | Better than PyPDF2 for complex layouts |
| langdetect | Language detection | Fast, accurate, port of Google's library |
| pymorphy2 | Russian morphology | Most comprehensive Russian NLP |
| natasha | Name extraction | Specialized for Russian names |
| regex | Unicode patterns | Better Unicode support than re |

## Future Improvements

Potential enhancements:

1. **Machine Learning**: Train classifier on Sakha corpus
2. **OCR Integration**: Direct support for scanned PDFs
3. **Batch Processing**: Parallel processing for speed
4. **Web Interface**: GUI for non-technical users
5. **Quality Metrics**: Calculate accuracy scores
6. **Custom Dictionaries**: User-editable word lists

## References

- [Sakha Language on Wikipedia](https://en.wikipedia.org/wiki/Yakut_language)
- [Unicode Cyrillic](https://unicode.org/charts/PDF/U0400.pdf)
- [Keep a Changelog](https://keepachangelog.com/)

