import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/lib/auth';
import { Sidebar } from '@/components/layout/Sidebar';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'AI Agent Workspace',
  description: 'Production-grade AI application workspace',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-zinc-950 text-slate-50 antialiased h-screen overflow-hidden`}>
        <AuthProvider>
          <div className="flex h-full">
            <Sidebar />
            <main className="flex-1 bg-zinc-950 shadow-2xl overflow-hidden relative">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-transparent to-purple-500/5 pointer-events-none" />
              {children}
            </main>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
