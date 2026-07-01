import os
import shutil
import logging
from fastapi import UploadFile, HTTPException
from app.services.document import load_and_chunk_documents
from app.services.vector_store import create_pinecone_index_if_not_exists, upsert_documents
import app.config as config

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

async def save_uploaded_file(file: UploadFile) -> str:
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    
    if ext not in [".pdf", ".txt", ".md"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'."
        )
        
    os.makedirs(DATA_DIR, exist_ok=True)
    file_path = os.path.join(DATA_DIR, filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return filename
    except Exception as e:
        logger.error(f"Failed to save file {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

async def run_ingestion() -> int:
    if not config.PINECONE_API_KEY or not config.OPENAI_API_KEY:
        logger.error("API Keys are not configured correctly")
        raise ValueError("API Keys are not configured correctly")
        
    os.makedirs(DATA_DIR, exist_ok=True)
    logger.info(f"Scanning for PDF, TXT, and Markdown documents in '{DATA_DIR}'...")
    chunks = load_and_chunk_documents(DATA_DIR)
    
    if not chunks:
        logger.info("No chunks were generated. Placed files are missing or empty.")
        return 0
        
    logger.info(f"Generated {len(chunks)} text chunks. Uploading to Pinecone...")
    create_pinecone_index_if_not_exists()
    await upsert_documents(chunks)
    logger.info("Ingestion completed successfully!")
    return len(chunks)