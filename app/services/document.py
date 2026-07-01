import os
import glob
import logging
import tiktoken
from pypdf import PdfReader

logger = logging.getLogger(__name__)

def chunk_text(text: str, filename: str, page_idx: int = 1, chunk_size: int = 600, chunk_overlap: int = 150) -> list[dict]:
    chunks = []
    if not text or not text.strip():
        return chunks
        
    tokenizer = tiktoken.get_encoding("cl100k_base")
    tokens = tokenizer.encode(text)
    
    if len(tokens) <= chunk_size:
        chunks.append({
            "text": text.strip(),
            "source": filename,
            "page": page_idx
        })
    else:
        i = 0
        while i < len(tokens):
            chunk_tokens = tokens[i:i + chunk_size]
            chunk_text = tokenizer.decode(chunk_tokens).strip()
            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "source": filename,
                    "page": page_idx
                })
            i += chunk_size - chunk_overlap
            
    return chunks

def load_and_chunk_file(file_path: str, chunk_size: int = 600, chunk_overlap: int = 150) -> list[dict]:
    chunks = []
    filename = os.path.basename(file_path)
    ext = os.path.splitext(filename)[1].lower()
    
    if not os.path.exists(file_path):
        logger.warning(f"File not found: {file_path}")
        return chunks
        
    try:
        if ext == ".pdf":
            logger.info(f"Processing PDF: {filename}")
            reader = PdfReader(file_path)
            for page_idx, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                chunks.extend(chunk_text(text, filename, page_idx, chunk_size, chunk_overlap))
        elif ext in [".txt", ".md"]:
            logger.info(f"Processing Text/Markdown: {filename}")
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            chunks.extend(chunk_text(text, filename, 1, chunk_size, chunk_overlap))
        else:
            logger.warning(f"Unsupported file format: {ext} for file {filename}")
    except Exception as e:
        logger.error(f"Error loading {filename}: {e}")
        
    return chunks

def load_and_chunk_pdfs(directory_path: str, chunk_size: int = 600, chunk_overlap: int = 150) -> list[dict]:
    return load_and_chunk_documents(directory_path, chunk_size, chunk_overlap)

def load_and_chunk_documents(directory_path: str, chunk_size: int = 600, chunk_overlap: int = 150) -> list[dict]:
    chunks = []
    if not os.path.exists(directory_path):
        logger.warning(f"Directory not found: {directory_path}")
        return chunks
        
    patterns = ["*.pdf", "*.txt", "*.md"]
    files = []
    for pattern in patterns:
        files.extend(glob.glob(os.path.join(directory_path, pattern)))
        
    if not files:
        logger.warning(f"No PDF, TXT, or MD files found in {directory_path}")
        return chunks
        
    for file_path in files:
        file_chunks = load_and_chunk_file(file_path, chunk_size, chunk_overlap)
        chunks.extend(file_chunks)
        logger.info(f"Successfully chunked {os.path.basename(file_path)} into {len(file_chunks)} parts")
        
    return chunks