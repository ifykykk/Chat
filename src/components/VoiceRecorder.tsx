import React, { useEffect, useState } from 'react';
import { Mic, Square } from 'lucide-react';

interface VoiceRecorderProps {
  onTranscript: (transcript: string) => void;
  onStop: () => void;
}

export const VoiceRecorder: React.FC<VoiceRecorderProps> = ({ onTranscript, onStop }) => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [recognition, setRecognition] = useState<SpeechRecognition | null>(null);

  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognitionInstance = new SpeechRecognition();
      
      recognitionInstance.continuous = true;
      recognitionInstance.interimResults = true;
      recognitionInstance.lang = 'en-US';

      recognitionInstance.onstart = () => {
        setIsListening(true);
      };

      recognitionInstance.onresult = (event) => {
        let finalTranscript = '';
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }

        setTranscript(finalTranscript + interimTranscript);
        
        if (finalTranscript) {
          onTranscript(finalTranscript);
          handleStop();
        }
      };

      recognitionInstance.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        handleStop();
      };

      recognitionInstance.onend = () => {
        setIsListening(false);
      };

      setRecognition(recognitionInstance);
      recognitionInstance.start();

      return () => {
        recognitionInstance.stop();
      };
    } else {
      alert('Speech recognition is not supported in this browser.');
      onStop();
    }
  }, []);

  const handleStop = () => {
    if (recognition) {
      recognition.stop();
    }
    setIsListening(false);
    onStop();
  };

  return (
    <div className="absolute bottom-full mb-2 left-0 bg-white border border-gray-200 rounded-lg p-3 shadow-lg min-w-64">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
          <span className="text-sm font-medium">Listening...</span>
        </div>
        <button
          onClick={handleStop}
          className="p-1 text-gray-500 hover:text-gray-700"
        >
          <Square size={16} />
        </button>
      </div>
      
      <div className="text-sm text-gray-600 min-h-8">
        {transcript || 'Speak now...'}
      </div>
      
      <div className="mt-2 text-xs text-gray-500">
        Tip: Speak clearly and pause when finished
      </div>
    </div>
  );
};

// Extend Window interface for TypeScript
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}