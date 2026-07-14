from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Dict, Any, Optional

# --- Analysis Schemas ---
class AnalysisBase(BaseModel):
    score: int
    summary: str
    missing_skills: List[str]
    suggested_improvements: List[str]
    grammar_issues: List[str]
    ats_compatibility: Dict[str, Any]
    suggested_roles: List[str]

class AnalysisCreate(AnalysisBase):
    resume_id: int

class Analysis(AnalysisBase):
    id: int
    resume_id: int
    analyzed_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Resume Schemas ---
class ResumeBase(BaseModel):
    filename: str
    file_path: str

class ResumeCreate(ResumeBase):
    pass

class Resume(ResumeBase):
    id: int
    uploaded_at: datetime
    analyses: List[Analysis] = []

    model_config = ConfigDict(from_attributes=True)


# --- Full Response Schema for Dashboard ---
class ResumeHistoryItem(BaseModel):
    id: int
    filename: str
    uploaded_at: datetime
    latest_score: Optional[int] = None
    latest_analysis_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
