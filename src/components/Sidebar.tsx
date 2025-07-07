import React, { useState } from 'react';
import { ChatSession } from '../types';
import { Plus, MessageSquare, Settings, Download, Trash2, Edit2 } from 'lucide-react';

interface SidebarProps {
  sessions: ChatSession[];
  currentSessionId?: string;
  onNewSession: () => void;
  onSelectSession: (sessionId: string) => void;
  onDeleteSession: (sessionId: string) => void;
  onRenameSession: (sessionId: string, newTitle: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  sessions,
  currentSessionId,
  onNewSession,
  onSelectSession,
  onDeleteSession,
  onRenameSession
}) => {
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');

  const handleStartEdit = (session: ChatSession) => {
    setEditingSessionId(session.id);
    setEditingTitle(session.title);
  };

  const handleFinishEdit = (sessionId: string) => {
    if (editingTitle.trim()) {
      onRenameSession(sessionId, editingTitle.trim());
    }
    setEditingSessionId(null);
    setEditingTitle('');
  };

  return (
    <div className="w-80 bg-gray-50 border-r border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h1 className="text-xl font-bold text-gray-800 mb-2">MOSDAC AI</h1>
        <p className="text-sm text-gray-600">Meteorological & Oceanographic Data Assistant</p>
      </div>

      {/* New Chat Button */}
      <div className="p-4">
        <button
          onClick={onNewSession}
          className="w-full flex items-center justify-center px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
        >
          <Plus size={18} className="mr-2" />
          New Chat
        </button>
      </div>

      {/* Sessions List */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-4 pt-0">
          <h2 className="text-sm font-medium text-gray-700 mb-3">Recent Conversations</h2>
          <div className="space-y-2">
            {sessions.map((session) => (
              <div
                key={session.id}
                className={`group flex items-center p-3 rounded-lg cursor-pointer transition-colors ${
                  currentSessionId === session.id
                    ? 'bg-blue-100 border-blue-200'
                    : 'hover:bg-gray-100'
                }`}
                onClick={() => onSelectSession(session.id)}
              >
                <MessageSquare size={16} className="text-gray-500 mr-3 flex-shrink-0" />
                
                <div className="flex-1 min-w-0">
                  {editingSessionId === session.id ? (
                    <input
                      type="text"
                      value={editingTitle}
                      onChange={(e) => setEditingTitle(e.target.value)}
                      onBlur={() => handleFinishEdit(session.id)}
                      onKeyPress={(e) => e.key === 'Enter' && handleFinishEdit(session.id)}
                      className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                      autoFocus
                    />
                  ) : (
                    <>
                      <div className="text-sm font-medium text-gray-800 truncate">
                        {session.title}
                      </div>
                      <div className="text-xs text-gray-500">
                        {session.updatedAt.toLocaleDateString()}
                      </div>
                    </>
                  )}
                </div>

                <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleStartEdit(session);
                    }}
                    className="p-1 text-gray-500 hover:text-gray-700"
                  >
                    <Edit2 size={14} />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteSession(session.id);
                    }}
                    className="p-1 text-gray-500 hover:text-red-500"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-200">
        <div className="space-y-2">
          <button className="w-full flex items-center px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
            <Download size={16} className="mr-2" />
            Export Data
          </button>
          <button className="w-full flex items-center px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
            <Settings size={16} className="mr-2" />
            Settings
          </button>
        </div>
      </div>
    </div>
  );
};