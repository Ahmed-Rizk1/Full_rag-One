'use client';

import Link from 'next/link';
import { ArrowRight, Bot, Cpu, Database, Zap, Shield, Check } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-zinc-950 text-white flex flex-col relative overflow-hidden">
      {/* Background gradients */}
      <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-blue-500/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-10 right-1/4 w-[600px] h-[600px] bg-indigo-500/10 rounded-full blur-[140px] pointer-events-none" />

      {/* Header */}
      <header className="border-b border-white/5 backdrop-blur-md bg-zinc-950/40 sticky top-0 z-50 px-8 py-4 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <Bot className="text-blue-500 w-6 h-6" />
          <span className="font-extrabold text-lg bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-400">
            AI Agent OS
          </span>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/login" className="text-sm font-medium text-gray-400 hover:text-white transition-colors">
            Sign In
          </Link>
          <Link href="/signup" className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-medium transition-all shadow-lg shadow-blue-500/20">
            Get Started
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 max-w-6xl mx-auto px-6 py-20 flex flex-col items-center justify-center text-center space-y-8 z-10">
        <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/5 border border-white/10 rounded-full text-xs text-blue-400 font-medium">
          <Zap size={12} /> Introducing Multi-Agent Orchestration 2.0
        </div>
        
        <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-b from-white to-zinc-400 max-w-4xl leading-tight">
          Supercharge your workspace with autonomous AI agents.
        </h1>
        
        <p className="text-lg text-zinc-400 max-w-2xl font-light leading-relaxed">
          Upload documents, connect codebases, and run complex multi-agent workflows in a secure, production-grade cloud container.
        </p>

        <div className="flex flex-wrap gap-4 justify-center pt-4">
          <Link href="/signup" className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-xl transition-all shadow-xl shadow-blue-500/25">
            Launch Workspace <ArrowRight size={16} />
          </Link>
          <a href="#features" className="px-6 py-3 bg-white/5 hover:bg-white/10 border border-white/10 text-white font-medium rounded-xl transition-colors">
            View Features
          </a>
        </div>

        {/* Demo/Pitch Cards Section */}
        <section id="features" className="w-full pt-24 grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
          <div className="p-6 bg-white/5 border border-white/5 rounded-2xl backdrop-blur-lg hover:border-white/10 transition-colors">
            <Database className="text-blue-500 w-8 h-8 mb-4" />
            <h3 className="text-lg font-bold mb-2">Smart RAG Ingestion</h3>
            <p className="text-zinc-400 text-sm font-light leading-relaxed">
              Upload PDF, DOCX, or text files to build a highly responsive semantic knowledge base powered by vectorized hybrid search.
            </p>
          </div>
          <div className="p-6 bg-white/5 border border-white/5 rounded-2xl backdrop-blur-lg hover:border-white/10 transition-colors">
            <Cpu className="text-blue-500 w-8 h-8 mb-4" />
            <h3 className="text-lg font-bold mb-2">Multi-Agent Orchestrator</h3>
            <p className="text-zinc-400 text-sm font-light leading-relaxed">
              LangGraph-based orchestration intelligently routes intent, schedules task lists, and coordinates agent handoffs.
            </p>
          </div>
          <div className="p-6 bg-white/5 border border-white/5 rounded-2xl backdrop-blur-lg hover:border-white/10 transition-colors">
            <Shield className="text-blue-500 w-8 h-8 mb-4" />
            <h3 className="text-lg font-bold mb-2">Secure Hardening</h3>
            <p className="text-zinc-400 text-sm font-light leading-relaxed">
              All processes run inside isolated non-root containers with rate limiting and secure database connection pooling.
            </p>
          </div>
        </section>

        {/* Pricing Table Section */}
        <section className="w-full pt-28 space-y-12">
          <div className="text-center space-y-3">
            <h2 className="text-3xl font-extrabold tracking-tight">Flexible plans for scale</h2>
            <p className="text-zinc-400 font-light">Start for free or unlock unlimited limits with a commercial license.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-3xl mx-auto text-left">
            {/* Free Tier */}
            <div className="p-8 bg-zinc-900/60 border border-white/5 rounded-2xl space-y-6 flex flex-col justify-between backdrop-blur-xl">
              <div>
                <h4 className="text-lg font-bold text-gray-300">Free Tier</h4>
                <p className="text-zinc-500 text-sm font-light">Ideal for prototyping & exploration</p>
                <div className="mt-4 flex items-baseline">
                  <span className="text-3xl font-extrabold">$0</span>
                  <span className="text-zinc-500 text-sm ml-1">/ month</span>
                </div>
                <ul className="mt-6 space-y-3 text-sm text-zinc-300">
                  <li className="flex items-center gap-2 font-light">
                    <Check size={16} className="text-green-500 shrink-0" /> Up to 3 total documents
                  </li>
                  <li className="flex items-center gap-2 font-light">
                    <Check size={16} className="text-green-500 shrink-0" /> 10 daily agent messages
                  </li>
                  <li className="flex items-center gap-2 font-light">
                    <Check size={16} className="text-green-500 shrink-0" /> Standard orchestration pipelines
                  </li>
                </ul>
              </div>
              <Link href="/signup" className="block w-full text-center py-2.5 bg-white/5 hover:bg-white/10 border border-white/10 text-white text-sm font-medium rounded-xl transition-colors">
                Sign Up Now
              </Link>
            </div>

            {/* Pro Tier */}
            <div className="p-8 bg-blue-950/20 border border-blue-500/20 rounded-2xl space-y-6 flex flex-col justify-between backdrop-blur-xl relative">
              <div className="absolute top-0 right-6 -translate-y-1/2 px-2.5 py-0.5 bg-blue-600 rounded-full text-[10px] font-bold tracking-wide uppercase">
                Popular
              </div>
              <div>
                <h4 className="text-lg font-bold text-blue-400">Pro SaaS Tier</h4>
                <p className="text-zinc-500 text-sm font-light">For production operations & pipelines</p>
                <div className="mt-4 flex items-baseline">
                  <span className="text-3xl font-extrabold">$29</span>
                  <span className="text-zinc-500 text-sm ml-1">/ month</span>
                </div>
                <ul className="mt-6 space-y-3 text-sm text-zinc-300">
                  <li className="flex items-center gap-2 font-light">
                    <Check size={16} className="text-blue-500 shrink-0" /> Unlimited document uploads
                  </li>
                  <li className="flex items-center gap-2 font-light">
                    <Check size={16} className="text-blue-500 shrink-0" /> Unlimited chat messages
                  </li>
                  <li className="flex items-center gap-2 font-light">
                    <Check size={16} className="text-blue-500 shrink-0" /> High-concurrency agent workflows
                  </li>
                  <li className="flex items-center gap-2 font-light">
                    <Check size={16} className="text-blue-500 shrink-0" /> Full repository reviews & diff audits
                  </li>
                </ul>
              </div>
              <Link href="/signup" className="block w-full text-center py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-xl transition-all shadow-lg shadow-blue-500/25">
                Go Pro Now
              </Link>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8 text-center text-xs text-zinc-600 font-light">
        &copy; {new Date().getFullYear()} AI OS Workspace Corp. All rights reserved.
      </footer>
    </div>
  );
}
