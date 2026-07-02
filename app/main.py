from fastapi import FastAPI
from app.api.endpoints import chat, ingest
from app.utils.openapi import patch_openapi

app = FastAPI(title="Mini AI Assistant")
app.include_router(ingest.router)
app.include_router(chat.router)

patch_openapi(app)

@app.get("/")
async def root():
    return {
        "message": "Mini AI Assistant is active."
    }