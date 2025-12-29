---
name: Architectural Review and Refactor
overview: Perform a comprehensive architectural review and refactor of the SaqaParser codebase, addressing code organization, naming conventions, error handling, documentation, configuration management, and project structure improvements.
todos:
  - id: fix-exception-naming
    content: Rename FileNotFoundError in exceptions.py to avoid conflict with built-in (e.g., FileNotFound or MissingFileError)
    status: completed
  - id: update-exception-imports
    content: Update all imports and usages of renamed exception across codebase
    status: completed
    dependencies:
      - fix-exception-naming
  - id: reorganize-cli-structure
    content: Create cli/ directory and move entry point scripts (pdf_insert.py -> cli/pdf_extract.py, cleaner.py -> cli/text_clean.py)
    status: completed
  - id: update-entry-points
    content: Update pyproject.toml entry points to reference new CLI module locations
    status: completed
    dependencies:
      - reorganize-cli-structure
  - id: refactor-config
    content: Separate directory creation from config initialization, add validation methods
    status: completed
  - id: consolidate-logging
    content: Create src/logging_config.py to centralize logging setup, update all entry points to use it
    status: completed
  - id: fix-textcleaner-methods
    content: Convert static methods to instance methods in TextCleaner where they use instance state (classifier)
    status: completed
  - id: fix-step-numbering-bug
    content: Fix step numbering in TextCleaner.clean_text() to use dynamic numbering based on word_healer_enabled setting
    status: completed
  - id: add-type-hints
    content: Add missing type hints across all modules, especially return types and class attributes
    status: completed
  - id: improve-error-handling
    content: Standardize error handling patterns, add error context helpers, improve error messages
    status: completed
    dependencies:
      - update-exception-imports
  - id: update-readme
    content: Condense verbose sections, improve structure, add quick start, fix examples
    status: completed
  - id: update-changelog
    content: Add actual release date to CHANGELOG.md, ensure completeness
    status: completed
  - id: improve-gitignore
    content: Add missing patterns, better organization, more comprehensive coverage
    status: completed
  - id: cleanup-dependencies
    content: Clean up requirements.txt, ensure consistency with pyproject.toml, remove redundancy
    status: completed
  - id: add-package-main
    content: Add src/__main__.py for package-level execution support
    status: completed
    dependencies:
      - reorganize-cli-structure
  - id: verify-tests
    content: Run all tests after refactoring to ensure no regressions, update tests for renamed modules
    status: completed
    dependencies:
      - fix-exception-naming
      - reorganize-cli-structure
      - fix-textcleaner-methods
---

# Architectural Review and Refactor Plan

## Overview

This plan addresses architectural issues, code quality improvements, naming inconsistencies, and project structure enhancements across the entire SaqaParser codebase.

## Key Issues Identified

### 1. Naming and Organization

- `pdf_insert.py` has unclear name (should reflect "extraction" not "insertion")
- Entry point scripts in root could be organized into `cli/` or `scripts/` directory
- Exception `FileNotFoundError` conflicts with built-in Python exception

### 2. Configuration Management

- Global mutable config instance could lead to issues
- Config initialization in `__post_init__` creates directories (side effects)
- No validation for config values

### 3. Error Handling

- Inconsistent exception handling patterns
- Some methods catch generic `Exception` without specific handling
- Missing error context in some cases

### 4. Logging

- Logger setup duplicated across entry points
- Log file named "logs" (no extension) could be confusing
- Multiple logger instances could be better managed

### 5. Type Hints and Documentation

- Some methods missing return type hints
- Some docstrings incomplete
- Missing type hints in some function signatures

### 6. Code Quality

- Static methods in `TextCleaner` that use instance state (classifier)
- Some magic numbers/strings that should be constants
- Duplicate path validation logic
- **BUG**: Step numbering in `TextCleaner.clean_text()` skips from Step 1 to Step 3 when word healing is disabled, causing confusing log output

### 7. Project Structure

- Entry points (`pdf_insert.py`, `cleaner.py`) at root level
- No proper CLI module structure
- Missing `__main__.py` for package execution

### 8. Documentation

- README could be more concise in some sections
- Missing API documentation structure
- CHANGELOG needs actual date

### 9. .gitignore

- Generally good but could exclude more IDE-specific files
- Missing explicit ignores for common Python artifacts

### 10. Dependencies

- `requirements.txt` and `pyproject.toml` have some redundancy
- Dev dependencies commented in requirements.txt

## Implementation Plan

### Phase 1: Fix Critical Naming and Exception Issues

**Files to modify:**

- `src/exceptions.py`: Rename `FileNotFoundError` to `FileNotFound` or `FileNotFoundError_` to avoid conflict
- Update all imports and usages of this exception
- `pdf_insert.py`: Consider renaming to `pdf_extract.py` (or move to `cli/`)

**Impact**: High - fixes potential bugs and naming confusion

### Phase 2: Improve Project Structure

**Create new structure:**

- `cli/` directory for command-line entry points
- `cli/__init__.py`
- `cli/pdf_extract.py` (rename from `pdf_insert.py`)
- `cli/text_clean.py` (rename from `cleaner.py`)
- Update `pyproject.toml` entry points to reference new locations
- Add `src/__main__.py` for package-level execution

**Benefits**: Better organization, clearer entry points

### Phase 3: Refactor Configuration Management

**Modify `src/config.py`:**

- Separate configuration from directory creation (move to setup function)
- Add config validation method
- Consider using `dataclasses.field()` with validators
- Add `validate()` method to check config values

**Impact**: Medium - improves maintainability and prevents side effects

### Phase 4: Consolidate Logging Setup

**Create `src/logging_config.py`:**

- Centralize logger setup logic
- Provide factory function for creating loggers
- Handle log file naming consistently (add `.log` extension option)
- Remove duplicate logging setup from entry points

**Update entry points:**

- Use centralized logging setup
- Simplify logger initialization

### Phase 5: Fix Code Quality Issues

**TextCleaner refactoring:**

- Convert static methods to instance methods where appropriate
- Fix `remove_russian_words` and `remove_special_characters` to properly use instance state
- **Fix step numbering bug**: Make step numbers dynamic based on whether word healing is enabled
- When enabled: Step 1 (special chars), Step 2 (healing), Step 3 (Russian removal)
- When disabled: Step 1 (special chars), Step 2 (Russian removal)

**Constants extraction:**

- Move magic numbers to constants
- Extract string literals to constants where appropriate

**Path validation:**

- Consolidate validation logic in `base_processor.py`
- Remove duplicate validation code

### Phase 6: Improve Type Hints and Documentation

**Across all modules:**

- Add missing return type hints
- Add missing parameter type hints
- Improve docstring completeness
- Add type hints for class attributes where missing

**Focus files:**

- `src/pdf_processor.py`
- `src/text_cleaner.py`
- `src/language_detector.py`
- `src/word_healer.py`

### Phase 7: Enhance Error Handling

**Standardize error handling:**

- Create error context helpers in `utils.py`
- Add more specific exception types where needed
- Improve error messages with context
- Add error recovery strategies where appropriate

### Phase 8: Update Documentation

**README.md improvements:**

- Condense overly verbose sections
- Add quick start section
- Improve structure for easier navigation
- Add architecture diagram (text-based or reference)
- Fix any outdated examples

**CHANGELOG.md:**

- Add actual release date (replace placeholder)
- Ensure all features are documented

**Add API documentation:**

- Add docstring examples where helpful
- Ensure all public APIs are documented

### Phase 9: Improve .gitignore

**Add missing patterns:**

- More IDE-specific files (.vscode settings can be more specific)
- Python version files (.python-version)
- Test coverage files more comprehensively
- Build artifacts
- Temporary files

**Organize sections:**

- Better grouping of ignore patterns
- Add comments for clarity

### Phase 10: Dependency Management Cleanup

**requirements.txt:**

- Remove commented dev dependencies (they're in pyproject.toml)
- Add comments explaining relationship to pyproject.toml
- Ensure versions match pyproject.toml

**pyproject.toml:**

- Verify all dependencies are listed
- Ensure version constraints are consistent

## Testing Strategy

After refactoring:

1. Run existing tests to ensure no regressions
2. Add tests for new configuration validation
3. Add tests for renamed modules
4. Verify CLI entry points work correctly

## Migration Notes

- Old entry points (`pdf_insert.py`, `cleaner.py`) should be kept temporarily with deprecation warnings or removed if breaking change is acceptable
- Update any scripts or documentation that reference old entry points
- Ensure entry points in `pyproject.toml` point to new locations

## Risk Assessment

**Low Risk:**

- Documentation updates
- .gitignore improvements
- Type hint additions

**Medium Risk:**

- Configuration refactoring (needs testing)
- Logging consolidation (must verify behavior unchanged)
- Project structure changes (entry point locations)

**High Risk:**

- Exception renaming (affects all imports)
- Static method changes in TextCleaner (affects callers)

## Success Criteria

1. All naming inconsistencies resolved
2. No Python built-in name conflicts
3. Improved code organization with clear entry points
4. Centralized configuration and logging
5. Comprehensive type hints throughout
6. Improved documentation clarity
7. All tests passing
8. No functionality regressions