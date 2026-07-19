import { Component, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { ResumeService, ResumeHistoryItem } from '../../services/resume.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css'
})
export class Dashboard implements OnInit {
  // Signals for state management
  protected readonly history = signal<ResumeHistoryItem[]>([]);
  protected readonly isUploading = signal(false);
  protected readonly isAnalyzing = signal(false);
  protected readonly uploadProgress = signal<string>('');
  protected readonly errorMessage = signal<string>('');
  protected readonly isDragging = signal(false);

  // Computed signals for stats
  protected readonly totalCount = computed(() => this.history().length);
  
  protected readonly averageScore = computed(() => {
    const scoredResumes = this.history().filter(item => item.latest_score !== null);
    if (scoredResumes.length === 0) return 0;
    const sum = scoredResumes.reduce((acc, curr) => acc + (curr.latest_score || 0), 0);
    return Math.round(sum / scoredResumes.length);
  });

  protected readonly highestScore = computed(() => {
    const scores = this.history()
      .map(item => item.latest_score)
      .filter((score): score is number => score !== null);
    if (scores.length === 0) return 0;
    return Math.max(...scores);
  });

  constructor(
    private resumeService: ResumeService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.loadHistory();
  }

  loadHistory(): void {
    this.resumeService.getHistory().subscribe({
      next: (data) => {
        this.history.set(data);
      },
      error: (err) => {
        console.error('Failed to load history', err);
        this.errorMessage.set('Could not fetch resume history. Please check if the backend is running.');
      }
    });
  }

  // --- Drag and Drop handlers ---
  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging.set(true);
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging.set(false);
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging.set(false);
    this.errorMessage.set('');

    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      this.handleFile(files[0]);
    }
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.handleFile(input.files[0]);
    }
  }

  private handleFile(file: File): void {
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (ext !== 'pdf' && ext !== 'docx') {
      this.errorMessage.set('Invalid file type. Only PDF and DOCX files are allowed.');
      return;
    }

    this.isUploading.set(true);
    this.uploadProgress.set('Uploading resume...');

    this.resumeService.uploadResume(file).subscribe({
      next: (response) => {
        this.uploadProgress.set('Analyzing resume (this might take a few seconds)...');
        this.isAnalyzing.set(true);
        this.isUploading.set(false);

        // Auto trigger analysis
        this.resumeService.analyzeResume(response.id).subscribe({
          next: (analysis) => {
            this.isAnalyzing.set(false);
            this.loadHistory();
            this.router.navigate(['/result', analysis.id]);
          },
          error: (err) => {
            this.isAnalyzing.set(false);
            this.errorMessage.set('Resume uploaded successfully, but AI analysis failed: ' + (err.error?.detail || err.message));
            this.loadHistory();
          }
        });
      },
      error: (err) => {
        this.isUploading.set(false);
        this.errorMessage.set('Upload failed: ' + (err.error?.detail || err.message));
      }
    });
  }

  viewAnalysis(analysisId: number | null): void {
    if (analysisId) {
      this.router.navigate(['/result', analysisId]);
    }
  }

  analyzeExisting(resumeId: number): void {
    this.isAnalyzing.set(true);
    this.uploadProgress.set('Analyzing resume...');
    this.resumeService.analyzeResume(resumeId).subscribe({
      next: (analysis) => {
        this.isAnalyzing.set(false);
        this.loadHistory();
        this.router.navigate(['/result', analysis.id]);
      },
      error: (err) => {
        this.isAnalyzing.set(false);
        this.errorMessage.set('AI analysis failed: ' + (err.error?.detail || err.message));
      }
    });
  }

  deleteResume(resumeId: number, event: Event): void {
    event.stopPropagation();
    if (confirm('Are you sure you want to delete this resume and its analysis?')) {
      this.resumeService.deleteResume(resumeId).subscribe({
        next: () => {
          this.loadHistory();
        },
        error: (err) => {
          this.errorMessage.set('Failed to delete: ' + (err.error?.detail || err.message));
        }
      });
    }
  }
}
