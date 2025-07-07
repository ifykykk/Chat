import React, { useState } from 'react';
import { X, Download, FileText, Database, Image, Calendar } from 'lucide-react';

interface ExportModalProps {
  sessions: any[];
  onClose: () => void;
  onExport: (options: any) => void;
}

export const ExportModal: React.FC<ExportModalProps> = ({ sessions, onClose, onExport }) => {
  const [exportOptions, setExportOptions] = useState({
    format: 'json',
    includeMessages: true,
    includeSources: true,
    includeEntities: true,
    includeMetadata: true,
    dateRange: 'all',
    selectedSessions: [] as string[]
  });

  const handleExport = () => {
    onExport(exportOptions);
    onClose();
  };

  const exportFormats = [
    { id: 'json', label: 'JSON', icon: Database, description: 'Machine-readable format' },
    { id: 'csv', label: 'CSV', icon: FileText, description: 'Spreadsheet compatible' },
    { id: 'pdf', label: 'PDF', icon: FileText, description: 'Printable document' },
    { id: 'html', label: 'HTML', icon: Image, description: 'Web page format' }
  ];

  const dateRanges = [
    { id: 'all', label: 'All time' },
    { id: 'today', label: 'Today' },
    { id: 'week', label: 'Last 7 days' },
    { id: 'month', label: 'Last 30 days' },
    { id: 'custom', label: 'Custom range' }
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-2xl max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-2">
            <Download size={24} className="text-blue-500" />
            <h2 className="text-xl font-semibold">Export Data</h2>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X size={24} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-96 space-y-6">
          {/* Export Format */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Export Format
            </label>
            <div className="grid grid-cols-2 gap-3">
              {exportFormats.map((format) => (
                <button
                  key={format.id}
                  onClick={() => setExportOptions(prev => ({ ...prev, format: format.id }))}
                  className={`p-3 border rounded-lg text-left transition-colors ${
                    exportOptions.format === format.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center space-x-2 mb-1">
                    <format.icon size={16} />
                    <span className="font-medium">{format.label}</span>
                  </div>
                  <div className="text-xs text-gray-600">{format.description}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Data to Include */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Data to Include
            </label>
            <div className="space-y-2">
              {[
                { key: 'includeMessages', label: 'Chat messages' },
                { key: 'includeSources', label: 'Source references' },
                { key: 'includeEntities', label: 'Extracted entities' },
                { key: 'includeMetadata', label: 'Session metadata' }
              ].map((option) => (
                <label key={option.key} className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={exportOptions[option.key as keyof typeof exportOptions] as boolean}
                    onChange={(e) => setExportOptions(prev => ({ 
                      ...prev, 
                      [option.key]: e.target.checked 
                    }))}
                    className="rounded"
                  />
                  <span className="text-sm text-gray-700">{option.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Date Range */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Date Range
            </label>
            <div className="grid grid-cols-3 gap-2">
              {dateRanges.map((range) => (
                <button
                  key={range.id}
                  onClick={() => setExportOptions(prev => ({ ...prev, dateRange: range.id }))}
                  className={`p-2 text-sm border rounded transition-colors ${
                    exportOptions.dateRange === range.id
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  {range.label}
                </button>
              ))}
            </div>
          </div>

          {/* Session Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Sessions to Export
            </label>
            <div className="max-h-32 overflow-y-auto border border-gray-200 rounded-lg">
              <div className="p-2">
                <label className="flex items-center space-x-2 mb-2">
                  <input
                    type="checkbox"
                    checked={exportOptions.selectedSessions.length === sessions.length}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setExportOptions(prev => ({ 
                          ...prev, 
                          selectedSessions: sessions.map(s => s.id) 
                        }));
                      } else {
                        setExportOptions(prev => ({ ...prev, selectedSessions: [] }));
                      }
                    }}
                    className="rounded"
                  />
                  <span className="text-sm font-medium">Select All ({sessions.length})</span>
                </label>
                
                {sessions.map((session) => (
                  <label key={session.id} className="flex items-center space-x-2 py-1">
                    <input
                      type="checkbox"
                      checked={exportOptions.selectedSessions.includes(session.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setExportOptions(prev => ({ 
                            ...prev, 
                            selectedSessions: [...prev.selectedSessions, session.id] 
                          }));
                        } else {
                          setExportOptions(prev => ({ 
                            ...prev, 
                            selectedSessions: prev.selectedSessions.filter(id => id !== session.id) 
                          }));
                        }
                      }}
                      className="rounded"
                    />
                    <span className="text-sm text-gray-700 truncate">
                      {session.title} ({session.messages?.length || 0} messages)
                    </span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Export Preview */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="text-sm font-medium text-gray-700 mb-2">Export Summary</div>
            <div className="text-sm text-gray-600 space-y-1">
              <div>Format: {exportFormats.find(f => f.id === exportOptions.format)?.label}</div>
              <div>Sessions: {exportOptions.selectedSessions.length} selected</div>
              <div>Date range: {dateRanges.find(r => r.id === exportOptions.dateRange)?.label}</div>
              <div>
                Estimated size: ~{Math.round(exportOptions.selectedSessions.length * 0.5)}MB
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200">
          <div className="text-sm text-gray-500">
            Export will be downloaded to your device
          </div>
          
          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-600 hover:text-gray-800"
            >
              Cancel
            </button>
            <button
              onClick={handleExport}
              disabled={exportOptions.selectedSessions.length === 0}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Download size={16} />
              <span>Export Data</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};