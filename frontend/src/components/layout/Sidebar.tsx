'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, MessageSquare, FileText, Activity, Database, Settings, Sparkles } from 'lucide-react';
import { useAuth } from '@/lib/auth';
import { fetchApi } from '@/lib/api';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/workspace', label: 'Workspace', icon: MessageSquare },
  { href: '/documents', label: 'Documents', icon: FileText },
  { href: '/workflows', label: 'Workflows', icon: Activity },
  { href: '/repositories', label: 'Repositories', icon: Database },
  { href: '/settings', label: 'Settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();
  const [usage, setUsage] = useState<{
    tier: string;
    document_count: number;
    document_limit: number;
    message_count: number;
    message_limit: number;
  } | null>(null);

  useEffect(() => {
    if (!user) return;
    fetchApi('/auth/usage')
      .then(async (res) => {
        if (res.ok) setUsage(await res.json());
      })
      .catch((err) => console.error(err));
  }, [user, pathname]);

  return (
    <div className="w-64 border-r border-white/10 bg-zinc-950/50 flex flex-col h-full backdrop-blur-xl">
      <div className="p-6">
        <h2 className="text-lg font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-400 tracking-tight">
          AI OS Workspace
        </h2>
      </div>
      
      <nav className="flex-1 px-4 space-y-2">
        {navItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          const Icon = item.icon;
          
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                isActive 
                  ? 'bg-blue-500/10 text-blue-400 font-medium' 
                  : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
              }`}
            >
              <Icon size={18} className={isActive ? 'text-blue-400' : 'text-gray-500'} />
              <span className="text-sm">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Progress Bars for Free Tier */}
      {user && user.tier === 'free' && usage && (
        <div className="px-5 py-4 mx-4 mb-4 bg-blue-500/5 border border-blue-500/10 rounded-2xl space-y-3">
          <div className="flex justify-between items-center text-xs">
            <span className="text-gray-400">Documents</span>
            <span className="text-gray-300 font-medium">{usage.document_count} / {usage.document_limit}</span>
          </div>
          <div className="w-full bg-white/5 h-1.5 rounded-full overflow-hidden">
            <div 
              className="bg-blue-500 h-full rounded-full transition-all duration-300"
              style={{ width: `${Math.min((usage.document_count / usage.document_limit) * 100, 100)}%` }}
            />
          </div>

          <div className="flex justify-between items-center text-xs pt-1">
            <span className="text-gray-400">Messages Today</span>
            <span className="text-gray-300 font-medium">{usage.message_count} / {usage.message_limit}</span>
          </div>
          <div className="w-full bg-white/5 h-1.5 rounded-full overflow-hidden">
            <div 
              className="bg-indigo-500 h-full rounded-full transition-all duration-300"
              style={{ width: `${Math.min((usage.message_count / usage.message_limit) * 100, 100)}%` }}
            />
          </div>

          <Link
            href="/pricing"
            className="flex items-center justify-center gap-1.5 w-full py-2 mt-2 bg-gradient-to-r from-blue-500 to-indigo-500 hover:from-blue-600 hover:to-indigo-600 text-[11px] font-semibold text-white rounded-xl transition-all shadow-md shadow-blue-500/10"
          >
            <Sparkles size={12} /> Upgrade to Pro
          </Link>
        </div>
      )}
      
      <div className="p-4 border-t border-white/10">
        <div className="flex items-center gap-3 px-4 py-2">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500" />
          <div className="text-xs">
            <p className="font-medium text-gray-200">{user?.full_name || 'Guest User'}</p>
            <p className="text-gray-500 capitalize">{user?.tier || 'free'} Tier</p>
          </div>
        </div>
      </div>
    </div>
  );
}
