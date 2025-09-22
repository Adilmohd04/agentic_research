/**
 * Document Upload Component for RAG System
 */

'use client';

import { useState, useCallback } from 'react';

interface DocumentUploadProps {
  onUploadComplete?: (result: any) => void;
}

export default function DocumentUpload({ onUploadComplete }: DocumentUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedFiles, setUploadedFiles] = useState<any[]>([]);
  const [dragActive, setDragActive] = useState(false);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const handleFileUpload = async (files: FileList) => {
    if (!files.length) return;

    setUploading(true);
    const results = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      setUploadProgress((i / files.length) * 100);

      try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE}/api/rag/upload`, {
          method: 'POST',
          body: formData,
        });

        if (response.ok) {
          const result = await response.json();
          results.push({
            ...result,
            filename: file.name,
            size: file.size,
            type: file.type
          });
        } else {
          const error = await response.json();
          results.push({
            filename: file.name,
            error: error.detail || 'Upload failed'
          });
        }
      } catch (error) {
        results.push({
          filename: file.name,
          error: 'Network error'
        });
      }
    }

    setUploadedFiles(prev => [...prev, ...results]);
    setUploading(false);
    setUploadProgress(0);
    
    if (onUploadComplete) {
      onUploadComplete(results);
    }
  };

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files);
    }
  }, []);

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-6">
      {/* Upload Area */}
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <div className="space-y-4">
          <div className="text-4xl">📄</div>
          <div>
            <h3 className="text-lg font-medium text-gray-900">
              Upload Documents to Knowledge Base
            </h3>
            <p className="text-sm text-gray-500 mt-1">
              Drag and drop files here, or click to select
            </p>
          </div>
          
          <div className="flex justify-center">
            <label className="cursor-pointer">
              <input
                type="file"
                multiple
                accept=".pdf,.docx,.doc,.txt,.md,.html"
                onChange={(e) => e.target.files && handleFileUpload(e.target.files)}
                className="hidden"
                disabled={uploading}
              />
              <span className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
                {uploading ? 'Uploading...' : 'Select Files'}
              </span>
            </label>
          </div>

          <div className="text-xs text-gray-400">
            Supported formats: PDF, DOCX, TXT, Markdown, HTML
          </div>
        </div>
      </div>

      {/* Upload Progress */}
      {uploading && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-blue-900">Uploading...</span>
            <span className="text-sm text-blue-700">{Math.round(uploadProgress)}%</span>
          </div>
          <div className="w-full bg-blue-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            ></div>
          </div>
        </div>
      )}

      {/* Uploaded Files */}
      {uploadedFiles.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg">
          <div className="p-4 border-b border-gray-200">
            <h4 className="font-medium text-gray-900">Recently Uploaded</h4>
          </div>
          <div className="divide-y divide-gray-200">
            {uploadedFiles.map((file, index) => (
              <div key={index} className="p-4 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="text-2xl">
                    {file.error ? '❌' : '✅'}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{file.filename}</p>
                    {file.error ? (
                      <p className="text-sm text-red-600">{file.error}</p>
                    ) : (
                      <p className="text-sm text-gray-500">
                        {file.chunks_created} chunks created • {formatFileSize(file.size || 0)}
                      </p>
                    )}
                  </div>
                </div>
                
                {!file.error && (
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">
                      Indexed
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tips */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h4 className="font-medium text-gray-900 mb-2">💡 Tips for Better Results</h4>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• Upload high-quality documents with clear text</li>
          <li>• Include diverse sources for comprehensive knowledge</li>
          <li>• Larger documents will be automatically chunked for better retrieval</li>
          <li>• The system supports multiple languages</li>
        </ul>
      </div>
    </div>
  );
}