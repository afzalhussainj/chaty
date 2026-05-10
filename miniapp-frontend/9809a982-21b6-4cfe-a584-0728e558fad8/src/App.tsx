import React from 'react';
import { Header } from './components/Header';
import { ChatContainer } from './components/ChatContainer';
export function App() {
  return (
    <div className="flex flex-col h-screen w-full bg-[#faf7f2] font-sans overflow-hidden">
      <Header />
      <main className="flex-1 flex flex-col min-h-0 relative">
        <ChatContainer />
      </main>
    </div>);

}