from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    class Config:
        from_attributes = True

class PaperResponse(BaseModel):
    id: str
    title: str
    authors: Optional[str] = "Unknown"
    year: Optional[int] = None
    doi: Optional[str] = None
    abstract: Optional[str] = ""
    file_name: str
    created_at: datetime
    class Config:
        from_attributes = True

class SessionResponse(BaseModel):
    id: str
    name: str
    created_at: datetime
    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    session_id: str
    message: str
    paper_ids: Optional[List[str]] = None

class StepLogSchema(BaseModel):
    agent: str
    action: str
    details: Any

class ChatResponse(BaseModel):
    answer: str
    plan: List[Dict[str, Any]]
    logs: List[Dict[str, Any]]
    artifacts: Dict[str, Any]

class LitReviewRequest(BaseModel):
    session_id: str
    title: str
    paper_ids: List[str]

class CompareRequest(BaseModel):
    session_id: str
    paper_ids: List[str]

class ExportRequest(BaseModel):
    title: str
    content: str
    format: str = "pdf" # pdf, docx, md
    metadata: Optional[Dict[str, str]] = None
