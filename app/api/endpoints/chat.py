from fastapi import APIRouter
from app.schemas.schema import ChatRequest, ChatResponse
from app.services.rag_pipeline import get_rag_response

router = APIRouter(prefix="/api/chat", tags=["Chat"])

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    answer = await get_rag_response(
        query_text=request.message,
        user_id=request.user_id,
        session_id=request.session_id
    )
    return ChatResponse(answer=answer)