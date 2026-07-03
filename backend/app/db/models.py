from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    papers = relationship("Paper", back_populates="user", cascade="all, delete-orphan")

class Paper(Base):
    __tablename__ = "papers"
    
    id = Column(String, primary_key=True, index=True) # Usually a hash or UUID
    title = Column(String, nullable=False)
    authors = Column(String, nullable=True)
    journal = Column(String, nullable=True)
    year = Column(Integer, nullable=True)
    doi = Column(String, nullable=True)
    abstract = Column(Text, nullable=True)
    file_path = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="papers")

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(String, primary_key=True, index=True) # UUID
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    lit_reviews = relationship("LiteratureReview", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    role = Column(String, nullable=False) # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    agent_name = Column(String, nullable=True) # e.g. 'Planner', 'Retrieval'
    step_logs = Column(JSON, nullable=True) # Stores agent thoughts/actions
    created_at = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("Session", back_populates="messages")

class LiteratureReview(Base):
    __tablename__ = "literature_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    papers_involved = Column(JSON, nullable=False) # List of paper IDs
    created_at = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("Session", back_populates="lit_reviews")
