'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { fetchApi } from '@/lib/api';
import { Check, Loader2, Bot, Shield, Globe } from 'lucide-react';

export default function PricingPage() {
  const { user, reloadUser } = useAuth();
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleUpgrade = async () => {
    setLoading(true);
    try {
      // Simulate secure Stripe/payment gateway delay
      await new Promise((resolve) => setTimeout(resolve, 1500));

      const res = await fetchApi('/auth/upgrade', {
        method: 'PUT',
      });

      if (res.ok) {
        // Refresh the context user immediately without logging out
        await reloadUser();
        alert('🎉 Payment Successful! Welcome to AI Agent OS Pro.');
        router.push('/workspace');
      } else {
        alert('Upgrade failed. Please try again.');
      }
    } catch (err) {
      console.error(err);
      alert('Upgrade error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 h-full flex flex-col max-w-4xl mx-auto justify-center">
      <header className="mb-12 text-center">
        <h1 className="text-3xl font-extrabold tracking-tight text-white">Upgrade to Pro SaaS</h1>
        <p className="text-gray-400 mt-2">Unlock unlimited workspace context, documents, and chat messages instantly.</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-stretch">
        {/* Free plan info */}
        <div className="p-8 bg-white/5 border border-white/10 rounded-2xl flex flex-col justify-between backdrop-blur-sm">
          <div>
            <h3 className="text-lg font-bold text-gray-300">Free Tier</h3>
            <p className="text-zinc-500 text-xs mt-1">Prototype & explore workflows</p>
            <div className="mt-4 flex items-baseline">
              <span className="text-3xl font-extrabold text-white">$0</span>
              <span className="text-zinc-500 text-xs ml-1">/ month</span>
            </div>
            <ul className="mt-6 space-y-3 text-sm text-zinc-300">
              <li className="flex items-center gap-2">
                <Check size={14} className="text-green-500 shrink-0" /> Limit of 3 total documents
              </li>
              <li className="flex items-center gap-2">
                <Check size={14} className="text-green-500 shrink-0" /> Limit of 10 messages/day
              </li>
              <li className="flex items-center gap-2">
                <Check size={14} className="text-green-500 shrink-0" /> Standard RAG indexing
              </li>
            </ul>
          </div>
          <div className="mt-8 text-center text-zinc-500 text-xs bg-white/5 py-2.5 rounded-xl">
            {user?.tier === 'pro' ? 'Downgraded' : 'Active Plan'}
          </div>
        </div>

        {/* Pro plan upgrade trigger */}
        <div className="p-8 bg-blue-950/20 border border-blue-500/30 rounded-2xl flex flex-col justify-between backdrop-blur-sm relative">
          <div className="absolute top-0 right-6 -translate-y-1/2 px-2.5 py-0.5 bg-blue-600 rounded-full text-[10px] font-bold tracking-wide uppercase">
            SaaS Plan
          </div>
          <div>
            <h3 className="text-lg font-bold text-blue-400">Pro SaaS License</h3>
            <p className="text-zinc-500 text-xs mt-1">Unlimited context for high performance</p>
            <div className="mt-4 flex items-baseline">
              <span className="text-3xl font-extrabold text-white">$29</span>
              <span className="text-zinc-500 text-xs ml-1">/ month</span>
            </div>
            <ul className="mt-6 space-y-3 text-sm text-zinc-300">
              <li className="flex items-center gap-2">
                <Check size={14} className="text-blue-500 shrink-0" /> Unlimited document uploads
              </li>
              <li className="flex items-center gap-2">
                <Check size={14} className="text-blue-500 shrink-0" /> Unlimited chat messages
              </li>
              <li className="flex items-center gap-2">
                <Check size={14} className="text-blue-500 shrink-0" /> Full repository diff auditing
              </li>
              <li className="flex items-center gap-2">
                <Check size={14} className="text-blue-500 shrink-0" /> Advanced workflow task execution
              </li>
            </ul>
          </div>
          <button
            onClick={handleUpgrade}
            disabled={loading || user?.tier === 'pro'}
            className="mt-8 flex items-center justify-center gap-2 w-full py-3 bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold rounded-xl transition-all shadow-lg shadow-blue-500/25 disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Processing checkout...
              </>
            ) : user?.tier === 'pro' ? (
              'You are Pro'
            ) : (
              'Upgrade to Pro'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
