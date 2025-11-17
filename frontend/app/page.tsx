'use client';

import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  agent?: string;
  timestamp?: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initialize session on mount
  useEffect(() => {
    const initSession = async () => {
      try {
        const response = await axios.post(`${API_URL}/api/session/new`);
        setSessionId(response.data.session_id);
        
        // Add welcome message
        setMessages([{
          role: 'assistant',
          content: "Hi! I'm the Civic Grant Agent. I help volunteer fire departments and EMS agencies find and apply for grants.\n\nTo get started, could you tell me your organization's name and what type of department you are (volunteer, paid, or combination)?",
          agent: 'ProfileBuilder',
        }]);
      } catch (error) {
        console.error('Failed to initialize session:', error);
      }
    };
    
    initSession();
  }, []);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content: input.trim(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_URL}/api/chat`, {
        message: userMessage.content,
        session_id: sessionId,
        user_id: 'user_default',
      });

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.response,
        agent: response.data.agent_name,
        timestamp: response.data.timestamp,
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      // Update session ID if it changed
      if (response.data.session_id !== sessionId) {
        setSessionId(response.data.session_id);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-md p-4">
        <div className="max-w-4xl mx-auto flex items-center gap-3">
          <div className="text-4xl">🚒</div>
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Civic Grant Agent</h1>
            <p className="text-sm text-gray-600">AI-powered grant finding for fire departments & EMS agencies</p>
          </div>
        </div>
      </header>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-3xl rounded-lg p-4 shadow-md ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-800'
                }`}
              >
                {message.agent && (
                  <div className="text-xs font-semibold mb-2 opacity-70">
                    {message.agent}
                  </div>
                )}
                <div className="prose prose-sm max-w-none">
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
                {message.timestamp && (
                  <div className="text-xs mt-2 opacity-50">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white rounded-lg p-4 shadow-md">
                <div className="flex items-center gap-2">
                  <div className="animate-pulse">💭</div>
                  <span className="text-gray-600">Agent is thinking...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Form */}
      <div className="bg-white border-t shadow-lg p-4">
        <form onSubmit={sendMessage} className="max-w-4xl mx-auto">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message here..."
              disabled={isLoading}
              className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              Send
            </button>
          </div>
          {sessionId && (
            <div className="mt-2 text-xs text-gray-500 text-center">
              Session: {sessionId}
            </div>
          )}
        </form>
      </div>
    </div>
  );
}
