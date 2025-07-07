import React, { useState, useRef } from 'react';
import { Send, Mic, MapPin, Paperclip, MicOff, Upload } from 'lucide-react';
import { VoiceRecorder } from './VoiceRecorder';
import { LocationPicker } from './LocationPicker';
import { FileUploader } from './FileUploader';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  onFileUpload: (files: FileList) => void;
  onLocationShare: (location: GeolocationPosition) => void;
  onVoiceInput: (transcript: string) => void;
  isLoading: boolean;
  settings: any;
}

export const ChatInput: React.FC<ChatInputProps> = ({ 
  onSendMessage, 
  onFileUpload,
  onLocationShare,
  onVoiceInput,
  isLoading,
  settings
}) => {
  const [message, setMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [showLocationPicker, setShowLocationPicker] = useState(false);
  const [showFileUploader, setShowFileUploader] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      onSendMessage(message);
      setMessage('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
    
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileUpload(e.target.files);
      e.target.value = ''; // Reset input
    }
  };

  const handleLocationRequest = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          onLocationShare(position);
          setShowLocationPicker(false);
        },
        (error) => {
          console.error('Error getting location:', error);
          alert('Unable to get your location. Please check your browser settings.');
        }
      );
    } else {
      alert('Geolocation is not supported by this browser.');
    }
  };

  const handleVoiceToggle = () => {
    setIsRecording(!isRecording);
  };

  const suggestedQueries = [
    "What satellites does MOSDAC operate?",
    "Show me weather data for Mumbai",
    "How do I access INSAT-3D data?",
    "Ocean temperature trends in Arabian Sea",
    "Latest cyclone tracking data",
    "Monsoon forecast for this season"
  ];

  return (
    <div className="bg-white border-t border-gray-200 p-4">
      {/* Suggested Queries */}
      <div className="mb-4 flex flex-wrap gap-2">
        {suggestedQueries.map((query, index) => (
          <button
            key={index}
            onClick={() => setMessage(query)}
            className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
          >
            {query}
          </button>
        ))}
      </div>

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="flex items-end space-x-3">
        {/* File Upload */}
        <div className="relative">
          <input
            ref={fileInputRef}
            type="file"
            multiple
            onChange={handleFileSelect}
            className="hidden"
            accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.txt,.json"
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-full transition-colors"
            title="Upload files"
          >
            <Paperclip size={18} />
          </button>
        </div>

        {/* Location Share */}
        <button
          type="button"
          onClick={handleLocationRequest}
          className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-full transition-colors"
          title="Share location"
        >
          <MapPin size={18} />
        </button>

        {/* Voice Input */}
        <div className="relative">
          <button
            type="button"
            onClick={handleVoiceToggle}
            className={`p-2 rounded-full transition-colors ${
              isRecording
                ? 'bg-red-500 text-white hover:bg-red-600 animate-pulse'
                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
            }`}
            title={isRecording ? 'Stop recording' : 'Voice input'}
          >
            {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
          </button>
          
          {isRecording && (
            <VoiceRecorder
              onTranscript={onVoiceInput}
              onStop={() => setIsRecording(false)}
            />
          )}
        </div>

        {/* Message Input */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={handleTextareaChange}
            onKeyPress={handleKeyPress}
            placeholder="Ask about MOSDAC data, satellites, weather, or ocean information..."
            className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            rows={1}
            disabled={isLoading}
          />
          
          {/* Character count */}
          {message.length > 0 && (
            <div className="absolute bottom-1 right-12 text-xs text-gray-400">
              {message.length}
            </div>
          )}
        </div>

        {/* Send Button */}
        <button
          type="submit"
          disabled={!message.trim() || isLoading}
          className={`p-3 rounded-full transition-all ${
            message.trim() && !isLoading
              ? 'bg-blue-500 text-white hover:bg-blue-600 shadow-lg hover:shadow-xl'
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
        >
          <Send size={18} />
        </button>
      </form>

      {/* Real-time Status */}
      <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center space-x-4">
          <span>🔴 Live connection to MOSDAC API</span>
          <span>📡 Real-time data updates</span>
        </div>
        <div>
          Last update: {new Date().toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};