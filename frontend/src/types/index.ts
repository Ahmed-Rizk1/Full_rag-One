export interface User {
  id: string;
  email: string;
  full_name: string;
  tier: string;
  preferred_provider?: string;
  has_openai_key?: boolean;
  has_groq_key?: boolean;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  created_at: string;
  citations?: any[];
}

export interface Document {
  id: string;
  filename: string;
  status: string;
  created_at: string;
}

export interface Workflow {
  id: string;
  name: string;
  status: string;
  created_at: string;
}
