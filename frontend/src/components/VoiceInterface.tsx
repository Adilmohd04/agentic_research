/**
 * Professional Voice Interface - Enterprise Grade
 * Real speech-to-text and text-to-speech functionality
 */

'use client';

import { useState, useEffect, useRef, useCallback } from 'react';

interface VoiceInterfaceProps {
  sessionId: string;
}

// Browser speech recognition types
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

interface ConversationEntry {
  id: string;
  type: 'user' | 'assistant';
  text: string;
  timestamp: Date;
  isProcessing?: boolean;
}

export default function VoiceInterface({ sessionId }: VoiceInterfaceProps) {
  // Core state
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [currentTranscript, setCurrentTranscript] = useState('');
  const [conversation, setConversation] = useState<ConversationEntry[]>([]);
  
  // Voice settings
  const [selectedVoice, setSelectedVoice] = useState<SpeechSynthesisVoice | null>(null);
  const [availableVoices, setAvailableVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [speechRate, setSpeechRate] = useState(0.9);
  const [speechVolume, setSpeechVolume] = useState(0.8);
  
  // System state
  const [speechSupported, setSpeechSupported] = useState(false);
  const [error, setError] = useState<string>('');
  const [permissionGranted, setPermissionGranted] = useState(false);

  // Refs
  const recognitionRef = useRef<any>(null);
  const synthRef = useRef<SpeechSynthesis | null>(null);
  const conversationEndRef = useRef<HTMLDivElement>(null);

  // Initialize speech recognition
  const initializeSpeechRecognition = useCallback(() => {
    if (typeof window === 'undefined') return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      setError('Speech recognition not supported. Please use Chrome, Edge, or Safari.');
      return;
    }

    recognitionRef.current = new SpeechRecognition();
    const recognition = recognitionRef.current;

    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setIsListening(true);
      setError('');
      setCurrentTranscript('');
    };

    recognition.onresult = (event: any) => {
      let interimTranscript = '';
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }

      setCurrentTranscript(interimTranscript);
      
      if (finalTranscript) {
        setCurrentTranscript('');
        processUserInput(finalTranscript.trim());
      }
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.onerror = (event: any) => {
      setIsListening(false);
      
      let errorMessage = '';
      switch (event.error) {
        case 'no-speech':
          errorMessage = 'No speech detected. Please try again.';
          break;
        case 'audio-capture':
          errorMessage = 'Microphone not accessible. Please check permissions.';
          break;
        case 'not-allowed':
          errorMessage = 'Microphone permission denied. Please allow microphone access.';
          setPermissionGranted(false);
          break;
        case 'network':
          errorMessage = 'Network error. Please check your connection.';
          break;
        default:
          errorMessage = `Speech recognition error: ${event.error}`;
      }
      
      setError(errorMessage);
    };

    setSpeechSupported(true);
  }, []);

  // Initialize text-to-speech
  const initializeTextToSpeech = useCallback(() => {
    if (typeof window === 'undefined') return;

    if ('speechSynthesis' in window) {
      synthRef.current = window.speechSynthesis;

      const loadVoices = () => {
        const voices = synthRef.current?.getVoices() || [];
        setAvailableVoices(voices);
        
        // Find best English voice
        const preferredVoices = [
          'Microsoft Zira - English (United States)',
          'Microsoft David - English (United States)', 
          'Google US English',
          'Alex',
          'Samantha',
          'Karen'
        ];

        let bestVoice = null;
        for (const preferred of preferredVoices) {
          bestVoice = voices.find(voice => 
            voice.name.toLowerCase().includes(preferred.toLowerCase().split(' - ')[0])
          );
          if (bestVoice) break;
        }

        if (!bestVoice) {
          bestVoice = voices.find(voice => voice.lang.startsWith('en-US')) ||
                     voices.find(voice => voice.lang.startsWith('en')) ||
                     voices[0];
        }

        setSelectedVoice(bestVoice || null);
      };

      loadVoices();
      if (synthRef.current) {
        synthRef.current.onvoiceschanged = loadVoices;
      }
    }
  }, []);

  // Process user input
  const processUserInput = async (text: string) => {
    if (!text.trim()) return;

    const userEntry: ConversationEntry = {
      id: `user-${Date.now()}`,
      type: 'user',
      text: text,
      timestamp: new Date()
    };

    const processingEntry: ConversationEntry = {
      id: `assistant-${Date.now()}`,
      type: 'assistant',
      text: 'Processing your request...',
      timestamp: new Date(),
      isProcessing: true
    };

    setConversation(prev => [...prev, userEntry, processingEntry]);
    setIsProcessing(true);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/agents/coordinate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task: text,
          context: { 
            session_id: sessionId,
            input_method: 'voice',
            conversation_context: conversation.slice(-4).map(c => ({
              role: c.type === 'user' ? 'user' : 'assistant',
              content: c.text
            }))
          },
          agents: ['researcher', 'analyzer']
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      const aiResponse = result.results?.summary || result.summary || 'I processed your request successfully.';
      
      // Update the processing entry with the actual response
      setConversation(prev => prev.map(entry => 
        entry.id === processingEntry.id 
          ? { ...entry, text: aiResponse, isProcessing: false }
          : entry
      ));

      // Speak the response
      if (synthRef.current && selectedVoice && aiResponse) {
        speakText(aiResponse);
      }

    } catch (error) {
      console.error('Error processing voice input:', error);
      const errorMsg = `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}`;
      
      setConversation(prev => prev.map(entry => 
        entry.id === processingEntry.id 
          ? { ...entry, text: errorMsg, isProcessing: false }
          : entry
      ));
      
      setError(errorMsg);
      
      if (synthRef.current && selectedVoice) {
        speakText(errorMsg);
      }
    } finally {
      setIsProcessing(false);
    }
  };

  // Text-to-speech function
  const speakText = (text: string) => {
    if (!synthRef.current || !selectedVoice || !text.trim()) return;

    // Stop any ongoing speech
    synthRef.current.cancel();

    // Clean text for better speech
    const cleanText = text
      .replace(/\*\*(.*?)\*\*/g, '$1') // Remove markdown bold
      .replace(/\*(.*?)\*/g, '$1')     // Remove markdown italic
      .replace(/`(.*?)`/g, '$1')       // Remove code blocks
      .replace(/#{1,6}\s/g, '')        // Remove markdown headers
      .replace(/\n+/g, '. ')           // Replace newlines with periods
      .replace(/\s+/g, ' ')            // Normalize whitespace
      .trim();

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.voice = selectedVoice;
    utterance.rate = speechRate;
    utterance.pitch = 1.0;
    utterance.volume = speechVolume;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => {
      setIsSpeaking(false);
      setError('Text-to-speech error occurred');
    };

    setIsSpeaking(true);
    synthRef.current.speak(utterance);
  };

  // Control functions
  const startListening = async () => {
    if (!recognitionRef.current || isListening || isProcessing) return;

    // Request microphone permission
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
      setPermissionGranted(true);
      setError('');
    } catch (err) {
      setError('Microphone permission required. Please allow access and try again.');
      setPermissionGranted(false);
      return;
    }

    try {
      recognitionRef.current.start();
    } catch (error) {
      setError('Failed to start speech recognition. Please try again.');
    }
  };

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
    }
  };

  const stopSpeaking = () => {
    if (synthRef.current) {
      synthRef.current.cancel();
      setIsSpeaking(false);
    }
  };

  const clearConversation = () => {
    setConversation([]);
    setCurrentTranscript('');
    setError('');
    stopListening();
    stopSpeaking();
  };

  // Initialize on mount
  useEffect(() => {
    initializeSpeechRecognition();
    initializeTextToSpeech();
  }, [initializeSpeechRecognition, initializeTextToSpeech]);

  // Auto-scroll to bottom
  useEffect(() => {
    conversationEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation]);

  if (!speechSupported) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="mx-auto w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Voice Interface Unavailable
          </h3>
          <p className="text-gray-600 max-w-md">
            Speech recognition is not supported in your browser. Please use Chrome, Edge, or Safari for voice features.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full max-h-screen">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Voice Assistant</h2>
            <p className="text-sm text-gray-600 mt-1">
              Speak naturally to interact with your research assistant
            </p>
          </div>
          
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${
              isListening ? 'bg-red-500 animate-pulse' : 
              isProcessing ? 'bg-yellow-500 animate-pulse' :
              isSpeaking ? 'bg-blue-500 animate-pulse' : 'bg-gray-300'
            }`}></div>
            <span className="text-sm text-gray-600">
              {isListening ? 'Listening...' : 
               isProcessing ? 'Processing...' :
               isSpeaking ? 'Speaking...' : 'Ready'}
            </span>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3">
            <div className="flex">
              <svg className="w-5 h-5 text-red-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="ml-3 text-sm text-red-800">{error}</p>
            </div>
          </div>
        )}
      </div>

      {/* Voice Controls */}
      <div className="flex-shrink-0 bg-gray-50 p-6 border-b border-gray-200">
        <div className="flex items-center justify-center space-x-4">
          {/* Main Voice Button */}
          <button
            onClick={isListening ? stopListening : startListening}
            disabled={isProcessing}
            className={`w-16 h-16 rounded-full flex items-center justify-center text-white font-semibold transition-all duration-200 ${
              isListening
                ? 'bg-red-500 hover:bg-red-600 animate-pulse shadow-lg'
                : 'bg-indigo-600 hover:bg-indigo-700 shadow-md hover:shadow-lg'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            {isListening ? (
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10h6v4H9z" />
              </svg>
            ) : (
              <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
            )}
          </button>

          {/* Secondary Controls */}
          {isSpeaking && (
            <button
              onClick={stopSpeaking}
              className="px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-lg text-sm font-medium"
            >
              Stop Speaking
            </button>
          )}
          
          <button
            onClick={clearConversation}
            className="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg text-sm font-medium"
          >
            Clear Chat
          </button>
        </div>

        {/* Current Transcript */}
        {currentTranscript && (
          <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p className="text-blue-800 text-sm">
              <span className="font-medium">Listening: </span>
              {currentTranscript}
            </p>
          </div>
        )}
      </div>

      {/* Voice Settings */}
      {availableVoices.length > 0 && (
        <div className="flex-shrink-0 bg-white p-4 border-b border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Voice</label>
              <select
                value={selectedVoice?.name || ''}
                onChange={(e) => {
                  const voice = availableVoices.find(v => v.name === e.target.value);
                  setSelectedVoice(voice || null);
                }}
                className="w-full text-xs p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                {availableVoices.map((voice) => (
                  <option key={voice.name} value={voice.name}>
                    {voice.name} ({voice.lang})
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Speed: {speechRate.toFixed(1)}x
              </label>
              <input
                type="range"
                min="0.5"
                max="2"
                step="0.1"
                value={speechRate}
                onChange={(e) => setSpeechRate(parseFloat(e.target.value))}
                className="w-full"
              />
            </div>
            
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Volume: {Math.round(speechVolume * 100)}%
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={speechVolume}
                onChange={(e) => setSpeechVolume(parseFloat(e.target.value))}
                className="w-full"
              />
            </div>
          </div>
        </div>
      )}

      {/* Conversation */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {conversation.length === 0 ? (
          <div className="text-center py-12">
            <div className="mx-auto w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Start a Voice Conversation</h3>
            <p className="text-gray-600 max-w-md mx-auto">
              Click the microphone button and speak your research question. The AI will respond with both text and voice.
            </p>
          </div>
        ) : (
          <>
            {conversation.map((entry) => (
              <div
                key={entry.id}
                className={`flex ${entry.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                    entry.type === 'user'
                      ? 'bg-indigo-600 text-white'
                      : 'bg-white border border-gray-200 text-gray-900'
                  }`}
                >
                  <div className="flex items-start space-x-2">
                    {entry.type === 'assistant' && (
                      <div className="w-6 h-6 bg-indigo-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                        <svg className="w-3 h-3 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                        </svg>
                      </div>
                    )}
                    <div className="flex-1">
                      <p className="text-sm whitespace-pre-wrap">
                        {entry.isProcessing ? (
                          <span className="flex items-center">
                            <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Processing...
                          </span>
                        ) : (
                          entry.text
                        )}
                      </p>
                      <p className="text-xs mt-1 opacity-70">
                        {entry.timestamp.toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
            <div ref={conversationEndRef} />
          </>
        )}
      </div>
    </div>
  );
}