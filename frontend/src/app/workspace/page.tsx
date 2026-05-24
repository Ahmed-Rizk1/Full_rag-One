'use client';

import { useState } from 'react';
import { useChat } from '@/lib/hooks/useChat';
import { Send, Bot, User } from 'lucide-react';

export default function WorkspacePage() {
  const [input, setInput] = useState('');
  const { messages, isStreaming, sendMessage } = useChat('default-session');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
    setInput('');
  };

  return (
    <div className="flex flex-col h-full">
      <header className="px-6 py-4 border-b border-white/10 backdrop-blur-md sticky top-0 z-10">
        <h1 className="text-xl font-semibold tracking-tight">AI Workspace</h1>
      </header>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center border border-blue-500/30">
                <Bot size={16} className="text-blue-400" />
              </div>
            )}
            
            <div className={`max-w-[80%] rounded-2xl p-4 ${
              msg.role === 'user' 
                ? 'bg-blue-600 text-white shadow-lg' 
                : 'bg-white/5 border border-white/10 text-gray-200'
            }`}>
              <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</p>
              
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-3 pt-3 border-t border-white/10 flex flex-wrap gap-2">
                  {msg.citations.map((c: any, i: number) => (
                    <span key={i} className="text-xs px-2 py-1 bg-white/5 rounded-md text-gray-400 border border-white/5">
                      [{i + 1}] {c.source_name}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center shadow-lg">
                <User size={16} className="text-white" />
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="p-6 bg-gradient-to-t from-zinc-950 to-transparent">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto relative group">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isStreaming}
            placeholder="Type your message..."
            className="w-full bg-white/5 border border-white/10 rounded-2xl pl-6 pr-14 py-4 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-transparent transition-all shadow-xl backdrop-blur-sm disabled:opacity-50"
          />
          <button 
            type="submit" 
            disabled={isStreaming || !input.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-xl bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-50 transition-colors shadow-md"
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
}
