export default function DocumentsPage() {
  return (
    <div className="p-8 h-full flex flex-col">
      <header className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Knowledge Base</h1>
          <p className="text-gray-400 mt-1">Manage documents for RAG processing</p>
        </div>
        <button className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg font-medium transition-colors border border-white/10">
          Upload Document
        </button>
      </header>
      
      <div className="flex-1 rounded-2xl border border-white/10 bg-white/5 flex items-center justify-center backdrop-blur-sm">
        <p className="text-gray-500">No documents found. Upload one to get started.</p>
      </div>
    </div>
  );
}
