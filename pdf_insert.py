"""
Entry point for PDF text extraction.
Extracts text from PDF files in source/ folder and appends to saqa.txt.
"""
from src.pdf_processor import PDFProcessor
from src.utils import setup_logging
from src.config import config

if __name__ == "__main__":
    # Set up logging
    logger = setup_logging(config.log_file)
    
    try:
        # Create processor and process all PDFs
        processor = PDFProcessor()
        processed_count = processor.process_all_pdfs()
        
        if processed_count > 0:
            logger.info(f"Successfully processed {processed_count} PDF file(s).")
        else:
            logger.warning("No PDF files were processed.")
    
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        raise
