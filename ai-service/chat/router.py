# chat/router.py

from fastapi import APIRouter, Depends
from chat.schemas import ChatRequest, ChatResponse, SummarizeRequest, SummarizeResponse
from chat.service import chat, summarize
from auth.dependencies import verify_token

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, payload: dict = Depends(verify_token)):
    return await chat(request)


@router.post("/summarize/", response_model=SummarizeResponse)
async def summarize_endpoint(
    request: SummarizeRequest, payload: dict = Depends(verify_token)
):
    summary = await summarize(request.conversation_history)
    return SummarizeResponse(summary=summary)
