# Contributing Guide

Thank you for considering contributing to SaqaParser! This guide will help you get started.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Familiarity with Python and NLP concepts

### Development Setup

```bash
# Fork and clone
git clone https://github.com/yourusername/SaqaParser.git
cd SaqaParser

# Install with dev dependencies
pip install -e ".[dev]"

# Set up pre-commit hooks
pre-commit install

# Run setup script
python scripts/setup_workspace.py
```

### Verify Setup

```bash
# Run tests
pytest tests/

# Check code quality
black --check src/ cli/ tests/
ruff check src/ cli/ tests/
mypy src/ cli/
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

Use descriptive branch names:
- `feature/add-kazakh-support`
- `fix/broken-word-repair`
- `docs/improve-readme`

### 2. Make Changes

Follow these guidelines:

#### Code Style

- **Line length**: 100 characters (enforced by black)
- **Formatting**: Use black formatter
- **Imports**: Sorted with isort (included in ruff)
- **Naming**: 
  - Functions/variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
  - Private: `_leading_underscore`

#### Type Hints

Add type hints to all functions:

```python
def process_text(text: str, max_length: int = 100) -> List[str]:
    """Process text and return word list."""
    ...
```

#### Docstrings

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Short description on one line.
    
    Longer description if needed, explaining what the function
    does in more detail.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When param1 is invalid
    """
    ...
```

#### Error Handling

Use custom exceptions:

```python
from src.exceptions import ValidationError

if not path.exists():
    raise ValidationError(f"Path does not exist: {path}")
```

### 3. Add Tests

Every new feature should have tests:

```bash
# Create test file
touch tests/test_your_feature.py

# Write tests
cat > tests/test_your_feature.py << 'EOF'
import unittest
from src.your_module import YourClass

class TestYourFeature(unittest.TestCase):
    def test_basic_functionality(self):
        obj = YourClass()
        result = obj.method()
        self.assertEqual(result, expected)
EOF

# Run tests
pytest tests/test_your_feature.py
```

### 4. Format and Lint

```bash
# Format code with black
black src/ cli/ tests/

# Sort imports and fix linting issues
ruff check --fix src/ cli/ tests/

# Type check
mypy src/ cli/
```

Or use pre-commit (automatic):

```bash
# Pre-commit runs on every commit
git add .
git commit -m "Your message"
# Hooks run automatically
```

### 5. Update Documentation

Update relevant documentation:

- **README.md** - If user-facing features change
- **docs/USAGE.md** - For usage changes
- **docs/ARCHITECTURE.md** - For architectural changes
- **CHANGELOG.md** - Always document changes

### 6. Commit and Push

```bash
# Commit with descriptive message
git add .
git commit -m "feat: Add support for Kazakh language"

# Push to your fork
git push origin feature/your-feature-name
```

#### Commit Message Convention

Use conventional commits:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `style:` - Formatting, no code change
- `refactor:` - Code restructuring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

Examples:
```
feat: Add support for Kazakh language detection
fix: Repair broken word merging in word healer
docs: Update installation guide for Python 3.12
refactor: Extract common CLI utilities
test: Add tests for edge cases in word healing
```

### 7. Create Pull Request

1. Go to GitHub
2. Click "New Pull Request"
3. Select your branch
4. Fill in the template:
   - **Title**: Clear, descriptive
   - **Description**: What changed and why
   - **Testing**: How you tested
   - **Related Issues**: Link any issues

## Code Review Process

### What We Look For

1. **Correctness**: Does it work as intended?
2. **Tests**: Are there adequate tests?
3. **Code Quality**: Is it readable and maintainable?
4. **Documentation**: Is it documented?
5. **Performance**: Any performance concerns?

### Responding to Feedback

- Be responsive and respectful
- Explain your reasoning
- Make requested changes
- Ask questions if unclear

## Testing Guidelines

### Running Tests

```bash
# All tests
pytest tests/

# Specific file
pytest tests/test_text_cleaner.py

# Specific test
pytest tests/test_text_cleaner.py::TestTextCleaner::test_remove_special_characters

# With coverage
pytest tests/ --cov=src --cov-report=html

# View coverage
open htmlcov/index.html
```

### Writing Good Tests

```python
class TestYourFeature(unittest.TestCase):
    def setUp(self):
        """Create test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up after tests."""
        shutil.rmtree(self.temp_dir)
    
    def test_normal_case(self):
        """Test normal usage."""
        result = function(normal_input)
        self.assertEqual(result, expected)
    
    def test_edge_case(self):
        """Test edge cases."""
        result = function(edge_input)
        self.assertEqual(result, expected)
    
    def test_error_handling(self):
        """Test error conditions."""
        with self.assertRaises(CustomError):
            function(invalid_input)
```

### Test Coverage Goals

- **Unit tests**: All public methods
- **Edge cases**: Empty input, invalid input, boundary conditions
- **Error handling**: Exception paths
- **Integration tests**: End-to-end workflows

## Adding New Features

### Process

1. **Discuss first**: Open an issue to discuss the feature
2. **Plan**: Design the feature before coding
3. **Implement**: Write code following guidelines
4. **Test**: Add comprehensive tests
5. **Document**: Update all relevant docs
6. **Review**: Submit PR for review

### Example: Adding New Language Support

1. **Add constants** (`src/constants.py`):
   ```python
   KAZAKH_ANCHOR_CHARS = {'ә', 'ғ', 'қ', 'ң', 'ө', 'ұ', 'ү', 'һ', 'і'}
   ```

2. **Add detection** (`src/language_detector.py`):
   ```python
   def has_kazakh_anchor_chars(self, word: str) -> bool:
       return any(char in word for char in KAZAKH_ANCHOR_CHARS)
   ```

3. **Update classifier**:
   ```python
   if self.has_kazakh_anchor_chars(word):
       return False  # Keep word
   ```

4. **Add tests**:
   ```python
   def test_kazakh_detection(self):
       self.assertFalse(classifier.is_russian_word("қазақ"))
   ```

5. **Document**: Update README and USAGE.md

## Code Review Checklist

Before submitting PR, ensure:

- [ ] Code follows style guidelines (black, ruff pass)
- [ ] Type hints added (mypy passes)
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No debug code or print statements
- [ ] No commented-out code
- [ ] Descriptive variable names
- [ ] Functions are focused (single responsibility)
- [ ] Error handling is appropriate

## Performance Guidelines

### Do's

- Pre-compile regex patterns at module level
- Use lazy loading for heavy dependencies
- Cache expensive computations
- Use generators for large datasets
- Profile before optimizing

### Don'ts

- Don't optimize prematurely
- Don't sacrifice readability for minor speed gains
- Don't load all PDFs into memory at once
- Don't use global state (except singletons)

## Documentation Guidelines

### README.md

- Keep short and focused (~200 lines)
- Quick start guide
- Basic examples
- Link to detailed docs

### docs/ Files

- **INSTALLATION.md**: Complete setup instructions
- **USAGE.md**: All features and configuration
- **ARCHITECTURE.md**: How it works internally
- **CONTRIBUTING.md**: This file

### Docstrings

Every public function/class needs:
- One-line summary
- Detailed description (if needed)
- Args documentation
- Returns documentation
- Raises documentation (if applicable)

### Comments

- Explain "why", not "what"
- Complex algorithms need explanation
- Avoid obvious comments
- Keep comments up-to-date

## Release Process

### Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **Major** (1.0.0 → 2.0.0): Breaking changes
- **Minor** (1.0.0 → 1.1.0): New features (backward compatible)
- **Patch** (1.0.0 → 1.0.1): Bug fixes

### Steps

1. Update `src/__init__.py` version
2. Update `pyproject.toml` version
3. Update `CHANGELOG.md` with changes
4. Create git tag: `git tag v1.0.1`
5. Push: `git push --tags`

## Getting Help

- **Issues**: Open a GitHub issue
- **Discussions**: Use GitHub Discussions
- **Questions**: Ask in issues with "question" label

## Code of Conduct

- Be respectful and inclusive
- Welcome beginners
- Provide constructive feedback
- Focus on the code, not the person

## Recognition

Contributors are recognized in:
- CHANGELOG.md
- GitHub contributors page
- Release notes

Thank you for contributing!

