import React, { useEffect, useRef } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatMessage } from './components/ChatMessage';
import { ChatInput } from './components/ChatInput';
import { LoadingIndicator } from './components/LoadingIndicator';
import { WelcomeScreen } from './components/WelcomeScreen';
import { SettingsModal } from './components/SettingsModal';
import { ExportModal } from './components/ExportModal';
import { useChat } from './hooks/useChat';
import { useSettings } from './hooks/useSettings';

function App() {
  const {
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
  } = useChat();

  const {
    settings,
    isSettingsOpen,
    openSettings,
    closeSettings,
    updateSettings
  } = useSettings();

  const [isExportOpen, setIsExportOpen] = React.useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [currentSession?.messages, isLoading]);

  const handleQuickStart = (query: string) => {
    if (!currentSessionId) {
      createNewSession();
    }
    sendMessage(query);
  };

  const handleFileUpload = (files: FileList) => {
    // Handle file upload functionality
    Array.from(files).forEach(file => {
      const message = `📎 Uploaded file: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
      sendMessage(message);
    });
  };

  const handleLocationShare = (location: GeolocationPosition) => {
    const { latitude, longitude } = location.coords;
    const message = `📍 Location shared: ${latitude.toFixed(4)}, ${longitude.toFixed(4)}`;
    sendMessage(message);
  };

  const handleVoiceInput = (transcript: string) => {
    sendMessage(transcript);
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <Sidebar
        sessions={sessions}
        currentSessionId={currentSessionId}
        onNewSession={createNewSession}
        onSelectSession={selectSession}
        onDeleteSession={deleteSession}
        onRenameSession={renameSession}
        onExport={() => setIsExportOpen(true)}
        onSettings={openSettings}
      />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {currentSession ? (
          <>
            {/* Chat Header */}
            <div className="bg-white border-b border-gray-200 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-gray-800">
                    {currentSession.title}
                  </h2>
                  <p className="text-sm text-gray-600">
                    {currentSession.messages.length} messages • Updated {currentSession.updatedAt.toLocaleTimeString()}
                  </p>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                    <span className="text-sm text-gray-600">Real-time Active</span>
                  </div>
                  <div className="text-xs text-gray-500">
                    API: {settings.apiEndpoint}
                  </div>
                </div>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {currentSession.messages.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="text-gray-500 mb-2">No messages yet</div>
                    <p className="text-gray-400">Start the conversation by asking a question below</p>
                  </div>
                </div>
              ) : (
                currentSession.messages.map((message) => (
                  <ChatMessage key={message.id} message={message} />
                ))
              )}
              {isLoading && <LoadingIndicator />}
              <div ref={messagesEndRef} />
            </div>

            {/* Chat Input */}
            <ChatInput 
              onSendMessage={sendMessage} 
              onFileUpload={handleFileUpload}
              onLocationShare={handleLocationShare}
              onVoiceInput={handleVoiceInput}
              isLoading={isLoading} 
              settings={settings}
            />
          </>
        ) : (
          <WelcomeScreen onQuickStart={handleQuickStart} />
        )}
      </div>

      {/* Modals */}
      {isSettingsOpen && (
        <SettingsModal
          settings={settings}
          onClose={closeSettings}
          onSave={updateSettings}
        />
      )}

      {isExportOpen && (
        <ExportModal
          sessions={sessions}
          onClose={() => setIsExportOpen(false)}
          onExport={exportData}
        />
      )}
    </div>
  );
}

export default App;