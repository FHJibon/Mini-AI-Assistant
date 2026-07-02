import os
import shutil
import logging
from fastapi import UploadFile, HTTPException
from app.utils.loader import load_file_text
from app.utils.chunker import chunk_documents
from app.services.vector import create_pinecone_index_if_not_exists, upsert_documents
import app.config as config

logger = logging.getLogger(__name__)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

async def save_uploaded_file(file: UploadFile) -> str:
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".txt", ".md"]:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{ext}'.")
        
    os.makedirs(DATA_DIR, exist_ok=True)
    file_path = os.path.join(DATA_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return file.filename
    except Exception as e:
        logger.error(f"Failed to save file {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

async def save_and_ingest_files(files: list[UploadFile]) -> dict:
    if not config.PINECONE_API_KEY or not config.OPENAI_API_KEY:
        logger.error("API Keys are not configured correctly")
        raise HTTPException(status_code=500, detail="API Keys are not configured correctly")

    newly_uploaded, skipped = [], []
    try:
        for file in files:
            if os.path.exists(os.path.join(DATA_DIR, file.filename)):
                skipped.append(file.filename)
            else:
                await save_uploaded_file(file)
                newly_uploaded.append(file.filename)
                
        chunks_count = 0
        if newly_uploaded:
            loaded_pages = []
            for fn in newly_uploaded:
                logger.info(f"Loading file text for: {fn}")
                loaded_pages.extend(load_file_text(os.path.join(DATA_DIR, fn)))
                
            logger.info(f"Chunking documents for {len(newly_uploaded)} files...")
            chunks = chunk_documents(loaded_pages)
            if chunks:
                logger.info(f"Initializing Pinecone and upserting {len(chunks)} chunks...")
                create_pinecone_index_if_not_exists()
                await upsert_documents(chunks)
                chunks_count = len(chunks)
                logger.info("Successfully ingested chunks to Pinecone.")
                
        return {
            "success": True,
            "ingested": newly_uploaded,
            "skipped": skipped,
            "chunks_count": chunks_count,
            "message": f"Ingested {len(newly_uploaded)} files, skipped {len(skipped)} files."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during save and ingest process: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion process failed: {str(e)}")