import { useState, useRef } from 'react';
import { Message } from '@/types';
import { useAuth } from '../auth';

export function useChat(conversationId: string) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const { user } = useAuth();

  const sendMessage = async (content: string) => {
    if (!content.trim() || isStreaming) return;
    
    const userMsg: Message = {
      id: Date.now().toString(),
      conversation_id: conversationId,
      role: 'user',
      content,
      created_at: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMsg]);
    setIsStreaming(true);

    let assistantMsg: Message = {
      id: (Date.now() + 1).toString(),
      conversation_id: conversationId,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString(),
      citations: []
    };
    
    setMessages(prev => [...prev, assistantMsg]);

    try {
      const token = localStorage.getItem('access_token');
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      
      const response = await fetch(`${API_URL}/chat/${conversationId}/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ content })
      });

      if (!response.body) throw new Error('No response body');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('event: token')) {
            const dataLine = lines[lines.indexOf(line) + 1];
            if (dataLine?.startsWith('data: ')) {
              const data = JSON.parse(dataLine.slice(6));
              assistantMsg.content += data.content;
              setMessages(prev => [...prev.slice(0, -1), { ...assistantMsg }]);
            }
          } else if (line.startsWith('event: citations')) {
            const dataLine = lines[lines.indexOf(line) + 1];
            if (dataLine?.startsWith('data: ')) {
              const data = JSON.parse(dataLine.slice(6));
              assistantMsg.citations = data.citations;
              setMessages(prev => [...prev.slice(0, -1), { ...assistantMsg }]);
            }
          }
        }
      }
    } catch (error) {
      console.error('Chat error:', error);
    } finally {
      setIsStreaming(false);
    }
  };

  return { messages, isStreaming, sendMessage };
}
