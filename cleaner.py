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

    # 1. Language detection - PRIMARY check (should distinguish Russian from Sakha)
    detected_lang = None
    try:
        detected_lang = detect(word)
        if detected_lang == "ru":
            # Language detection says it's Russian - trust this
            return True
        elif detected_lang and detected_lang != "ru":
            # Language detection says it's NOT Russian (e.g., Sakha) - trust this
            return False
    except:
        pass

    # 2. Russian names & surnames
    matches = names_extractor(word)
    if matches:
        return True

    # 3. Morphological analysis - only trust if language detection was inconclusive
    # pymorphy2 is specifically for Russian morphology, but it might parse Sakha words too
    # So we need to be more strict
    try:
        parses = morph.parse(word)
        if parses:
            # Only trust morphological analysis if:
            # - Language detection didn't work (detected_lang is None)
            # - AND we get high-confidence parses (not just any parse)
            for p in parses:
                if p.tag is not None and str(p.tag) != 'UNKN':
                    # Check if it's a high-confidence parse (normalized form exists)
                    if p.normal_form and p.normal_form != word.lower():
                        # This suggests it's a real Russian word with morphology
                        # But only if language detection didn't say it's NOT Russian
                        if detected_lang is None:
                            return True
    except:
        pass

    # 4. Cyrillic check - only as absolute last resort
    # Only use if language detection failed AND morphological analysis suggests Russian
    if CYRILLIC_RE.search(word) and detected_lang is None:
        try:
            parses = morph.parse(word)
            if parses and any(p.tag is not None and str(p.tag) != 'UNKN' for p in parses):
                # Only if we have a normalized form (suggests real Russian word)
                if any(p.normal_form and p.normal_form != word.lower() for p in parses):
                    return True
        except:
            pass

    return False


def remove_russian_words(text: str) -> str:
    # Extract words that may contain separators (-, –, _, \n)
    # Pattern matches sequences of letters with optional separators between them
    words = regex.findall(r'[\p{L}]+(?:[-–_\n][\p{L}]+)*', text)
    
    total_words = len(words)
    print(f"  Processing {total_words} words...")
    
    russian_words_found = []
    clean_words = []
    
    for i, w in enumerate(words, 1):
        if is_russian_word(w):
            russian_words_found.append(w)
        else:
            # For non-Russian words, replace separators (-, –, _, \n) with spaces
            cleaned_word = w.replace('-', ' ').replace('–', ' ').replace('_', ' ').replace('\n', ' ')
            # Remove extra spaces and add to clean words
            cleaned_word = ' '.join(cleaned_word.split())
            if cleaned_word:  # Only add if word is not empty after cleaning
                clean_words.append(cleaned_word)
        
        # Show progress every 1000 words or at the end
        if i % 1000 == 0 or i == total_words:
            percentage = (i / total_words) * 100
            print(f"  Progress: {i}/{total_words} words ({percentage:.1f}%) processed...")
    
    # Debug: show sample of Russian words found (first 20)
    if russian_words_found:
        sample = russian_words_found[:20]
        print(f"  Debug: Found {len(russian_words_found)} Russian words (showing first 20): {sample}")
        print(f"  Debug: Keeping {len(clean_words)} non-Russian words")
    else:
        print(f"  Debug: No Russian words found, keeping all {len(clean_words)} words")

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
        print("  Step 1: Removing special characters and numbers...")
        text_no_special = remove_special_characters(input_text)
        word_count = len(regex.findall(r'\p{L}+', text_no_special))
        print(f"  ✓ Removed special characters. Found {word_count} words to process.")
        print("  Step 2: Removing Russian words...")
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
