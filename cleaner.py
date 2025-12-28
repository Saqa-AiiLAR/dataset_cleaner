import re
import regex
from langdetect import detect
import pymorphy2
from natasha import (
    Segmenter,
    MorphVocab,
    NamesExtractor
)
from pathlib import Path
from datetime import datetime

morph = pymorphy2.MorphAnalyzer()
segmenter = Segmenter()
morph_vocab = MorphVocab()
names_extractor = NamesExtractor(morph_vocab)

CYRILLIC_RE = regex.compile(r'\p{IsCyrillic}+')

def is_russian_word(word: str) -> bool:
    word = word.strip()

    if not word:
        return False

    # 1. Cyrillic — immediate execution
    if CYRILLIC_RE.search(word):
        return True

    # 2. Language detection (for transliteration)
    try:
        if detect(word) == "ru":
            return True
    except:
        pass

    # 3. Morphological analysis (Russian roots)
    # pymorphy2 is specifically for Russian morphology
    # If it can parse the word, it's likely Russian
    try:
        parses = morph.parse(word)
        if parses:
            # If pymorphy2 returns valid parses, the word is likely Russian
            # Check that we have actual parse results (not just empty/default)
            for p in parses:
                # Simple check: if tag exists and is not None
                if p.tag is not None:
                    # Additional check: make sure it's not an unknown/unparseable word
                    if str(p.tag) != 'UNKN':
                        return True
    except:
        pass

    # 4. Russian names & surnames
    matches = names_extractor(word)
    if matches:
        return True

    return False


def remove_russian_words(text: str) -> str:
    # Split text into words using whitespace (works better after special chars are removed)
    # This handles both spaces and newlines properly
    words = regex.findall(r'\p{L}+', text)
    
    clean_words = [
        w for w in words if not is_russian_word(w)
    ]

    return " ".join(clean_words)


def remove_special_characters(text: str) -> str:
    """
    Remove all special characters and numbers, keeping only:
    - Letters (Cyrillic and non-Cyrillic)
    - Spaces
    - Line breaks (\n)
    """
    # Pattern to match: Unicode letters, spaces, or newlines
    # \p{L} matches any Unicode letter (includes Cyrillic and Latin)
    # Space character and \n for line breaks
    pattern = regex.compile(r'[\p{L} \n]')
    
    # Find all matching characters (letters, spaces, newlines)
    matches = pattern.findall(text)
    
    # Join the matches back together
    return ''.join(matches)


# Main execution
if __name__ == "__main__":
    # Define paths
    input_file = Path("saqa.txt")
    output_file = Path("saqaCleaned.txt")
    log_file = Path("logs")
    
    try:
        print("Reading saqa.txt...")
        
        # Read input file
        with open(input_file, "r", encoding="utf-8") as f:
            input_text = f.read()
        
        print("Processing text (removing special characters, then Russian words)...")
        
        # Process text: first remove special characters, then remove Russian words
        text_no_special = remove_special_characters(input_text)
        cleaned_text = remove_russian_words(text_no_special)
        
        # Count characters in output
        char_count = len(cleaned_text)
        
        print(f"Writing cleaned text to saqaCleaned.txt...")
        
        # Write output file
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(cleaned_text)
        
        # Get output file size
        file_size = output_file.stat().st_size
        
        print(f"  ✓ Processed and saved cleaned text ({char_count} chars, {file_size} bytes)")
        
        # Write log entry
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"cleaner.py - saqa.txt -> saqaCleaned.txt - {timestamp} - {char_count} chars - {file_size} bytes\n"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
        
        print("\nProcessing complete.")
        
    except FileNotFoundError:
        error_msg = f"Input file {input_file} not found"
        print(f"  ✗ {error_msg}")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"cleaner.py - saqa.txt -> saqaCleaned.txt - {timestamp} - ERROR: {error_msg}\n"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        error_msg = str(e)
        print(f"  ✗ Error: {error_msg}")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"cleaner.py - saqa.txt -> saqaCleaned.txt - {timestamp} - ERROR: {error_msg}\n"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
