'use client';

import { useState, useEffect } from 'react';
import { fetchApi } from '@/lib/api';
import { Database, Plus, Loader2, CheckCircle, Clock, Globe } from 'lucide-react';

interface Repository {
  id: string;
  name: string;
  status: string;
  created_at: string;
}

export default function RepositoriesPage() {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [repoUrl, setRepoUrl] = useState('');
  const [branch, setBranch] = useState('main');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadRepositories();
  }, []);

  const loadRepositories = async () => {
    const res = await fetchApi('/repositories');
    if (res.ok) setRepositories(await res.json());
  };

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoUrl.trim()) return;

    setLoading(true);
    try {
      const res = await fetchApi('/repositories/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_url: repoUrl, branch }),
      });

      if (res.ok) {
        const result = await res.json();
        // Construct basic temp object to show in list immediately
        const newRepo: Repository = {
          id: result.id,
          name: repoUrl.replace(/https?:\/\/github\.com\//, ''),
          status: result.status,
          created_at: new Date().toISOString(),
        };
        setRepositories((prev) => [newRepo, ...prev]);
        setIsOpen(false);
        setRepoUrl('');
        setBranch('main');
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 h-full flex flex-col">
      <header className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Database className="text-blue-500" /> Repositories
          </h1>
          <p className="text-gray-400 mt-1">Connected codebases for the Code Agent</p>
        </div>
        <button
          onClick={() => setIsOpen(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition-colors shadow-lg shadow-blue-500/20"
        >
          <Plus size={16} /> Connect Repo
        </button>
      </header>

      {repositories.length === 0 ? (
        <div className="flex-1 rounded-2xl border border-white/10 bg-white/5 flex items-center justify-center backdrop-blur-sm">
          <p className="text-gray-500">No repositories connected.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {repositories.map((repo) => (
            <div key={repo.id} className="flex items-center justify-between px-5 py-4 bg-white/5 border border-white/10 rounded-xl hover:bg-white/[.07] transition-colors">
              <div className="flex items-center gap-3">
                <Database size={20} className="text-blue-400" />
                <div>
                  <p className="text-sm font-medium text-white">{repo.name}</p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Connected: {new Date(repo.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {repo.status === 'completed' || repo.status === 'ready' ? (
                  <CheckCircle size={16} className="text-green-400" />
                ) : repo.status === 'failed' ? (
                  <span className="w-2.5 h-2.5 rounded-full bg-red-500" />
                ) : (
                  <Loader2 size={16} className="text-blue-400 animate-spin" />
                )}
                <span className="text-xs text-gray-400 capitalize">{repo.status}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {isOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-zinc-900 border border-white/10 rounded-2xl p-6 w-full max-w-md shadow-2xl relative">
            <h3 className="text-lg font-bold text-white mb-4">Connect New Repository</h3>
            <form onSubmit={handleConnect} className="space-y-4">
              <div>
                <label className="text-xs text-gray-400 block mb-1">GitHub Repository URL</label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-500">
                    <Globe size={16} />
                  </span>
                  <input
                    type="url"
                    required
                    value={repoUrl}
                    onChange={(e) => setRepoUrl(e.target.value)}
                    placeholder="https://github.com/username/repo"
                    className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors"
                  />
                </div>
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Branch Name</label>
                <input
                  type="text"
                  required
                  value={branch}
                  onChange={(e) => setBranch(e.target.value)}
                  placeholder="main"
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
                  {loading ? 'Connecting...' : 'Connect'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
