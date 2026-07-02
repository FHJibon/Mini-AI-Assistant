from fastapi import APIRouter, UploadFile, File
from app.services.ingest import save_and_ingest_files

router = APIRouter(prefix="/api/ingest", tags=["Ingestion"])

@router.post("")
async def upload_and_ingest(files: list[UploadFile] = File(...)):
    return await save_and_ingest_files(files)
