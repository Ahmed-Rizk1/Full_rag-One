'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth';
import { fetchApi } from '@/lib/api';
import { 
  LogOut, 
  User, 
  Settings as SettingsIcon, 
  Key, 
  Eye, 
  EyeOff, 
  Save, 
  CheckCircle2, 
  AlertCircle, 
  Loader2 
} from 'lucide-react';

export default function SettingsPage() {
  const { user, logout, reloadUser } = useAuth();

  const [provider, setProvider] = useState<string>('groq');
  const [openaiKey, setOpenaiKey] = useState<string>('');
  const [groqKey, setGroqKey] = useState<string>('');

  // Visibility toggles
  const [showOpenai, setShowOpenai] = useState<boolean>(false);
  const [showGroq, setShowGroq] = useState<boolean>(false);

  // Status states
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [successMsg, setSuccessMsg] = useState<string>('');
  const [errorMsg, setErrorMsg] = useState<string>('');

  // Initialize values when user state loads
  useEffect(() => {
    if (user) {
      if (user.preferred_provider) {
        setProvider(user.preferred_provider);
      }
    }
  }, [user]);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setSuccessMsg('');
    setErrorMsg('');

    try {
      const payload: Record<string, any> = {
        preferred_provider: provider,
      };

      // Only send keys if the user typed something in them
      if (openaiKey.trim()) {
        payload.openai_api_key = openaiKey.trim();
      }
      if (groqKey.trim()) {
        payload.groq_api_key = groqKey.trim();
      }

      const res = await fetchApi('/auth/settings', {
        method: 'PUT',
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'Failed to update settings');
      }

      setSuccessMsg('Settings saved and API keys verified successfully!');
      setOpenaiKey('');
      setGroqKey('');
      await reloadUser();
    } catch (err: any) {
      setErrorMsg(err.message || 'An unexpected error occurred.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="p-8 h-full flex flex-col max-w-2xl overflow-y-auto">
      <header className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <SettingsIcon className="text-blue-500 animate-spin-slow" /> Settings
        </h1>
        <p className="text-gray-400 mt-1">Manage your account credentials and preferred LLM models</p>
      </header>

      <div className="space-y-6 pb-12">
        {/* Main Settings Form */}
        <form onSubmit={handleSave} className="p-6 bg-white/5 border border-white/10 rounded-2xl space-y-6 backdrop-blur-md">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2 border-b border-white/10 pb-3">
            <Key size={18} className="text-blue-400" /> SaaS API Integration
          </h2>

          {/* Success Banner */}
          {successMsg && (
            <div className="flex items-center gap-3 p-4 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-xl text-sm transition-all animate-fade-in">
              <CheckCircle2 size={18} className="shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          {/* Error Banner */}
          {errorMsg && (
            <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl text-sm transition-all animate-fade-in">
              <AlertCircle size={18} className="shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Preferred Provider Selection */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-300 block">Preferred LLM Provider</label>
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="w-full bg-zinc-900 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all"
            >
              <option value="groq">Groq (Llama 3 / DeepSeek R1)</option>
              <option value="openai">OpenAI (GPT-4o / GPT-4o-mini)</option>
            </select>
            <p className="text-xs text-gray-500">Select which API service to orchestrate your agents.</p>
          </div>

          {/* OpenAI API Key */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label className="text-sm font-medium text-gray-300">OpenAI API Key</label>
              {user?.has_openai_key && (
                <span className="text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/10">
                  Configured
                </span>
              )}
            </div>
            <div className="relative">
              <input
                type={showOpenai ? 'text' : 'password'}
                value={openaiKey}
                onChange={(e) => setOpenaiKey(e.target.value)}
                placeholder={user?.has_openai_key ? '••••••••••••••••••••••••••••••••' : 'sk-...'}
                className="w-full bg-zinc-900 border border-white/10 rounded-xl pl-4 pr-11 py-2.5 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all placeholder:text-gray-600"
              />
              <button
                type="button"
                onClick={() => setShowOpenai(!showOpenai)}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-200 transition-colors"
              >
                {showOpenai ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {/* Groq API Key */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label className="text-sm font-medium text-gray-300">Groq API Key</label>
              {user?.has_groq_key && (
                <span className="text-[11px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/10">
                  Configured
                </span>
              )}
            </div>
            <div className="relative">
              <input
                type={showGroq ? 'text' : 'password'}
                value={groqKey}
                onChange={(e) => setGroqKey(e.target.value)}
                placeholder={user?.has_groq_key ? '••••••••••••••••••••••••••••••••' : 'gsk_...'}
                className="w-full bg-zinc-900 border border-white/10 rounded-xl pl-4 pr-11 py-2.5 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all placeholder:text-gray-600"
              />
              <button
                type="button"
                onClick={() => setShowGroq(!showGroq)}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-200 transition-colors"
              >
                {showGroq ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isSaving}
            className="flex items-center justify-center gap-2 w-full py-2.5 bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 text-sm font-semibold text-white rounded-xl shadow-lg shadow-blue-500/10 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSaving ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Validating & Saving Key...
              </>
            ) : (
              <>
                <Save size={16} />
                Save API Configuration
              </>
            )}
          </button>
        </form>

        {/* Account Details */}
        <div className="p-6 bg-white/5 border border-white/10 rounded-2xl space-y-4">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2 border-b border-white/10 pb-3">
            <User size={18} className="text-blue-400" /> Account Profile
          </h2>
          <div>
            <label className="text-xs text-gray-500 block mb-1">Email Address</label>
            <p className="text-sm font-medium text-gray-200">{user?.email || 'user@example.com'}</p>
          </div>
          <div>
            <label className="text-xs text-gray-500 block mb-1">Membership Plan</label>
            <p className="text-sm font-medium text-blue-400">Pro Tier</p>
          </div>
        </div>

        {/* Logout */}
        <button
          onClick={logout}
          className="flex items-center gap-2 px-4 py-2.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 rounded-xl font-medium transition-colors w-full justify-center"
        >
          <LogOut size={16} />
          Sign Out of Account
        </button>
      </div>
    </div>
  );
}
