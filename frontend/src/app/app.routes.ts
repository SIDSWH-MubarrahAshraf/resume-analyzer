import { Routes } from '@angular/router';
import { Dashboard } from './components/dashboard/dashboard';
import { Result } from './components/result/result';
import { VoiceAssistant } from './components/voice-assistant/voice-assistant';

export const routes: Routes = [
  { path: '', component: Dashboard },
  { path: 'result/:id', component: Result },
  { path: 'voice-assistant', component: VoiceAssistant },
  { path: '**', redirectTo: '' }
];
