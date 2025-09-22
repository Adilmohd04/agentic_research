/**
 * Real-time Voice Chat with Speech-to-Speech
 * Instant voice interaction with AI agents
 */

'use client';

import { useState, useEffect, useRef, useCallback } from 'react';

interface RealTimeVoiceChatProps {
  sessionId: string;
}

declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

export default function RealTimeVoiceChat({ sessionId }: RealTimeVoiceChatProps) {
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [aiResponse, setAiResponse] = useState('');
  const [conversation, setConversation] = useState<Array<{
    type: 'user' | 'ai';
    text: string;
    timestamp: Date;
  }>>([]);
  const [error, setError] = useState('');
  const [voiceEnabled, setVoiceEnabled] = useState(false);

  const recognitionRef = useRef<any>(null);
  const synthRef = useRef<SpeechSynthesis | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Initialize speech recognition and synthesis
  useEffect(() => {
    const initializeVoice = async () => {
      // Initialize speech recognition
      if (typeof window !== 'undefined') {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (SpeechRecognition) {
          recognitionRef.current = new SpeechRecognition();
          const recognition = recognitionRef.current;

          recognition.continuous = true;
          recognition.interimResults = true;
          recognition.lang = 'en-US';

          recognition.onstart = () => {
            setIsListening(true);
            setError('');
          };

          recognition.onresult = (event: any) => {
            let finalTranscript = '';
            
            for (let i = event.resultIndex; i < event.results.length; i++) {
              if (event.results[i].isFinal) {
                finalTranscript += event.results[i][0].transcript;
              }
            }

            if (finalTranscript) {
              setTranscript(finalTranscript);
              processVoiceInput(finalTranscript);
            }
          };

          recognition.onend = () => {
            setIsListening(false);
          };

          recognition.onerror = (event: any) => {
            setIsListening(false);
            setError(`Speech recognition error: ${event.error}`);
          };
        }

        // Initialize speech synthesis
        if ('speechSynthesis' in window) {
          synthRef.current = window.speechSynthesis;
        }

        setVoiceEnabled(true);
      }
    };

    initializeVoice();
  }, []);

  // Audio visualization
  useEffect(() => {
    if (isListening && canvasRef.current) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      
      if (!audioContextRef.current) {
        navigator.mediaDevices.getUserMedia({ audio: true })
          .then(stream => {
            audioContextRef.current = new AudioContext();
            analyserRef.current = audioContextRef.current.createAnalyser();
            const source = audioContextRef.current.createMediaStreamSource(stream);
            source.connect(analyserRef.current);
            
            analyserRef.current.fftSize = 256;
            const bufferLength = analyserRef.current.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);

            const draw = () => {
              if (!isListening) return;
              
              requestAnimationFrame(draw);
              analyserRef.current!.getByteFrequencyData(dataArray);

              ctx!.fillStyle = 'rgba(0, 0, 0, 0.1)';
              ctx!.fillRect(0, 0, canvas.width, canvas.height);

              const barWidth = (canvas.width / bufferLength) * 2.5;
              let barHeight;
              let x = 0;

              for (let i = 0; i < bufferLength; i++) {
                barHeight = (dataArray[i] / 255) * canvas.height;

                const r = barHeight + 25 * (i / bufferLength);
                const g = 250 * (i / bufferLength);
                const b = 50;

                ctx!.fillStyle = `rgb(${r},${g},${b})`;
                ctx!.fillRect(x, canvas.height - barHeight, barWidth, barHeight);

                x += barWidth + 1;
              }
            };

            draw();
          })
          .catch(err => {
            console.error('Error accessing microphone:', err);
            setError('Microphone access denied');
          });
      }
    }
  }, [isListening]);

  const startListening = useCallback(() => {
    if (recognitionRef.current && !isListening && !isProcessing) {
      setTranscript('');
      setError('');
      recognitionRef.current.start();
    }
  }, [isListening, isProcessing]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
    }
  }, [isListening]);

  const processVoiceInput = async (text: string) => {
    if (!text.trim() || isProcessing) return;

    setIsProcessing(true);
    stopListening();

    // Add user message to conversation
    const userMessage = {
      type: 'user' as const,
      text: text,
      timestamp: new Date()
    };
    setConversation(prev => [...prev, userMessage]);

    try {
      const response = await fetch('http://localhost:8000/api/agents/coordinate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task: text,
          context: { 
            session_id: sessionId,
            input_method: 'voice',
            real_time: true
          },
          agents: ['researcher', 'analyzer']
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const result = await response.json();
      const aiText = result.results?.summary || result.summary || 'I processed your request successfully!';
      
      setAiResponse(aiText);

      // Add AI response to conversation
      const aiMessage = {
        type: 'ai' as const,
        text: aiText,
        timestamp: new Date()
      };
      setConversation(prev => [...prev, aiMessage]);

      // Speak the response immediately
      speakText(aiText);

    } catch (error) {
      const errorMsg = `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}`;
      setError(errorMsg);
      speakText(errorMsg);
    } finally {
      setIsProcessing(false);
    }
  };

  const speakText = (text: string) => {
    if (!synthRef.current || !text.trim()) return;

    synthRef.current.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    const voices = synthRef.current.getVoices();
    const englishVoice = voices.find(voice => voice.lang.startsWith('en')) || voices[0];
    
    if (englishVoice) {
      utterance.voice = englishVoice;
    }
    
    utterance.rate = 0.9;
    utterance.pitch = 1.0;
    utterance.volume = 0.8;

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => {
      setIsSpeaking(false);
      // Auto-start listening again for continuous conversation
      setTimeout(() => {
        if (!isProcessing) {
          startListening();
        }
      }, 500);
    };
    utterance.onerror = () => setIsSpeaking(false);

    setIsSpeaking(true);
    synthRef.current.speak(utterance);
  };

  const stopSpeaking = () => {
    if (synthRef.current) {
      synthRef.current.cancel();
      setIsSpeaking(false);
    }
  };

  const toggleVoiceChat = () => {
    if (isListening) {
      stopListening();
    } else if (isSpeaking) {
      stopSpeaking();
    } else {
      startListening();
    }
  };

  if (!voiceEnabled) {
    return (
      <div className="p-8 text-center">
        <div className="w-24 h-24 mx-auto mb-4 bg-red-500/20 rounded-full flex items-center justify-center">
          <svg className="w-12 h-12 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636" />
          </svg>
        </div>
        <h3 className="text-xl font-semibold text-white mb-2">Voice Not Available</h3>
        <p className="text-white/70">Please use Chrome, Edge, or Safari for voice features</p>
      </div>
    );
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-white mb-2">
          Real-time Voice AI
        </h2>
        <p className="text-white/70">
          Speak naturally - I'll respond instantly with voice
        </p>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-6 p-4 bg-red-500/20 border border-red-500/30 rounded-lg">
          <p className="text-red-300 text-sm">{error}</p>
        </div>
      )}

      {/* Main Voice Interface */}
      <div className="flex flex-col items-center space-y-8">
        {/* Voice Visualizer */}
        <div className="relative">
          <canvas
            ref={canvasRef}
            width={300}
            height={150}
            className={`rounded-lg border-2 ${
              isListening ? 'border-red-400' : 'border-white/20'
            } bg-black/20`}
          />
          {!isListening && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-white/50 text-center">
                <svg className="w-12 h-12 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
                </svg>
                <p className="text-sm">Voice Visualizer</p>
              </div>
            </div>
          )}
        </div>

        {/* Main Control Button */}
        <button
          onClick={toggleVoiceChat}
          disabled={isProcessing}
          className={`w-32 h-32 rounded-full flex items-center justify-center text-white font-bold text-lg transition-all duration-300 transform ${
            isListening
              ? 'bg-red-500 hover:bg-red-600 animate-pulse scale-110 shadow-2xl shadow-red-500/50'
              : isSpeaking
              ? 'bg-green-500 hover:bg-green-600 animate-pulse scale-110 shadow-2xl shadow-green-500/50'
              : isProcessing
              ? 'bg-blue-500 animate-spin scale-110 shadow-2xl shadow-blue-500/50'
              : 'bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 hover:scale-105 shadow-xl'
          } disabled:opacity-50`}
        >
          {isListening ? (
            <div className="text-center">
              <svg className="w-12 h-12 mx-auto mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10h6v4H9z" />
              </svg>
              <div className="text-xs">STOP</div>
            </div>
          ) : isSpeaking ? (
            <div className="text-center">
              <svg className="w-12 h-12 mx-auto mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
              </svg>
              <div className="text-xs">SPEAKING</div>
            </div>
          ) : isProcessing ? (
            <div className="text-center">
              <svg className="w-12 h-12 mx-auto mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <div className="text-xs">THINKING</div>
            </div>
          ) : (
            <div className="text-center">
              <svg className="w-12 h-12 mx-auto mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
              <div className="text-xs">TALK</div>
            </div>
          )}
        </button>

        {/* Status Text */}
        <div className="text-center">
          <p className="text-white/90 font-medium">
            {isListening ? 'Listening... Speak now!' :
             isSpeaking ? 'AI is speaking...' :
             isProcessing ? 'Processing your request...' :
             'Click to start voice conversation'}
          </p>
          {transcript && (
            <p className="text-blue-300 text-sm mt-2 italic">
              "{transcript}"
            </p>
          )}
        </div>
      </div>

      {/* Conversation History */}
      {conversation.length > 0 && (
        <div className="mt-8 max-h-64 overflow-y-auto space-y-3">
          <h3 className="text-white font-semibold mb-3">Conversation</h3>
          {conversation.slice(-6).map((message, index) => (
            <div
              key={index}
              className={`p-3 rounded-lg ${
                message.type === 'user'
                  ? 'bg-blue-500/20 border-l-4 border-blue-400 ml-8'
                  : 'bg-green-500/20 border-l-4 border-green-400 mr-8'
              }`}
            >
              <div className="flex justify-between items-start mb-1">
                <span className="text-xs font-medium text-white/70">
                  {message.type === 'user' ? 'You' : 'AI Assistant'}
                </span>
                <span className="text-xs text-white/50">
                  {message.timestamp.toLocaleTimeString()}
                </span>
              </div>
              <p className="text-white text-sm">{message.text}</p>
            </div>
          ))}
        </div>
      )}

      {/* Quick Actions */}
      <div className="mt-8 flex justify-center space-x-4">
        <button
          onClick={() => setConversation([])}
          className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg text-sm font-medium transition-colors"
        >
          Clear Chat
        </button>
        <button
          onClick={stopSpeaking}
          disabled={!isSpeaking}
          className="px-4 py-2 bg-orange-500/20 hover:bg-orange-500/30 text-orange-300 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
        >
          Stop Speaking
        </button>
      </div>

      {/* Instructions */}
      <div className="mt-8 p-4 bg-white/5 rounded-lg">
        <h4 className="text-white font-medium mb-2">How to Use:</h4>
        <ul className="text-white/70 text-sm space-y-1">
          <li>• Click the microphone and speak your question</li>
          <li>• AI will respond with both text and voice</li>
          <li>• Conversation continues automatically</li>
          <li>• Ask about research, analysis, or any topic</li>
        </ul>
      </div>
    </div>
  );
}