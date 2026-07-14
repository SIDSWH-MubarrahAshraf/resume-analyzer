import os
import shutil
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from app.database import Base, engine, get_db, Resume, Analysis
from app.parser import extract_text
from app.analyzer import analyze_resume_text
from app.schemas import Resume as ResumeSchema, Analysis as AnalysisSchema, ResumeHistoryItem

# Ensure database tables are created
Base.metadata.create_all(bind=engine)

# Directory to store uploaded resumes
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="AI Resume Analyzer API", version="1.0.0")

# Configure CORS for frontend access
frontend_origin = os.getenv("FRONTEND_URL", "http://localhost:4200")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin, "http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/upload")
def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # File validation
    filename = file.filename
    _, ext = os.path.splitext(filename.lower())
    if ext not in [".pdf", ".docx"]:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are allowed.")
    
    # Save the file locally
    file_path = os.path.join(UPLOAD_DIR, filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")
    
    # Create DB entry
    db_resume = Resume(filename=filename, file_path=file_path)
    db.add(db_resume)
    db.commit()
    db.refresh(db_resume)
    
    return {
        "id": db_resume.id,
        "filename": db_resume.filename,
        "uploaded_at": db_resume.uploaded_at
    }

@app.post("/api/analyze/{resume_id}", response_model=AnalysisSchema)
def analyze_resume(resume_id: int, db: Session = Depends(get_db)):
    # Fetch resume from database
    db_resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not db_resume:
        raise HTTPException(status_code=404, detail="Resume not found.")
    
    if not os.path.exists(db_resume.file_path):
        raise HTTPException(status_code=404, detail="Resume file not found on disk.")
    
    # 1. Parse text from the resume
    try:
        resume_text = extract_text(db_resume.file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse resume file: {str(e)}")
    
    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="The resume file appears to be empty or unscannable.")
    
    # 2. Run AI Analysis
    try:
        analysis_data = analyze_resume_text(resume_text)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")
    
    # 3. Save analysis to database
    db_analysis = Analysis(
        resume_id=db_resume.id,
        score=analysis_data.get("score", 0),
        summary=analysis_data.get("summary", ""),
        missing_skills=analysis_data.get("missing_skills", []),
        suggested_improvements=analysis_data.get("suggested_improvements", []),
        grammar_issues=analysis_data.get("grammar_issues", []),
        ats_compatibility=analysis_data.get("ats_compatibility", {}),
        suggested_roles=analysis_data.get("suggested_roles", [])
    )
    
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    
    return db_analysis

@app.get("/api/analysis/{analysis_id}", response_model=AnalysisSchema)
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    return analysis

@app.get("/api/history", response_model=List[ResumeHistoryItem])
def get_history(db: Session = Depends(get_db)):
    resumes = db.query(Resume).all()
    history = []
    
    for r in resumes:
        # Find latest analysis for this resume if exists
        latest_analysis = (
            db.query(Analysis)
            .filter(Analysis.resume_id == r.id)
            .order_by(Analysis.analyzed_at.desc())
            .first()
        )
        
        history.append({
            "id": r.id,
            "filename": r.filename,
            "uploaded_at": r.uploaded_at,
            "latest_score": latest_analysis.score if latest_analysis else None,
            "latest_analysis_id": latest_analysis.id if latest_analysis else None
        })
        
    # Sort history by uploaded_at descending
    history.sort(key=lambda x: x["uploaded_at"], reverse=True)
    return history

@app.delete("/api/resume/{resume_id}")
def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    db_resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not db_resume:
        raise HTTPException(status_code=404, detail="Resume not found.")
    
    # Try to delete the physical file
    if os.path.exists(db_resume.file_path):
        try:
            os.remove(db_resume.file_path)
        except Exception:
            pass # Keep deleting database records even if file delete fails
            
    db.delete(db_resume)
    db.commit()
    return {"message": f"Resume {resume_id} deleted successfully."}
