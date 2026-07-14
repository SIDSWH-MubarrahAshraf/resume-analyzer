import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ResumeHistoryItem {
  id: number;
  filename: string;
  uploaded_at: string;
  latest_score: number | null;
  latest_analysis_id: number | null;
}

export interface AtsCompatibility {
  ats_score: number;
  feedback: string;
  formatting_issues: string[];
}

export interface Analysis {
  id: number;
  resume_id: number;
  score: number;
  summary: string;
  missing_skills: string[];
  suggested_improvements: string[];
  grammar_issues: string[];
  ats_compatibility: AtsCompatibility;
  suggested_roles: string[];
  analyzed_at: string;
}

export interface UploadResponse {
  id: number;
  filename: string;
  uploaded_at: string;
}

@Injectable({
  providedIn: 'root'
})
export class ResumeService {
  private apiUrl =  'https://resume-analyzer-1crm.vercel.app/api';

  constructor(private http: HttpClient) {}

  uploadResume(file: File): Observable<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<UploadResponse>(`${this.apiUrl}/upload`, formData);
  }

  analyzeResume(resumeId: number): Observable<Analysis> {
    return this.http.post<Analysis>(`${this.apiUrl}/analyze/${resumeId}`, {});
  }

  getAnalysis(analysisId: number): Observable<Analysis> {
    return this.http.get<Analysis>(`${this.apiUrl}/analysis/${analysisId}`);
  }

  getHistory(): Observable<ResumeHistoryItem[]> {
    return this.http.get<ResumeHistoryItem[]>(`${this.apiUrl}/history`);
  }

  deleteResume(resumeId: number): Observable<any> {
    return this.http.delete<any>(`${this.apiUrl}/resume/${resumeId}`);
  }
}
