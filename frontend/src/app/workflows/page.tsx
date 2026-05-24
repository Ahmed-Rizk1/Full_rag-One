export default function WorkflowsPage() {
  return (
    <div className="p-8 h-full flex flex-col">
      <header className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Workflows</h1>
          <p className="text-gray-400 mt-1">Automate tasks with chained agent execution</p>
        </div>
        <button className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors shadow-lg shadow-blue-500/20">
          New Workflow
        </button>
      </header>
      
      <div className="flex-1 rounded-2xl border border-white/10 bg-white/5 flex items-center justify-center backdrop-blur-sm">
        <p className="text-gray-500">No active workflows running.</p>
      </div>
    </div>
  );
}
