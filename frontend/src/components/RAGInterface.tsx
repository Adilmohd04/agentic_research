'use client';

import { useState, useRef } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { 
  Upload, 
  Search, 
  FileText, 
  Brain, 
  Sparkles, 
  MessageSquare,
  Download,
  Trash2,
  Loader2,
  CheckCircle,
  AlertCircle
} from 'lucide-react';

interface Document {
  id: string;
  filename: string;
  file_type: string;
  chunks: number;
  uploaded_at: string;
  file_size?: number;
}

interface SearchResult {
  id: string;
  title: string;
  content: string;
  source: string;
  confidence: number;
  relevance: number;
}

interface RAGResponse {
  answer: string;
  sources: SearchResult[];
  confidence: number;
  model_used?: string;
  tokens_used?: number;
  search_results_count?: number;
}

export default function RAGInterface() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [question, setQuestion] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [response, setResponse] = useState<RAGResponse | null>(null);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [isAsking, setIsAsking] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 5000);
  };

  const loadDocuments = async () => {
    try {
      const response = await fetch('/api/rag/documents');
      if (response.ok) {
        const data = await response.json();
        setDocuments(data.documents || []);
      }
    } catch (error) {
      console.error('Failed to load documents:', error);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/rag/upload', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        showMessage('success', `Document "${file.name}" uploaded successfully! Created ${result.chunks_created} chunks.`);
        loadDocuments();
      } else {
        const error = await response.json();
        showMessage('error', error.detail || 'Failed to upload document');
      }
    } catch (error) {
      showMessage('error', 'Upload failed. Please try again.');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    try {
      const response = await fetch('/api/rag/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery, max_results: 5 }),
      });

      if (response.ok) {
        const data = await response.json();
        setSearchResults(data.documents || []);
        showMessage('success', `Found ${data.documents?.length || 0} relevant documents`);
      } else {
        showMessage('error', 'Search failed');
      }
    } catch (error) {
      showMessage('error', 'Search failed. Please try again.');
    } finally {
      setIsSearching(false);
    }
  };

  const handleAskQuestion = async () => {
    if (!question.trim()) return;

    setIsAsking(true);
    try {
      const response = await fetch('/api/rag/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          question: question,
          max_context_docs: 5 
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setResponse(data);
        showMessage('success', 'Question answered successfully!');
      } else {
        const error = await response.json();
        showMessage('error', error.detail || 'Failed to get answer');
      }
    } catch (error) {
      showMessage('error', 'Failed to get answer. Please try again.');
    } finally {
      setIsAsking(false);
    }
  };

  const handleDeleteDocument = async (documentId: string) => {
    try {
      const response = await fetch(`/api/rag/documents/${documentId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        showMessage('success', 'Document deleted successfully');
        loadDocuments();
      } else {
        showMessage('error', 'Failed to delete document');
      }
    } catch (error) {
      showMessage('error', 'Delete failed. Please try again.');
    }
  };

  // Load documents on component mount
  React.useEffect(() => {
    loadDocuments();
  }, []);

  return (
    <div className="h-full bg-gradient-to-br from-slate-50 to-blue-50 p-6 overflow-auto">
      <div className="max-w-6xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold gradient-text flex items-center justify-center gap-3">
            <Brain className="h-8 w-8" />
            RAG Knowledge System
          </h1>
          <p className="text-slate-600">Upload documents, search knowledge, and ask intelligent questions</p>
        </div>

        {/* Message */}
        {message && (
          <div className={`p-4 rounded-lg flex items-center gap-2 ${
            message.type === 'success' 
              ? 'bg-green-50 text-green-800 border border-green-200' 
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}>
            {message.type === 'success' ? (
              <CheckCircle className="w-5 h-5" />
            ) : (
              <AlertCircle className="w-5 h-5" />
            )}
            <span>{message.text}</span>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Left Column - Upload & Documents */}
          <div className="space-y-6">
            
            {/* Document Upload */}
            <Card className="glass">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="h-5 w-5" />
                  Upload Documents
                </CardTitle>
                <CardDescription>
                  Upload PDF, DOCX, TXT, MD, or HTML files to build your knowledge base
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,.docx,.doc,.txt,.md,.html,.htm"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                  <Button
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isUploading}
                    className="w-full"
                    size="lg"
                  >
                    {isUploading ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Uploading...
                      </>
                    ) : (
                      <>
                        <Upload className="h-4 w-4 mr-2" />
                        Choose File to Upload
                      </>
                    )}
                  </Button>
                  <p className="text-xs text-muted-foreground text-center">
                    Supported formats: PDF, DOCX, TXT, Markdown, HTML
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Document Library */}
            <Card className="glass">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Document Library ({documents.length})
                </CardTitle>
                <CardDescription>
                  Manage your uploaded documents
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {documents.length === 0 ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <FileText className="h-12 w-12 mx-auto mb-2 opacity-50" />
                      <p>No documents uploaded yet</p>
                      <p className="text-sm">Upload your first document to get started</p>
                    </div>
                  ) : (
                    documents.map((doc) => (
                      <div key={doc.id} className="flex items-center justify-between p-3 bg-white/50 rounded-lg border">
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-sm truncate">{doc.filename}</p>
                          <p className="text-xs text-muted-foreground">
                            {doc.file_type} • {doc.chunks} chunks
                          </p>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDeleteDocument(doc.id)}
                          className="text-red-500 hover:text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Search & Ask */}
          <div className="space-y-6">
            
            {/* Document Search */}
            <Card className="glass">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Search className="h-5 w-5" />
                  Search Documents
                </CardTitle>
                <CardDescription>
                  Find relevant information in your documents
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex gap-2">
                    <Input
                      placeholder="Search your documents..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                    />
                    <Button onClick={handleSearch} disabled={isSearching}>
                      {isSearching ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Search className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                  
                  {searchResults.length > 0 && (
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {searchResults.map((result, index) => (
                        <div key={index} className="p-3 bg-white/50 rounded-lg border text-sm">
                          <div className="font-medium text-blue-600 mb-1">{result.title}</div>
                          <p className="text-muted-foreground line-clamp-2">{result.content}</p>
                          <div className="flex justify-between items-center mt-2 text-xs text-muted-foreground">
                            <span>{result.source}</span>
                            <span>Confidence: {Math.round(result.confidence * 100)}%</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* AI Question Answering */}
            <Card className="glass">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5" />
                  Ask AI Questions
                </CardTitle>
                <CardDescription>
                  Get intelligent answers based on your documents
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex gap-2">
                    <Input
                      placeholder="Ask a question about your documents..."
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleAskQuestion()}
                    />
                    <Button onClick={handleAskQuestion} disabled={isAsking}>
                      {isAsking ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <MessageSquare className="h-4 w-4" />
                      )}
                    </Button>
                  </div>

                  {response && (
                    <div className="space-y-4">
                      <div className="p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border">
                        <div className="flex items-center gap-2 mb-2">
                          <Brain className="h-4 w-4 text-blue-600" />
                          <span className="font-medium text-blue-900">AI Answer</span>
                          {response.model_used && (
                            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                              {response.model_used}
                            </span>
                          )}
                        </div>
                        <p className="text-gray-800 whitespace-pre-wrap">{response.answer}</p>
                        
                        {response.tokens_used && (
                          <div className="mt-2 text-xs text-muted-foreground">
                            Tokens used: {response.tokens_used} • Sources: {response.search_results_count}
                          </div>
                        )}
                      </div>

                      {response.sources && response.sources.length > 0 && (
                        <div>
                          <h4 className="font-medium mb-2 flex items-center gap-2">
                            <FileText className="h-4 w-4" />
                            Sources ({response.sources.length})
                          </h4>
                          <div className="space-y-2 max-h-48 overflow-y-auto">
                            {response.sources.map((source, index) => (
                              <div key={index} className="p-3 bg-white/70 rounded-lg border text-sm">
                                <div className="font-medium text-green-600 mb-1">{source.title}</div>
                                <p className="text-muted-foreground line-clamp-2">{source.content_preview}</p>
                                <div className="flex justify-between items-center mt-2 text-xs text-muted-foreground">
                                  <span>{source.source}</span>
                                  <span>Confidence: {Math.round(source.confidence * 100)}%</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}