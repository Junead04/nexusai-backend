from fastapi import APIRouter, Depends, HTTPException
from app.api.auth_router import get_current_user
from app.core.rag_engine import ask
from app.core.rbac import has_feature
from app.models.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/ask", response_model=ChatResponse)
def chat(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    result = ask(req.query, current_user.get("role", "employee"))
    return ChatResponse(**result)
