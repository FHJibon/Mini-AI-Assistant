from fastapi import APIRouter, UploadFile, File
from app.services.ingest import run_ingestion, save_uploaded_file

router = APIRouter(prefix="/api/ingest", tags=["Ingestion"])

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    filename = await save_uploaded_file(file)
    return {"message": f"Successfully uploaded {filename} to data folder."}

@router.post("/ingest")
async def process_ingest():
    chunks_count = await run_ingestion()
    return {
        "success": True,
        "message": "Ingestion completed successfully.",
        "chunks_count": chunks_count
    }
