git add .
git commit -m "Fix CORS wildcard credentials conflict"
git push origin mainimport os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")

# For SQLite, we need connect_args={"check_same_thread": False}
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    file_path = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to analyses
    analyses = relationship("Analysis", back_populates="resume", cascade="all, delete-orphan")

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"))
    score = Column(Integer)
    summary = Column(Text)
    missing_skills = Column(JSON)          # List of strings
    suggested_improvements = Column(JSON)  # List of strings
    grammar_issues = Column(JSON)          # List of strings
    ats_compatibility = Column(JSON)      # Dict containing compatibility metrics/notes
    suggested_roles = Column(JSON)        # List of strings
    analyzed_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to resume
    resume = relationship("Resume", back_populates="analyses")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
