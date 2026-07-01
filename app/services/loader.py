import os
import glob
import logging
from pypdf import PdfReader

logger = logging.getLogger(__name__)

def load_file_text(file_path: str) -> list[dict]:
    pages = []
    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()
    
    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        return pages
        
    try:
        if ext == ".pdf":
            logger.info(f"Loading PDF: {filename}")
            reader = PdfReader(file_path)
            for page_idx, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                pages.append({
                    "text": text,
                    "source": filename,
                    "page": page_idx
                })
        elif ext in [".txt", ".md"]:
            logger.info(f"Loading Text/Markdown: {filename}")
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            pages.append({
                "text": text,
                "source": filename,
                "page": 1
            })
        else:
            logger.warning(f"Unsupported file format: {ext} for file {filename}")
    except Exception as e:
        logger.error(f"Error loading {filename}: {e}")
        
    return pages

def load_documents_directory(directory_path: str) -> list[dict]:
    all_pages = []
    if not os.path.exists(directory_path):
        logger.warning(f"Directory not found: {directory_path}")
        return all_pages
        
    patterns = ["*.pdf", "*.txt", "*.md"]
    files = []
    for pattern in patterns:
        files.extend(glob.glob(os.path.join(directory_path, pattern)))
        
    for file_path in files:
        file_pages = load_file_text(file_path)
        all_pages.extend(file_pages)
        logger.info(f"Successfully loaded {os.path.basename(file_path)} with {len(file_pages)} pages/parts")
        
    return all_pages
