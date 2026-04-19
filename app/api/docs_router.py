from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from app.api.auth_router import get_current_user
from app.core.vectorstore import ingest, list_docs, delete_doc
from app.core.rbac import has_feature, get_departments

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
    result = ingest(content, file.filename, department, current_user.get("email",""), description)
    if not result["success"]:
        raise HTTPException(status_code=422, detail=result["reason"])
    return result

@router.get("/list")
def list_documents(current_user: dict = Depends(get_current_user)):
    allowed = get_departments(current_user.get("role","employee"))
    return list_docs(allowed)

@router.delete("/{doc_id}")
def remove_document(doc_id: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete documents")
    success = delete_doc(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"deleted": doc_id}
