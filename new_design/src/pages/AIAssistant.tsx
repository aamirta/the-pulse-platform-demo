import { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, User, Bot, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { useLanguage } from '@/context/LanguageContext';
import { apiPost } from '@/lib/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  /** Tables the figures were drawn from, shown so answers stay auditable. */
  sources?: string[];
}

interface AssistantAnswer {
  answer: string;
  intent: string;
  sources: string[];
}

export default function AIAssistant() {
  const { t, language } = useLanguage();

  const suggestedPrompts = language === 'en' ? [
    'Which startups are in fintech in Morocco?',
    'Who is raising funds right now?',
    'Show me incubators in Casablanca',
    'What are the most active sectors?',
  ] : [
    'Quelles sont les startups en fintech au Maroc ?',
    'Qui lève des fonds en ce moment ?',
    'Montre-moi les incubateurs à Casablanca',
    'Quels sont les secteurs les plus actifs ?',
  ];

  const defaultResponse = t('aiDefaultResponse');

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Sync initial welcome message on language change
  useEffect(() => {
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: defaultResponse,
      },
    ]);
  }, [language, defaultResponse]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (text: string) => {
    if (!text.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    // Answers come from the API, which aggregates the live database. This page
    // previously replied from a hardcoded map whose figures (funding rounds
    // attributed to named companies, sector counts) were invented and did not
    // match the data.
    try {
      const result = await apiPost<AssistantAnswer>('/assistant/query', { question: text });
      setMessages((prev) => [
        ...prev,
        {
          id: `${Date.now() + 1}`,
          role: 'assistant',
          content: result.answer,
          sources: result.sources,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: `${Date.now() + 1}`,
          role: 'assistant',
          content:
            language === 'en'
              ? 'I could not reach the ecosystem data just now. Please try again.'
              : "Je n'ai pas pu accéder aux données de l'écosystème. Veuillez réessayer.",
        },
      ]);
      toast.error(err instanceof Error ? err.message : 'Assistant unavailable');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSend(input);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-140px)]">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b border-zinc-200 dark:border-zinc-800 mb-4">
        <div className="w-9 h-9 rounded-lg bg-pulse-orange-50 dark:bg-zinc-800 flex items-center justify-center">
          <Sparkles className="w-5 h-5 text-pulse-orange" />
        </div>
        <div>
          <h1 className="text-lg font-semibold text-zinc-900 dark:text-white flex items-center gap-2">
            PulseGPT
            <span className="px-1.5 py-0.5 text-[11px] font-semibold text-pulse-orange border border-pulse-orange/30 rounded">
              BETA
            </span>
          </h1>
          <p className="text-xs text-zinc-600 dark:text-zinc-300">{t('aiSubtitle')}</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}
          >
            {msg.role === 'assistant' && (
              <div className="w-7 h-7 rounded-lg bg-pulse-orange-50 dark:bg-zinc-800 flex items-center justify-center flex-shrink-0 mt-1">
                <Bot className="w-4 h-4 text-pulse-orange" />
              </div>
            )}
            <div
              className={`max-w-[80%] p-3.5 rounded-xl text-sm leading-relaxed whitespace-pre-line ${
                msg.role === 'user'
                  ? 'bg-pulse-orange text-primary-foreground rounded-br-sm'
                  : 'bg-white dark:bg-zinc-900 border border-zinc-100 dark:border-zinc-800 text-zinc-700 dark:text-zinc-300 rounded-bl-sm'
              }`}
            >
              {msg.content}
            </div>
            {msg.role === 'user' && (
              <div className="w-7 h-7 rounded-lg bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center flex-shrink-0 mt-1">
                <User className="w-4 h-4 text-zinc-550 dark:text-zinc-400" />
              </div>
            )}
          </div>
        ))}
        {isLoading && (
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-lg bg-pulse-orange-50 dark:bg-zinc-800 flex items-center justify-center flex-shrink-0">
              <Bot className="w-4 h-4 text-pulse-orange" />
            </div>
            <div className="p-3.5 bg-white dark:bg-zinc-900 border border-zinc-100 dark:border-zinc-800 rounded-xl rounded-bl-sm">
              <Loader2 className="w-4 h-4 text-zinc-500 dark:text-zinc-400 animate-spin" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Prompts */}
      {messages.length <= 1 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {suggestedPrompts.map((prompt) => (
            <button
              key={prompt}
              onClick={() => handleSend(prompt)}
              className="px-3 py-2 text-xs text-zinc-650 bg-white dark:bg-zinc-900 border border-zinc-250 dark:border-zinc-800 rounded-lg hover:border-pulse-orange/40 dark:hover:border-pulse-orange/40 hover:text-pulse-orange dark:hover:text-pulse-orange transition-colors"
            >
              {prompt}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <form onSubmit={handleSubmit} className="relative">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={t('pulseGptPlaceholder')}
          className="w-full h-12 pl-4 pr-12 bg-white dark:bg-zinc-900 border border-zinc-250 dark:border-zinc-800 rounded-xl text-sm text-zinc-900 dark:text-white placeholder:text-zinc-500 dark:text-zinc-400 focus:outline-none focus:border-pulse-orange/40 dark:focus:border-pulse-orange/40 focus:ring-2 focus:ring-pulse-orange/10 transition-all"
        />
        <button
          type="submit"
          disabled={!input.trim() || isLoading}
          className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-zinc-500 dark:text-zinc-400 hover:text-pulse-orange disabled:opacity-40 disabled:hover:text-zinc-500 dark:text-zinc-400 transition-colors"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
