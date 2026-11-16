"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Send,
  Droplets,
  RotateCcw,
  Sparkles,
  AlertCircle,
  Activity,
} from "lucide-react";
import DataCard from "../components/DataCard";
import { translations, Language } from "../lib/translations";

interface Message {
  id: string;
  sender: "user" | "assistant";
  text: string;
  toolCalled?: string | null;
  params?: Record<string, unknown> | null;
  data?: Record<string, unknown> | null;
  timestamp: string;
  responseLanguage?: string;
  detectedLanguage?: string;
}

export default function ChatPage() {
  const [language, setLanguage] = useState<Language>("en");
  const [inputMessage, setInputMessage] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const msgCounter = useRef(0);

  const t = translations[language];
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Check API health on mount
  useEffect(() => {
    async function checkHealth() {
      try {
        const res = await fetch("/api/health");
        setApiOnline(res.ok);
      } catch {
        setApiOnline(false);
      }
    }
    checkHealth();
  }, []);

  // Auto-scroll to bottom of conversation
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || inputMessage).trim();
    if (!text || isLoading) return;

    setErrorMsg(null);
    msgCounter.current += 1;
    const userMsgId = `user-msg-${msgCounter.current}`;
    const newMsg: Message = {
      id: userMsgId,
      sender: "user",
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, newMsg]);
    setInputMessage("");
    setIsLoading(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, language }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: Failed to reach INGRES agent`);
      }

      const result = await response.json();
      msgCounter.current += 1;
      const assistantMsg: Message = {
        id: `assistant-msg-${msgCounter.current}`,
        sender: "assistant",
        text: typeof result.answer === "string" ? result.answer : "No response received.",
        toolCalled: result.tool_called,
        params: result.params,
        data: result.data,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        responseLanguage: result.response_language,
        detectedLanguage: result.detected_language,
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: unknown) {
      console.error("Chat Error:", err);
      setErrorMsg(t.errorConnection);
    } finally {
      setIsLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  };

  const handleClearChat = () => {
    setMessages([]);
    setErrorMsg(null);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex h-screen flex-col bg-slate-50 text-slate-900">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-200/90 bg-white/90 px-4 backdrop-blur-md sm:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-sky-600 to-cyan-500 text-white shadow-md shadow-sky-500/20">
            <Droplets className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold text-slate-900 sm:text-lg">
                {t.title}
              </h1>
              <span className="rounded-md bg-sky-50 px-2 py-0.5 text-[10px] font-semibold text-sky-700 border border-sky-200">
                SIH25066
              </span>
            </div>
            <p className="hidden text-xs text-slate-500 sm:block">{t.tagline}</p>
          </div>
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          {/* API Health Pill */}
          <div
            className={`hidden sm:flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium border ${
              apiOnline === true
                ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                : apiOnline === false
                ? "bg-rose-50 text-rose-700 border-rose-200"
                : "bg-slate-50 text-slate-600 border-slate-200"
            }`}
          >
            <Activity className="h-3 w-3 animate-pulse" />
            {apiOnline === true ? "FastAPI Live" : "FastAPI Offline"}
          </div>

          {/* Language Selector */}
          <div className="flex items-center rounded-lg border border-slate-200 bg-slate-50 p-0.5 text-xs">
            <button
              type="button"
              onClick={() => setLanguage("en")}
              className={`flex items-center gap-1 rounded-md px-2.5 py-1 font-semibold transition-all ${
                language === "en"
                  ? "bg-white text-sky-700 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              English
            </button>
            <button
              type="button"
              onClick={() => setLanguage("hi")}
              className={`flex items-center gap-1 rounded-md px-2.5 py-1 font-semibold transition-all ${
                language === "hi"
                  ? "bg-white text-sky-700 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              हिन्दी
            </button>
          </div>

          {/* Clear Chat Button */}
          {messages.length > 0 && (
            <button
              type="button"
              onClick={handleClearChat}
              title={t.clearChat}
              className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100 hover:text-slate-900"
            >
              <RotateCcw className="h-4 w-4" />
            </button>
          )}
        </div>
      </header>

      {/* Main Chat Scroll Container */}
      <main className="flex-1 overflow-y-auto px-4 py-6 sm:px-6">
        <div className="mx-auto max-w-4xl space-y-6">
          {/* Welcome Card & Example Chips when empty */}
          {messages.length === 0 && (
            <div className="mt-4 rounded-2xl border border-sky-100 bg-gradient-to-b from-white to-sky-50/50 p-6 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-sky-100 text-sky-700">
                  <Sparkles className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-slate-900">{t.subtitle}</h2>
                  <p className="text-xs text-slate-600 mt-0.5">{t.tagline}</p>
                </div>
              </div>

              <div className="mt-6 border-t border-sky-100 pt-4">
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  {t.examplesTitle}
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {t.examples.map((item, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleSendMessage(item.query)}
                      className="rounded-full border border-sky-200 bg-white px-3.5 py-1.5 text-xs font-medium text-sky-900 shadow-2xs hover:border-sky-400 hover:bg-sky-50 transition-all text-left"
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Message List */}
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col ${msg.sender === "user" ? "items-end" : "items-start"}`}
            >
              {msg.sender === "user" ? (
                <div className="max-w-[85%] rounded-2xl rounded-tr-xs bg-sky-600 px-4 py-3 text-sm text-white shadow-sm sm:max-w-xl">
                  <p className="whitespace-pre-wrap leading-relaxed">{msg.text}</p>
                  <span className="mt-1 block text-right text-[10px] text-sky-200 font-medium">
                    {msg.timestamp}
                  </span>
                </div>
              ) : (
                <div className="w-full max-w-3xl rounded-2xl rounded-tl-xs border border-slate-200 bg-white p-4 shadow-sm sm:p-5">
                  <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-100 text-xs">
                    <div className="flex items-center gap-2">
                      <span className="flex items-center gap-1.5 font-bold text-sky-800">
                        <Droplets className="h-3.5 w-3.5 text-sky-600" /> INGRES Virtual Assistant
                      </span>
                      {msg.responseLanguage === "hi" && (
                        <span className="rounded-full bg-orange-50 px-2 py-0.5 text-[9px] font-semibold text-orange-700 border border-orange-200">
                          🇮🇳 हिन्दी
                        </span>
                      )}
                    </div>
                    <span className="text-[10px] text-slate-400">{msg.timestamp}</span>
                  </div>

                  <div className="text-sm text-slate-800 leading-relaxed space-y-2 whitespace-pre-line">
                    {msg.text}
                  </div>

                  {/* Structured Data Card under answer */}
                  <DataCard
                    toolCalled={msg.toolCalled}
                    params={msg.params}
                    data={msg.data}
                  />
                </div>
              )}
            </div>
          ))}

          {/* Loading Indicator */}
          {isLoading && (
            <div className="flex items-start">
              <div className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-xs">
                <div className="flex space-x-1">
                  <div className="h-2 w-2 rounded-full bg-sky-600 animate-bounce" />
                  <div className="h-2 w-2 rounded-full bg-sky-600 animate-bounce [animation-delay:0.2s]" />
                  <div className="h-2 w-2 rounded-full bg-sky-600 animate-bounce [animation-delay:0.4s]" />
                </div>
                <span className="text-xs font-medium text-slate-600">{t.loading}</span>
              </div>
            </div>
          )}

          {/* Error Banner */}
          {errorMsg && (
            <div className="rounded-xl border border-rose-200 bg-rose-50 p-3.5 text-xs text-rose-800 flex items-start gap-2.5">
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-600 mt-0.5" />
              <div className="flex-1">
                <p className="font-semibold">Connection Notice</p>
                <p className="mt-0.5">{errorMsg}</p>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Input Form Bar */}
      <footer className="border-t border-slate-200/90 bg-white/95 p-3 sm:p-4 backdrop-blur-md">
        <div className="mx-auto max-w-4xl">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center gap-2"
          >
            <input
              ref={inputRef}
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              placeholder={t.placeholder}
              className="flex-1 rounded-xl border border-slate-300 bg-slate-50/70 px-4 py-3 text-sm text-slate-900 placeholder-slate-400 focus:border-sky-500 focus:bg-white focus:outline-hidden disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={!inputMessage.trim() || isLoading}
              className="flex h-11 items-center gap-2 rounded-xl bg-sky-600 px-4 font-semibold text-white shadow-sm hover:bg-sky-700 disabled:opacity-40 transition-all text-xs sm:text-sm"
            >
              <span>{t.send}</span>
              <Send className="h-4 w-4" />
            </button>
          </form>

          <p className="mt-2 text-center text-[10px] text-slate-400">
            Smart India Hackathon SIH25066 | India-Groundwater Resource Estimation System (INGRES) & CGWB Open Data
          </p>
        </div>
      </footer>
    </div>
  );
}
