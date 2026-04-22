from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from app.api.auth_router import get_current_user
from app.core.vectorstore import ingest, list_docs, delete_doc
from app.core.rbac import has_feature, get_departments
import traceback

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    department: str = Form(...),
    description: str = Form(""),
    current_user: dict = Depends(get_current_user),
):
    role = current_user.get("role", "employee")
    if not has_feature(role, "upload"):
        raise HTTPException(status_code=403, detail="Upload not permitted for your role")
    allowed = get_departments(role)
    if department not in allowed:
        raise HTTPException(status_code=403, detail=f"Cannot upload to department: {department}")
    content = await file.read()
    try:
        result = ingest(content, file.filename, department, current_user.get("email",""), description)
        if not result["success"]:
            raise HTTPException(status_code=422, detail=result["reason"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"UPLOAD ERROR: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e)[:200])

@router.get("/list")
async def list_documents(current_user: dict = Depends(get_current_user)):
    try:
        allowed = get_departments(current_user.get("role", "employee"))
        docs = await run_in_threadpool(list_docs, allowed)
        return JSONResponse(content={"documents": docs, "count": len(docs)})
    except Exception as e:
        print(f"LIST ERROR: {e}\n{traceback.format_exc()}")
        return JSONResponse(content={"documents": [], "count": 0, "error": str(e)[:200]})

@router.delete("/{doc_id}")
async def delete(doc_id: str, current_user: dict = Depends(get_current_user)):
    role = current_user.get("role", "employee")
    if not has_feature(role, "upload"):
        raise HTTPException(status_code=403, detail="Delete not permitted for your role")
    try:
        result = await run_in_threadpool(delete_doc, doc_id)
        return {"success": result, "doc_id": doc_id}
    except Exception as e:
        print(f"DELETE ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e)[:200])
