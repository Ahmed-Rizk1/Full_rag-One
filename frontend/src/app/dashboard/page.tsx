export default function DashboardPage() {
  return (
    <div className="p-8">
      <header className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight text-white">Dashboard</h1>
        <p className="text-gray-400 mt-1">Overview of your AI Workspace</p>
      </header>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 bg-white/5 border border-white/10 rounded-2xl shadow-xl backdrop-blur-sm">
          <h3 className="text-sm font-medium text-gray-400">Total Documents</h3>
          <p className="text-3xl font-bold mt-2 text-white">0</p>
        </div>
        <div className="p-6 bg-white/5 border border-white/10 rounded-2xl shadow-xl backdrop-blur-sm">
          <h3 className="text-sm font-medium text-gray-400">Active Workflows</h3>
          <p className="text-3xl font-bold mt-2 text-white">0</p>
        </div>
        <div className="p-6 bg-white/5 border border-white/10 rounded-2xl shadow-xl backdrop-blur-sm">
          <h3 className="text-sm font-medium text-gray-400">Chat Sessions</h3>
          <p className="text-3xl font-bold mt-2 text-white">0</p>
        </div>
      </div>
    </div>
  );
}
