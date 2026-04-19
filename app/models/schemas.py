from pydantic import BaseModel
from typing import Optional

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class ChatRequest(BaseModel):
    query: str

class ChatSource(BaseModel):
    filename: str
    department: str
    preview: str

class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource]
    tokens: int
    cost: float
    latency: float
    blocked: bool
    model_used: str
    is_complex: Optional[bool] = False

class DocumentMeta(BaseModel):
    doc_id: str
    filename: str
    department: str
    description: Optional[str] = ""
    uploaded_by: str
    ingested_at: str
