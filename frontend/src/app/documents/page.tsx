'use client';

import { useState, useEffect, useRef } from 'react';
import { fetchApi } from '@/lib/api';
import { Upload, FileText, Loader2, CheckCircle, Clock } from 'lucide-react';
import { Document } from '@/types';

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load documents on mount
  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    const res = await fetchApi('/documents/');
    if (res.ok) setDocuments(await res.json());
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const res = await fetchApi('/documents/upload', {
        method: 'POST',
        body: formData,
      });

      if (res.ok) {
        const doc = await res.json();
        setDocuments((prev) => [doc, ...prev]);
      }
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const statusIcon = (status: string) => {
    switch (status) {
      case 'ready': return <CheckCircle size={16} className="text-green-400" />;
      case 'pending': return <Clock size={16} className="text-yellow-400" />;
      case 'processing': return <Loader2 size={16} className="text-blue-400 animate-spin" />;
      default: return <Clock size={16} className="text-gray-400" />;
    }
  };

  return (
    <div className="p-8 h-full flex flex-col">
      <header className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Knowledge Base</h1>
          <p className="text-gray-400 mt-1">Manage documents for RAG processing</p>
        </div>
        <div>
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleUpload}
            accept=".txt,.pdf,.docx,.md"
            className="hidden"
            id="doc-upload"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors shadow-lg shadow-blue-500/20 disabled:opacity-50"
          >
            {uploading ? <Loader2 size={16} className="animate-spin" /> : <Upload size={16} />}
            {uploading ? 'Uploading...' : 'Upload Document'}
          </button>
        </div>
      </header>

      {documents.length === 0 ? (
        <div className="flex-1 rounded-2xl border border-white/10 bg-white/5 flex items-center justify-center backdrop-blur-sm">
          <div className="text-center space-y-3">
            <FileText size={48} className="mx-auto text-gray-600" />
            <p className="text-gray-500">No documents found. Upload one to get started.</p>
          </div>
        </div>
      ) : (
        <div className="space-y-2">
          {documents.map((doc) => (
            <div key={doc.id} className="flex items-center justify-between px-5 py-4 bg-white/5 border border-white/10 rounded-xl hover:bg-white/[.07] transition-colors">
              <div className="flex items-center gap-3">
                <FileText size={20} className="text-blue-400" />
                <div>
                  <p className="text-sm font-medium text-white">{doc.filename}</p>
                  <p className="text-xs text-gray-500">{new Date(doc.created_at).toLocaleString()}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {statusIcon(doc.status)}
                <span className="text-xs text-gray-400 capitalize">{doc.status}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
