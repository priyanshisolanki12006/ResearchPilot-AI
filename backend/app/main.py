import sys
from pathlib import Path

# Inject project root paths to resolve ModuleNotFoundError regardless of current working directory
current_file = Path(__file__).resolve()
project_root = str(current_file.parent.parent.parent)
backend_root = str(current_file.parent.parent)

if project_root not in sys.path:
    sys.path.insert(0, project_root)
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

import os
import shutil
import uuid
import hashlib
from typing import List, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.services.database import get_db, init_db
from backend.app.db import models
from backend.app.schemas import api_schemas
from backend.app.services import pdf_parser, vector_store, export
from backend.app.agents.orchestrator import Orchestrator, AgentSession

# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Multi-Agent system for research paper search, synthesis, and compilation.",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    # Create SQLite tables
    init_db()

# Simple Helper for password hashing (no heavy bcrypt dependencies needed)
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# Auth Endpoints
@app.post("/api/auth/register", response_model=api_schemas.UserResponse)
def register(user_data: api_schemas.UserRegister, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user_data.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed = hash_password(user_data.password)
    user = models.User(username=user_data.username, hashed_password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.post("/api/auth/login")
def login(user_data: api_schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user_data.username).first()
    if not db_user or db_user.hashed_password != hash_password(user_data.password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    return {
        "access_token": f"mocked-jwt-token-for-{db_user.username}",
        "token_type": "bearer",
        "user": {
            "id": db_user.id,
            "username": db_user.username
        }
    }

# Session Management Endpoints
@app.post("/api/sessions", response_model=api_schemas.SessionResponse)
def create_session(name: str = "New Research Session", db: Session = Depends(get_db)):
    session_id = str(uuid.uuid4())
    db_session = models.Session(id=session_id, name=name)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

@app.get("/api/sessions", response_model=List[api_schemas.SessionResponse])
def get_sessions(db: Session = Depends(get_db)):
    return db.query(models.Session).order_by(models.Session.created_at.desc()).all()

@app.get("/api/sessions/{session_id}/messages")
def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    messages = db.query(models.ChatMessage).filter(models.ChatMessage.session_id == session_id).order_by(models.ChatMessage.created_at.asc()).all()
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "agent_name": m.agent_name,
            "step_logs": m.step_logs,
            "created_at": m.created_at
        }
        for m in messages
    ]

# Paper Management Endpoints
@app.post("/api/papers/upload", response_model=List[api_schemas.PaperResponse])
def upload_papers(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    uploaded_papers = []
    
    for file in files:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported.")
            
        file_id = str(uuid.uuid4())[:8]
        temp_file_name = f"{file_id}_{file.filename}"
        save_path = settings.UPLOAD_DIR / temp_file_name
        
        # Save file to upload directory
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        try:
            # Parse PDF metadata and text
            pdf_data = pdf_parser.extract_pdf_data(str(save_path))
            paper_id = pdf_data["id"] # hash of the file
            
            # Check if this paper hash already exists in DB
            db_paper = db.query(models.Paper).filter(models.Paper.id == paper_id).first()
            if db_paper:
                # Remove file copy since it's already indexed
                os.remove(save_path)
                uploaded_papers.append(db_paper)
                continue
                
            # Create paper entry
            paper = models.Paper(
                id=paper_id,
                title=pdf_data["title"],
                authors=pdf_data["authors"],
                year=int(pdf_data["year"]) if pdf_data["year"] and pdf_data["year"].isdigit() else None,
                abstract=pdf_data["abstract"],
                file_path=str(save_path),
                file_name=file.filename
            )
            
            db.add(paper)
            db.commit()
            db.refresh(paper)
            
            # Chunk and insert to Vector store
            chunks = pdf_parser.chunk_text(pdf_data["full_text"])
            vector_store.add_documents(paper_id, pdf_data["title"], chunks)
            
            uploaded_papers.append(paper)
        except Exception as e:
            # Cleanup on failure
            if os.path.exists(save_path):
                os.remove(save_path)
            raise HTTPException(status_code=500, detail=f"Error parsing PDF {file.filename}: {str(e)}")
            
    return uploaded_papers

@app.get("/api/papers", response_model=List[api_schemas.PaperResponse])
def get_papers(db: Session = Depends(get_db)):
    return db.query(models.Paper).order_by(models.Paper.created_at.desc()).all()

# Chat and Agent Workflow Endpoint
@app.post("/api/chat", response_model=api_schemas.ChatResponse)
def chat_with_agents(payload: api_schemas.ChatRequest, db: Session = Depends(get_db)):
    session_id = payload.session_id
    user_msg = payload.message
    paper_ids = payload.paper_ids
    
    db_session = db.query(models.Session).filter(models.Session.id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Save User message to history
    user_chat = models.ChatMessage(
        session_id=session_id,
        role="user",
        content=user_msg
    )
    db.add(user_chat)
    db.commit()
    
    # Initialize AgentSession context
    agent_session = AgentSession(session_id=session_id, db_session=db)
    
    # Load workspace papers
    if paper_ids:
        db_papers = db.query(models.Paper).filter(models.Paper.id.in_(paper_ids)).all()
    else:
        db_papers = db.query(models.Paper).all()
        
    for p in db_papers:
        # Load snippet text to keep agent session light
        pdf_data = pdf_parser.extract_pdf_data(p.file_path)
        agent_session.papers.append({
            "id": p.id,
            "title": p.title,
            "authors": p.authors,
            "year": p.year,
            "abstract": p.abstract,
            "full_text": pdf_data["full_text"]
        })
        
    # Fetch chat history for LLM context
    history_messages = db.query(models.ChatMessage).filter(models.ChatMessage.session_id == session_id).order_by(models.ChatMessage.created_at.asc()).all()
    agent_session.messages = [{"role": m.role, "content": m.content} for m in history_messages]
    
    # Run orchestration workflow
    orchestrator = Orchestrator()
    result = orchestrator.execute_workflow(agent_session, user_msg)
    
    # Save Assistant message and structured logs
    assistant_chat = models.ChatMessage(
        session_id=session_id,
        role="assistant",
        content=result["answer"],
        agent_name="Orchestrator",
        step_logs=result["logs"]
    )
    db.add(assistant_chat)
    db.commit()
    
    return {
        "answer": result["answer"],
        "plan": result["plan"],
        "logs": result["logs"],
        "artifacts": result["artifacts"]
    }

# Literature Review Generation Endpoint
@app.post("/api/literature-review")
def generate_lit_review(payload: api_schemas.LitReviewRequest, db: Session = Depends(get_db)):
    paper_ids = payload.paper_ids
    session_id = payload.session_id
    
    papers = db.query(models.Paper).filter(models.Paper.id.in_(paper_ids)).all()
    if not papers:
        raise HTTPException(status_code=400, detail="At least one paper must be selected.")
        
    # Initialize Session
    agent_session = AgentSession(session_id=session_id, db_session=db)
    for p in papers:
        agent_session.papers.append({
            "id": p.id,
            "title": p.title,
            "abstract": p.abstract
        })
        
    # Trigger Literature Review agent directly
    from backend.app.agents.worker_agents import LiteratureReviewAgent
    agent = LiteratureReviewAgent()
    
    prompt = f"Synthesize a literature review on '{payload.title}' using the selected papers."
    review_content = agent.execute(agent_session, prompt)
    
    # Save Lit Review to DB
    db_review = models.LiteratureReview(
        session_id=session_id,
        title=payload.title,
        content=review_content,
        papers_involved=paper_ids
    )
    db.add(db_review)
    db.commit()
    
    return {
        "title": payload.title,
        "content": review_content
    }

# Comparison Grid Endpoint
@app.post("/api/compare")
def compare_papers(payload: api_schemas.CompareRequest, db: Session = Depends(get_db)):
    paper_ids = payload.paper_ids
    session_id = payload.session_id
    
    papers = db.query(models.Paper).filter(models.Paper.id.in_(paper_ids)).all()
    if not papers:
        raise HTTPException(status_code=400, detail="At least one paper must be selected.")
        
    agent_session = AgentSession(session_id=session_id, db_session=db)
    for p in papers:
        agent_session.papers.append({
            "id": p.id,
            "title": p.title,
            "abstract": p.abstract
        })
        
    from backend.app.agents.worker_agents import ComparisonAgent
    agent = ComparisonAgent()
    
    prompt = "Create a side-by-side comparison matrix for the selected research papers."
    comparison_table = agent.execute(agent_session, prompt)
    
    return {
        "comparisons": comparison_table
    }

# File Export Endpoint
@app.post("/api/export")
def export_document(payload: api_schemas.ExportRequest):
    title = payload.title
    content = payload.content
    doc_format = payload.format.lower()
    metadata = payload.metadata or {}
    
    if doc_format == "md":
        md_text = export.generate_markdown(title, content, metadata)
        return StreamingResponse(
            iter([md_text.encode('utf-8')]),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename={title.replace(' ', '_')}.md"}
        )
    elif doc_format == "docx":
        docx_stream = export.generate_docx(title, content, metadata)
        return StreamingResponse(
            docx_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={title.replace(' ', '_')}.docx"}
        )
    elif doc_format == "pdf":
        pdf_stream = export.generate_pdf(title, content, metadata)
        return StreamingResponse(
            pdf_stream,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={title.replace(' ', '_')}.pdf"}
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported format. Choose from pdf, docx, md")
