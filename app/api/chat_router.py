from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from app.api.auth_router import get_current_user
from app.core.rag_engine import ask
from app.models.schemas import ChatRequest, ChatResponse
import traceback

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/ask")
async def chat(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    try:
        result = await run_in_threadpool(ask, req.query, current_user.get("role", "employee"))
        return JSONResponse(content=result)
    except Exception as e:
        tb = traceback.format_exc()
        print(f"CHAT ERROR: {e}\n{tb}")
        # Return 200 with error message so CORS headers are included
        return JSONResponse(content={
            "answer": f"⚠️ Server error: {str(e)[:200]}. Check Railway logs for details.",
            "sources": [], "tokens": 0, "cost": 0.0,
            "latency": 0.0, "blocked": True,
            "model_used": "none", "is_complex": False
        })
