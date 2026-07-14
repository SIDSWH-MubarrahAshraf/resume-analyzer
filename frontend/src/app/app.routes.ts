import { Routes } from '@angular/router';
import { Dashboard } from './components/dashboard/dashboard';
import { Result } from './components/result/result';

export const routes: Routes = [
  { path: '', component: Dashboard },
  { path: 'result/:id', component: Result },
  { path: '**', redirectTo: '' }
];
