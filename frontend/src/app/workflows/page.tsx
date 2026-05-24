'use client';

import { useState, useEffect } from 'react';
import { fetchApi } from '@/lib/api';
import { Activity, Plus, Loader2, Play, CheckCircle, Clock } from 'lucide-react';

interface Workflow {
  id: string;
  name: string;
  status: string;
}

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState<string | null>(null);

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    const res = await fetchApi('/workflows');
    if (res.ok) setWorkflows(await res.json());
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setLoading(true);
    try {
      const res = await fetchApi('/workflows/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, steps: [] }),
      });

      if (res.ok) {
        const wf = await res.json();
        setWorkflows((prev) => [wf, ...prev]);
        setIsOpen(false);
        setName('');
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async (id: string) => {
    setExecuting(id);
    try {
      await fetchApi(`/workflows/${id}/execute`, { method: 'POST' });
      setTimeout(loadWorkflows, 1000);
    } catch (err) {
      console.error(err);
    } finally {
      setExecuting(null);
    }
  };

  return (
    <div className="p-8 h-full flex flex-col">
      <header className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Activity className="text-blue-500" /> Workflows
          </h1>
          <p className="text-gray-400 mt-1">Automate tasks with chained agent execution</p>
        </div>
        <button
          onClick={() => setIsOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors shadow-lg shadow-blue-500/20"
        >
          <Plus size={16} /> New Workflow
        </button>
      </header>

      {workflows.length === 0 ? (
        <div className="flex-1 rounded-2xl border border-white/10 bg-white/5 flex items-center justify-center backdrop-blur-sm">
          <p className="text-gray-500">No active workflows running.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {workflows.map((wf) => (
            <div key={wf.id} className="flex items-center justify-between px-5 py-4 bg-white/5 border border-white/10 rounded-xl hover:bg-white/[.07] transition-colors">
              <div className="flex items-center gap-3">
                <Activity size={20} className="text-blue-400" />
                <div>
                  <p className="text-sm font-medium text-white">{wf.name}</p>
                  <p className="text-xs text-gray-500 flex items-center gap-1.5 mt-0.5">
                    {wf.status === 'completed' ? (
                      <CheckCircle size={12} className="text-green-400" />
                    ) : (
                      <Clock size={12} className="text-yellow-400" />
                    )}
                    <span className="capitalize">{wf.status}</span>
                  </p>
                </div>
              </div>
              <button
                onClick={() => handleExecute(wf.id)}
                disabled={executing !== null}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 text-xs font-medium text-white rounded-lg transition-all"
              >
                {executing === wf.id ? (
                  <Loader2 size={12} className="animate-spin text-gray-400" />
                ) : (
                  <Play size={12} className="text-blue-400" />
                )}
                Run
              </button>
            </div>
          ))}
        </div>
      )}

      {isOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-zinc-900 border border-white/10 rounded-2xl p-6 w-full max-w-md shadow-2xl relative">
            <h3 className="text-lg font-bold text-white mb-4">Create New Workflow</h3>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="text-xs text-gray-400 block mb-1">Workflow Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Code Review Pipeline"
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors"
                />
              </div>
              <div className="flex gap-2 justify-end pt-2">
                <button
                  type="button"
                  onClick={() => setIsOpen(false)}
                  className="px-4 py-2 border border-white/10 hover:bg-white/5 rounded-xl text-sm font-medium text-gray-300 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-sm font-medium transition-colors disabled:opacity-50"
                >
                  {loading ? 'Creating...' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
