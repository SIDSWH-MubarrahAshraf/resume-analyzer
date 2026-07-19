import { Component, OnInit, OnDestroy, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { ResumeService, ChatMessage } from '../../services/resume.service';

@Component({
  selector: 'app-voice-assistant',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  templateUrl: './voice-assistant.html',
  styleUrl: './voice-assistant.css'
})
export class VoiceAssistant implements OnInit, OnDestroy {
  // Speech Recognition Object
  private recognition: any = null;
  private accumulatedTranscript = '';
  
  // State Signals
  protected readonly messages = signal<ChatMessage[]>([]);
  protected readonly isListening = signal(false);
  protected readonly isSpeechSupported = signal(false);
  protected readonly currentTranscript = signal('');
  protected readonly keyboardInput = signal('');
  protected readonly isLoading = signal(false);
  protected readonly ttsEnabled = signal(true);
  protected readonly errorMessage = signal('');

  constructor(private resumeService: ResumeService) {}

  ngOnInit(): void {
    this.checkSpeechSupport();
    this.initWelcomeMessage();
  }

  ngOnDestroy(): void {
    this.stopSpeaking();
    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch (e) {}
    }
  }

  private checkSpeechSupport(): void {
    if (typeof window !== 'undefined') {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        this.isSpeechSupported.set(true);
        this.initSpeechRecognition(SpeechRecognition);
      } else {
        this.errorMessage.set('Speech recognition is not supported in this browser. You can still type your questions below!');
      }
    }
  }

  private initWelcomeMessage(): void {
    const welcomeText = "Hello! I am your AI career coach. Ask me anything about resume building, interview preparation, career transitions, or job search strategies!";
    this.messages.set([
      { role: 'model', content: welcomeText }
    ]);
    // Speak welcome message if TTS is active
    setTimeout(() => {
      if (this.ttsEnabled()) {
        this.speakAnswer(welcomeText);
      }
    }, 800);
  }

  private initSpeechRecognition(SpeechRecognitionClass: any): void {
    this.recognition = new SpeechRecognitionClass();
    this.recognition.continuous = true; // Keep listening until explicitly stopped
    this.recognition.interimResults = true; // Show results in progress
    this.recognition.lang = 'en-US';

    this.recognition.onstart = () => {
      this.isListening.set(true);
      this.currentTranscript.set('');
      this.accumulatedTranscript = '';
      this.errorMessage.set('');
      this.stopSpeaking();
    };

    this.recognition.onresult = (event: any) => {
      let interimTranscript = '';
      let newFinalTranscript = '';
      
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          newFinalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }
      
      if (newFinalTranscript) {
        this.accumulatedTranscript += newFinalTranscript;
      }
      
      this.currentTranscript.set(this.accumulatedTranscript + interimTranscript);
    };

    this.recognition.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error);
      this.isListening.set(false);
      
      if (event.error === 'not-allowed') {
        this.errorMessage.set('Microphone access was denied. Please check your browser site settings.');
      } else if (event.error !== 'aborted') {
        this.errorMessage.set(`Speech recognition failed: ${event.error}`);
      }
    };

    this.recognition.onend = () => {
      this.isListening.set(false);
      // Submit the accumulated speech query
      const finalQuery = this.currentTranscript().trim();
      if (finalQuery) {
        this.submitQuery(finalQuery);
        this.currentTranscript.set('');
        this.accumulatedTranscript = '';
      }
    };
  }

  protected toggleListening(): void {
    if (!this.isSpeechSupported()) {
      return;
    }

    if (this.isListening()) {
      this.recognition.stop();
    } else {
      try {
        this.recognition.start();
      } catch (e) {
        console.error('Error starting recognition:', e);
        this.errorMessage.set('Failed to access microphone. Please refresh and try again.');
      }
    }
  }

  protected submitQuery(query: string): void {
    if (!query.trim()) return;

    // Add user message
    const updatedMessages = [...this.messages(), { role: 'user' as const, content: query }];
    this.messages.set(updatedMessages);
    this.isLoading.set(true);
    this.errorMessage.set('');
    
    // Stop any ongoing speech
    this.stopSpeaking();

    // Call service (with history)
    this.resumeService.askVoiceAssistant(query, this.messages().slice(0, -1)).subscribe({
      next: (res) => {
        this.isLoading.set(false);
        const aiResponse = res.answer;
        
        // Add AI message
        this.messages.set([...this.messages(), { role: 'model' as const, content: aiResponse }]);
        
        // Read response out loud
        if (this.ttsEnabled()) {
          this.speakAnswer(aiResponse);
        }
      },
      error: (err) => {
        this.isLoading.set(false);
        this.errorMessage.set('Could not fetch response. Please verify if the backend is running.');
        console.error('API Error:', err);
      }
    });
  }

  protected onTextSubmit(event: Event): void {
    event.preventDefault();
    const query = this.keyboardInput().trim();
    if (query) {
      this.submitQuery(query);
      this.keyboardInput.set('');
    }
  }

  protected toggleTts(): void {
    this.ttsEnabled.update(val => !val);
    if (!this.ttsEnabled()) {
      this.stopSpeaking();
    } else {
      // Speak last message if it's from AI
      const list = this.messages();
      if (list.length > 0) {
        const lastMsg = list[list.length - 1];
        if (lastMsg.role === 'model') {
          this.speakAnswer(lastMsg.content);
        }
      }
    }
  }

  private speakAnswer(text: string): void {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel(); // Clear previous speech queue
      
      const utterance = new SpeechSynthesisUtterance(text);
      const voices = window.speechSynthesis.getVoices();
      
      // Try to find a standard English voice
      const englishVoice = voices.find(v => v.lang.startsWith('en'));
      if (englishVoice) {
        utterance.voice = englishVoice;
      }
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      window.speechSynthesis.speak(utterance);
    }
  }

  private stopSpeaking(): void {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
  }

  protected clearChat(): void {
    this.stopSpeaking();
    this.messages.set([]);
    this.currentTranscript.set('');
    this.keyboardInput.set('');
    this.errorMessage.set('');
    this.initWelcomeMessage();
  }
}
