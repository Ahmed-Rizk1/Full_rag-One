'use client';

import { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/lib/auth';
import { fetchApi } from '@/lib/api';
import { Send, Bot, User, Plus } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: any[];
}

interface Conversation {
  id: string;
  title: string;
}

export default function WorkspacePage() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { user } = useAuth();

  // Load conversations on mount
  useEffect(() => {
    fetchApi('/chat/conversations').then(async (res) => {
      if (res.ok) setConversations(await res.json());
    });
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const createConversation = async () => {
    const res = await fetchApi('/chat/conversations', {
      method: 'POST',
      body: JSON.stringify({ title: 'New Chat', agent_type: 'general' }),
    });
    if (res.ok) {
      const conv = await res.json();
      setConversation(conv);
      setConversations((prev) => [conv, ...prev]);
      setMessages([]);
    }
  };

  const selectConversation = async (conv: Conversation) => {
    setConversation(conv);
    const res = await fetchApi(`/chat/conversations/${conv.id}/messages`);
    if (res.ok) setMessages(await res.json());
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    // Auto-create conversation if none selected
    let activeConv = conversation;
    if (!activeConv) {
      const res = await fetchApi('/chat/conversations', {
        method: 'POST',
        body: JSON.stringify({ title: input.slice(0, 50), agent_type: 'general' }),
      });
      if (!res.ok) return;
      activeConv = await res.json();
      setConversation(activeConv);
      setConversations((prev) => [activeConv!, ...prev]);
    }

    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: input };
    const assistantMsg: Message = { id: (Date.now() + 1).toString(), role: 'assistant', content: '', citations: [] };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setInput('');
    setIsStreaming(true);

    try {
      const token = localStorage.getItem('access_token');
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

      const response = await fetch(`${API_URL}/chat/conversations/${activeConv!.id}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ content: input }),
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      if (!response.body) throw new Error('No response body');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        let currentEvent = '';
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim();
          } else if (line.startsWith('data: ') && currentEvent) {
            try {
              const data = JSON.parse(line.slice(6));
              if (currentEvent === 'token') {
                assistantMsg.content += data.content || '';
                setMessages((prev) => [...prev.slice(0, -1), { ...assistantMsg }]);
              } else if (currentEvent === 'citations') {
                assistantMsg.citations = data.citations || [];
                setMessages((prev) => [...prev.slice(0, -1), { ...assistantMsg }]);
              }
            } catch { /* skip malformed JSON */ }
            currentEvent = '';
          }
        }
      }
    } catch (error) {
      assistantMsg.content = assistantMsg.content || 'An error occurred. Please try again.';
      setMessages((prev) => [...prev.slice(0, -1), { ...assistantMsg }]);
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <div className="flex h-full">
      {/* Sidebar - Conversation List */}
      <aside className="w-64 border-r border-white/10 flex flex-col">
        <div className="p-4">
          <button onClick={createConversation} className="w-full flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors">
            <Plus size={16} /> New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-2 space-y-1">
          {conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => selectConversation(conv)}
              className={`w-full text-left px-3 py-2 rounded-lg text-sm truncate transition-colors ${
                conversation?.id === conv.id ? 'bg-white/10 text-white' : 'text-gray-400 hover:bg-white/5 hover:text-gray-200'
              }`}
            >
              {conv.title}
            </button>
          ))}
        </div>
      </aside>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        <header className="px-6 py-4 border-b border-white/10 backdrop-blur-md sticky top-0 z-10">
          <h1 className="text-xl font-semibold tracking-tight">
            {conversation ? conversation.title : 'AI Workspace'}
          </h1>
        </header>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 && (
            <div className="flex-1 flex items-center justify-center h-full">
              <p className="text-gray-500">Start a conversation or select one from the sidebar.</p>
            </div>
          )}
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
                <p className="whitespace-pre-wrap text-sm leading-relaxed">
                  {msg.content || (isStreaming ? '●' : '')}
                </p>

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
          <div ref={messagesEndRef} />
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
    </div>
  );
}
