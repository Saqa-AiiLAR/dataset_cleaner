"""
Entry point for text cleaning.
Removes Russian words and special characters from saqa.txt and saves to saqaCleaned.txt.
"""
from src.text_cleaner import TextCleaner
from src.utils import setup_logging
from src.config import config

if __name__ == "__main__":
    # Set up logging
    logger = setup_logging(config.log_file)
    
    try:
        # Create cleaner and process text
        cleaner = TextCleaner()
        char_count = cleaner.clean_text()
        
        logger.info(f"Processing complete. Cleaned text contains {char_count} characters.")
    
    except FileNotFoundError as e:
        error_msg = f"Input file not found: {e}"
        logger.error(error_msg)
        raise
    
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        raise
