from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.config import settings
from backend.app.db.models import Base

# Setup SQLite database engine
SQLALCHEMY_DATABASE_URL = f"sqlite:///{settings.DB_PATH}"

# For SQLite, connect_args={"check_same_thread": False} is required
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency injection helper to yield a db session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
