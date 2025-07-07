import React, { useCallback } from 'react';
import { Upload, File, X } from 'lucide-react';

interface FileUploaderProps {
  onFileUpload: (files: FileList) => void;
  onClose: () => void;
}

export const FileUploader: React.FC<FileUploaderProps> = ({ onFileUpload, onClose }) => {
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      onFileUpload(files);
      onClose();
    }
  }, [onFileUpload, onClose]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileUpload(e.target.files);
      onClose();
    }
  };

  const supportedFormats = [
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', 
    '.csv', '.txt', '.json', '.xml'
  ];

  return (
    <div className="absolute bottom-full mb-2 left-0 bg-white border border-gray-200 rounded-lg p-4 shadow-lg w-80">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium">Upload Files</h3>
        <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
          <X size={16} />
        </button>
      </div>

      {/* Drag & Drop Area */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-400 transition-colors"
      >
        <Upload size={32} className="mx-auto text-gray-400 mb-2" />
        <p className="text-sm text-gray-600 mb-2">
          Drag & drop files here, or click to select
        </p>
        
        <input
          type="file"
          multiple
          onChange={handleFileSelect}
          accept={supportedFormats.join(',')}
          className="hidden"
          id="file-upload"
        />
        
        <label
          htmlFor="file-upload"
          className="inline-block px-4 py-2 bg-blue-500 text-white text-sm rounded-lg cursor-pointer hover:bg-blue-600"
        >
          Choose Files
        </label>
      </div>

      {/* Supported Formats */}
      <div className="mt-3">
        <div className="text-xs text-gray-600 mb-1">Supported formats:</div>
        <div className="flex flex-wrap gap-1">
          {supportedFormats.map((format) => (
            <span
              key={format}
              className="px-2 py-1 bg-gray-100 text-xs rounded"
            >
              {format}
            </span>
          ))}
        </div>
      </div>

      {/* Upload Tips */}
      <div className="mt-3 text-xs text-gray-500">
        <div>💡 Tips:</div>
        <ul className="list-disc list-inside space-y-1">
          <li>Max file size: 10MB per file</li>
          <li>Multiple files supported</li>
          <li>Files will be processed for content extraction</li>
        </ul>
      </div>
    </div>
  );
};