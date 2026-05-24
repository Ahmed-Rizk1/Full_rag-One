'use client';

import { useAuth } from '@/lib/auth';
import { LogOut, User, Settings as SettingsIcon } from 'lucide-react';

export default function SettingsPage() {
  const { user, logout } = useAuth();

  return (
    <div className="p-8 h-full flex flex-col max-w-2xl">
      <header className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
          <SettingsIcon className="text-blue-500" /> Settings
        </h1>
        <p className="text-gray-400 mt-1">Manage your account and app configurations</p>
      </header>

      <div className="space-y-6">
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
