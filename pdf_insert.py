import pdfplumber
from pathlib import Path
import shutil
from datetime import datetime

# Define paths
source_folder = Path("source")
archive_folder = Path("archive")
output_file = Path("saqa.txt")
log_file = Path("logs")

# Create archive folder if it doesn't exist
archive_folder.mkdir(exist_ok=True)

# Get all PDF files from source folder
pdf_files = list(source_folder.glob("*.pdf"))

if not pdf_files:
    print("No PDF files found in source folder.")
else:
    total_pdfs = len(pdf_files)
    print(f"Found {total_pdfs} PDF file(s) to process.")
    
    # Process each PDF file
    for pdf_index, pdf_path in enumerate(pdf_files, 1):
        try:
            print(f"\n[{pdf_index}/{total_pdfs}] Processing: {pdf_path.name}")
            
            # Get file size before processing
            file_size = pdf_path.stat().st_size
            
            # Extract text from PDF
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                print(f"  Extracting text from {total_pages} pages...")
                extracted_text = ""
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text += page_text
                    # Show progress every 10 pages or at the end
                    if page_num % 10 == 0 or page_num == total_pages:
                        percentage = (page_num / total_pages) * 100
                        print(f"  Progress: Page {page_num}/{total_pages} ({percentage:.1f}%)")
            
            # Count characters
            char_count = len(extracted_text)
            
            # Append text to saqa.txt
            if extracted_text:
                with open(output_file, "a", encoding="utf-8") as f:
                    f.write(extracted_text)
                print(f"  ✓ Extracted and saved text from {pdf_path.name}")
            else:
                print(f"  ⚠ No text extracted from {pdf_path.name}")
            
            # Move PDF to archive folder
            archive_path = archive_folder / pdf_path.name
            shutil.move(str(pdf_path), str(archive_path))
            print(f"  ✓ Moved {pdf_path.name} to archive folder")
            
            # Write log entry
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"pdf_insert.py - {pdf_path.name} - {timestamp} - {char_count} chars - {file_size} bytes\n"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
            
        except Exception as e:
            print(f"  ✗ Error processing {pdf_path.name}: {str(e)}")
            # Log error as well
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"pdf_insert.py - {pdf_path.name} - {timestamp} - ERROR: {str(e)}\n"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
            continue
    
    print(f"\nProcessing complete. Processed {len(pdf_files)} file(s).")
