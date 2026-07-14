import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { ResumeService, Analysis } from '../../services/resume.service';

@Component({
  selector: 'app-result',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './result.html',
  styleUrl: './result.css'
})
export class Result implements OnInit {
  protected readonly analysis = signal<Analysis | null>(null);
  protected readonly isLoading = signal(false);
  protected readonly errorMessage = signal<string>('');

  // Selected tab for detailed feedback section
  protected readonly activeTab = signal<string>('improvements');

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private resumeService: ResumeService
  ) {}

  ngOnInit(): void {
    const idParam = this.route.snapshot.paramMap.get('id');
    if (idParam) {
      const id = parseInt(idParam, 10);
      if (!isNaN(id)) {
        this.loadAnalysis(id);
      } else {
        this.errorMessage.set('Invalid analysis ID.');
      }
    } else {
      this.errorMessage.set('No analysis ID provided.');
    }
  }

  loadAnalysis(id: number): void {
    this.isLoading.set(true);
    this.resumeService.getAnalysis(id).subscribe({
      next: (data) => {
        this.analysis.set(data);
        this.isLoading.set(false);
      },
      error: (err) => {
        console.error('Failed to load analysis', err);
        this.errorMessage.set('Could not fetch the detailed analysis. Verify if the database entry exists.');
        this.isLoading.set(false);
      }
    });
  }

  // --- Visual Helpers ---
  getScoreRating(score: number): string {
    if (score >= 85) return 'Excellent';
    if (score >= 70) return 'Good / Competitive';
    if (score >= 50) return 'Needs Improvements';
    return 'Weak / Critical Redesign Needed';
  }

  getScoreColorClass(score: number): string {
    if (score >= 85) return 'score-excellent';
    if (score >= 70) return 'score-good';
    if (score >= 50) return 'score-average';
    return 'score-poor';
  }

  getDashOffset(score: number): number {
    // 2 * PI * r = 2 * 3.14159 * 54 = 339.29 (circumference of stroke circle)
    const circumference = 339.29;
    return circumference - (score / 100) * circumference;
  }

  setActiveTab(tabName: string): void {
    this.activeTab.set(tabName);
  }

  goBack(): void {
    this.router.navigate(['/']);
  }
}
