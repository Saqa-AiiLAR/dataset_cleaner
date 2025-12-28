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
    print(f"Found {len(pdf_files)} PDF file(s) to process.")
    
    # Process each PDF file
    for pdf_path in pdf_files:
        try:
            print(f"Processing: {pdf_path.name}")
            
            # Get file size before processing
            file_size = pdf_path.stat().st_size
            
            # Extract text from PDF
            with pdfplumber.open(pdf_path) as pdf:
                extracted_text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text += page_text
            
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
