import { useState, useCallback, useEffect } from 'react';
import { Message, ChatSession, QueryRequest } from '../types';
import { apiService } from '../services/api';
import { getMockResponse } from '../services/mockData';

export const useChat = () => {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const currentSession = sessions.find(s => s.id === currentSessionId);

  // Load sessions from localStorage on mount
  useEffect(() => {
    const savedSessions = localStorage.getItem('mosdac-sessions');
    if (savedSessions) {
      try {
        const parsed = JSON.parse(savedSessions);
        setSessions(parsed.map((s: any) => ({
          ...s,
          createdAt: new Date(s.createdAt),
          updatedAt: new Date(s.updatedAt),
          messages: s.messages.map((m: any) => ({
            ...m,
            timestamp: new Date(m.timestamp)
          }))
        })));
      } catch (error) {
        console.error('Error loading sessions:', error);
      }
    }
  }, []);

  // Save sessions to localStorage whenever sessions change
  useEffect(() => {
    if (sessions.length > 0) {
      localStorage.setItem('mosdac-sessions', JSON.stringify(sessions));
    }
  }, [sessions]);

  const createNewSession = useCallback(() => {
    const newSession: ChatSession = {
      id: Date.now().toString(),
      title: 'New Chat',
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date()
    };
    
    setSessions(prev => [newSession, ...prev]);
    setCurrentSessionId(newSession.id);
    return newSession;
  }, []);

  const selectSession = useCallback((sessionId: string) => {
    setCurrentSessionId(sessionId);
  }, []);

  const deleteSession = useCallback((sessionId: string) => {
    setSessions(prev => prev.filter(s => s.id !== sessionId));
    if (currentSessionId === sessionId) {
      setCurrentSessionId(null);
    }
  }, [currentSessionId]);

  const renameSession = useCallback((sessionId: string, newTitle: string) => {
    setSessions(prev => prev.map(s => 
      s.id === sessionId 
        ? { ...s, title: newTitle, updatedAt: new Date() }
        : s
    ));
  }, []);

  const sendMessage = useCallback(async (text: string, location?: any, files?: FileList) => {
    let sessionId = currentSessionId;
    
    if (!sessionId) {
      const newSession = createNewSession();
      sessionId = newSession.id;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      text,
      sender: 'user',
      timestamp: new Date()
    };

    // Add user message
    setSessions(prev => prev.map(session => 
      session.id === sessionId
        ? {
            ...session,
            messages: [...session.messages, userMessage],
            updatedAt: new Date(),
            title: session.messages.length === 0 ? text.slice(0, 50) : session.title
          }
        : session
    ));

    setIsLoading(true);

    try {
      // Try real API first, fallback to mock
      let response;
      try {
        const queryRequest: QueryRequest = {
          query: text,
          sessionId: sessionId,
          location: location
        };
        
        response = await apiService.sendMessage(queryRequest);
      } catch (apiError) {
        console.warn('API unavailable, using mock response:', apiError);
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));
        response = getMockResponse(text);
      }
      
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: response.answer || response.response,
        sender: 'bot',
        timestamp: new Date(),
        sources: response.sources,
        entities: response.entities,
        confidence: response.confidence
      };

      // Add bot message
      setSessions(prev => prev.map(session => 
        session.id === sessionId
          ? {
              ...session,
              messages: [...session.messages, botMessage],
              updatedAt: new Date()
            }
          : session
      ));

    } catch (error) {
      console.error('Error sending message:', error);
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Sorry, I encountered an error processing your request. Please check your connection and try again.',
        sender: 'bot',
        timestamp: new Date(),
        confidence: 0.1
      };

      setSessions(prev => prev.map(session => 
        session.id === sessionId
          ? {
              ...session,
              messages: [...session.messages, errorMessage],
              updatedAt: new Date()
            }
          : session
      ));
    } finally {
      setIsLoading(false);
    }
  }, [currentSessionId, createNewSession]);

  const exportData = useCallback((options: any) => {
    const selectedSessions = sessions.filter(s => 
      options.selectedSessions.includes(s.id)
    );

    let exportData: any = {
      exportedAt: new Date().toISOString(),
      options: options,
      sessions: selectedSessions
    };

    // Filter data based on options
    if (!options.includeMessages) {
      exportData.sessions = exportData.sessions.map((s: any) => ({
        ...s,
        messages: []
      }));
    }

    if (!options.includeSources) {
      exportData.sessions = exportData.sessions.map((s: any) => ({
        ...s,
        messages: s.messages.map((m: any) => ({
          ...m,
          sources: undefined
        }))
      }));
    }

    if (!options.includeEntities) {
      exportData.sessions = exportData.sessions.map((s: any) => ({
        ...s,
        messages: s.messages.map((m: any) => ({
          ...m,
          entities: undefined
        }))
      }));
    }

    // Generate file based on format
    const timestamp = new Date().toISOString().split('T')[0];
    let filename = `mosdac-export-${timestamp}`;
    let content = '';
    let mimeType = '';

    switch (options.format) {
      case 'json':
        content = JSON.stringify(exportData, null, 2);
        filename += '.json';
        mimeType = 'application/json';
        break;
      
      case 'csv':
        // Convert to CSV format
        const csvRows = ['Session ID,Title,Message ID,Sender,Text,Timestamp,Confidence'];
        selectedSessions.forEach(session => {
          session.messages.forEach(message => {
            const row = [
              session.id,
              `"${session.title}"`,
              message.id,
              message.sender,
              `"${message.text.replace(/"/g, '""')}"`,
              message.timestamp.toISOString(),
              message.confidence || ''
            ];
            csvRows.push(row.join(','));
          });
        });
        content = csvRows.join('\n');
        filename += '.csv';
        mimeType = 'text/csv';
        break;
      
      case 'html':
        // Generate HTML report
        content = `
<!DOCTYPE html>
<html>
<head>
    <title>MOSDAC Chat Export</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .session { margin-bottom: 30px; border: 1px solid #ddd; padding: 15px; }
        .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .user { background: #e3f2fd; }
        .bot { background: #f5f5f5; }
        .metadata { font-size: 0.8em; color: #666; }
    </style>
</head>
<body>
    <h1>MOSDAC Chat Export</h1>
    <p>Exported on: ${new Date().toLocaleString()}</p>
    ${selectedSessions.map(session => `
        <div class="session">
            <h2>${session.title}</h2>
            <p class="metadata">Created: ${session.createdAt.toLocaleString()}</p>
            ${session.messages.map(message => `
                <div class="message ${message.sender}">
                    <strong>${message.sender === 'user' ? 'You' : 'MOSDAC AI'}:</strong>
                    <p>${message.text}</p>
                    <div class="metadata">${message.timestamp.toLocaleString()}</div>
                </div>
            `).join('')}
        </div>
    `).join('')}
</body>
</html>`;
        filename += '.html';
        mimeType = 'text/html';
        break;
      
      default:
        content = JSON.stringify(exportData, null, 2);
        filename += '.json';
        mimeType = 'application/json';
    }

    // Download file
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

  }, [sessions]);

  return {
    sessions,
    currentSession,
    currentSessionId,
    isLoading,
    createNewSession,
    selectSession,
    deleteSession,
    renameSession,
    sendMessage,
    exportData
  };
};