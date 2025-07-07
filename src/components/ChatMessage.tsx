import React from 'react';
import { Message } from '../types';
import { Bot, User, Clock, ExternalLink, Tag } from 'lucide-react';

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.sender === 'user';
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6`}>
      <div className={`flex max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 ${isUser ? 'ml-3' : 'mr-3'}`}>
          <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
            isUser 
              ? 'bg-blue-500 text-white' 
              : 'bg-gradient-to-br from-emerald-500 to-teal-600 text-white'
          }`}>
            {isUser ? <User size={20} /> : <Bot size={20} />}
          </div>
        </div>
        
        {/* Message Content */}
        <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
          <div className={`px-4 py-3 rounded-2xl shadow-sm ${
            isUser 
              ? 'bg-blue-500 text-white' 
              : 'bg-white border border-gray-200 text-gray-800'
          }`}>
            <div className="whitespace-pre-wrap text-sm leading-relaxed">
              {message.text}
            </div>
          </div>
          
          {/* Metadata */}
          <div className="flex items-center mt-2 text-xs text-gray-500 space-x-3">
            <div className="flex items-center">
              <Clock size={12} className="mr-1" />
              {message.timestamp.toLocaleTimeString()}
            </div>
            {message.confidence && (
              <div className="flex items-center">
                <span className="mr-1">Confidence:</span>
                <span className={`font-medium ${
                  message.confidence > 0.8 ? 'text-green-600' : 
                  message.confidence > 0.6 ? 'text-yellow-600' : 'text-red-600'
                }`}>
                  {Math.round(message.confidence * 100)}%
                </span>
              </div>
            )}
          </div>
          
          {/* Sources */}
          {message.sources && message.sources.length > 0 && (
            <div className="mt-3 space-y-2">
              <div className="text-xs font-medium text-gray-600">Sources:</div>
              {message.sources.map((source, index) => (
                <div key={index} className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900 mb-1">
                        {source.title}
                      </div>
                      <div className="text-xs text-gray-600 mb-2">
                        {source.content.substring(0, 100)}...
                      </div>
                      <div className="text-xs text-blue-600 font-medium">
                        Relevance: {Math.round(source.relevance * 100)}%
                      </div>
                    </div>
                    <a
                      href={source.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="ml-2 text-blue-500 hover:text-blue-700"
                    >
                      <ExternalLink size={14} />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          )}
          
          {/* Entities */}
          {message.entities && message.entities.length > 0 && (
            <div className="mt-3">
              <div className="text-xs font-medium text-gray-600 mb-2">Entities:</div>
              <div className="flex flex-wrap gap-1">
                {message.entities.map((entity, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800"
                  >
                    <Tag size={10} className="mr-1" />
                    {entity.text}
                    <span className="ml-1 text-blue-600">
                      ({entity.label})
                    </span>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};