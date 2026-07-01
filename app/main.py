from fastapi import FastAPI
from app.api.endpoints import chat, ingest

app = FastAPI(title="Mini AI Assistant")

app.include_router(chat.router)
app.include_router(ingest.router)

@app.get("/")
async def root():
    return {
        "message": "Mini AI Assistant is active."
    }