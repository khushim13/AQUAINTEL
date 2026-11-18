"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Send,
  Droplets,
  RotateCcw,
  Sparkles,
  AlertCircle,
  Activity,
  Copy,
  Check,
  Volume2,
  VolumeX,
  Mic,
  MicOff,
  Download,
  Clock,
  Compass,
} from "lucide-react";
import DataCard from "../components/DataCard";
import FormattedMessage from "../components/FormattedMessage";
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
  latencyMs?: number | null;
}

interface SpeechRecognitionEvent {
  results: {
    [index: number]: {
      [index: number]: {
        transcript: string;
      };
    };
  };
}

interface SpeechRecognitionInstance {
  lang: string;
  interimResults: boolean;
  maxAlternatives: number;
  start: () => void;
  stop: () => void;
  onstart: (() => void) | null;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
}

interface IWindow extends Window {
  SpeechRecognition?: new () => SpeechRecognitionInstance;
  webkitSpeechRecognition?: new () => SpeechRecognitionInstance;
}

export default function ChatPage() {
  const [language, setLanguage] = useState<Language>("en");
  const [inputMessage, setInputMessage] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [speakingId, setSpeakingId] = useState<string | null>(null);
  const [isListening, setIsListening] = useState(false);
  const msgCounter = useRef(0);
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);

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

  // Cleanup speech synthesis on unmount
  useEffect(() => {
    return () => {
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
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
        latencyMs: typeof result.latency_ms === "number" ? result.latency_ms : null,
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
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    setSpeakingId(null);
    setMessages([]);
    setErrorMsg(null);
  };

  const handleCopyMessage = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleToggleSpeak = (id: string, text: string, langCode?: string) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      alert("Text-to-speech is not supported in this browser.");
      return;
    }

    if (speakingId === id) {
      window.speechSynthesis.cancel();
      setSpeakingId(null);
      return;
    }

    window.speechSynthesis.cancel();

    // Clean markdown symbols for cleaner speech
    const cleanText = text
      .replace(/\*\*/g, "")
      .replace(/`/g, "")
      .replace(/•/g, "")
      .replace(/#+/g, "");

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = langCode === "hi" ? "hi-IN" : "en-IN";
    utterance.rate = 1.0;

    utterance.onend = () => setSpeakingId(null);
    utterance.onerror = () => setSpeakingId(null);

    setSpeakingId(id);
    window.speechSynthesis.speak(utterance);
  };

  const handleToggleVoiceInput = () => {
    const win = window as IWindow;
    const SpeechRecognition = win.SpeechRecognition || win.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Voice input is not supported in this browser. Please use Chrome or Edge.");
      return;
    }

    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = language === "hi" ? "hi-IN" : "en-IN";
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event: SpeechRecognitionEvent) => {
        const transcript = event.results[0][0].transcript;
        setInputMessage((prev) => (prev ? `${prev} ${transcript}` : transcript));
        setIsListening(false);
      };

      recognition.onerror = (event: { error: string }) => {
        console.error("Speech Recognition Error:", event.error);
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      console.error("Speech recognition startup error:", err);
      setIsListening(false);
    }
  };

  const handleExportChat = () => {
    if (messages.length === 0) return;

    const transcript = [
      `# INGRES-Agent Groundwater Assessment Report`,
      `*Exported on: ${new Date().toLocaleString()}*`,
      `*Language: ${language.toUpperCase()}*\n`,
      `---`,
      ...messages.map((m) => {
        const sender = m.sender === "user" ? "👤 User Query" : "🤖 INGRES-Agent";
        const meta = m.toolCalled ? `\n> *Tool Invoked:* \`${m.toolCalled}\`` : "";
        return `\n### ${sender} (${m.timestamp})${meta}\n\n${m.text}\n`;
      }),
    ].join("\n");

    const blob = new Blob([transcript], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `INGRES_Report_${new Date().toISOString().slice(0, 10)}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex h-screen flex-col bg-slate-50 text-slate-900 font-sans antialiased">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-20 flex h-16 shrink-0 items-center justify-between border-b border-slate-200/90 bg-white/95 px-4 backdrop-blur-md sm:px-6 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-sky-600 via-cyan-500 to-teal-400 text-white shadow-md shadow-sky-500/25 ring-2 ring-white">
            <Droplets className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold tracking-tight text-slate-900 sm:text-lg">
                {t.title}
              </h1>
              <span className="rounded-md bg-sky-50 px-2 py-0.5 text-[10px] font-semibold text-sky-700 border border-sky-200/80">
                CGWB Open Data
              </span>
            </div>
            <p className="hidden text-xs text-slate-500 sm:block leading-none mt-1">{t.tagline}</p>
          </div>
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          {/* API Health Pill */}
          <div
            className={`hidden sm:flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium border shadow-2xs ${
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

          {/* Export Chat Button */}
          {messages.length > 0 && (
            <button
              type="button"
              onClick={handleExportChat}
              title={t.exportChat}
              className="flex h-9 items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 text-xs font-medium text-slate-700 hover:bg-slate-50 shadow-2xs transition-all"
            >
              <Download className="h-3.5 w-3.5 text-slate-500" />
              <span className="hidden md:inline">{t.exportChat}</span>
            </button>
          )}

          {/* Language Selector */}
          <div className="flex items-center rounded-lg border border-slate-200 bg-slate-100 p-0.5 text-xs shadow-2xs">
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
              className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100 hover:text-slate-900 shadow-2xs transition-all"
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
            <div className="mt-4 rounded-3xl border border-sky-100 bg-gradient-to-b from-white via-white to-sky-50/40 p-6 sm:p-8 shadow-sm">
              <div className="flex items-start gap-4">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-tr from-sky-500 to-cyan-400 text-white shadow-md shadow-sky-500/20">
                  <Sparkles className="h-6 w-6" />
                </div>
                <div>
                  <h2 className="text-xl font-bold tracking-tight text-slate-900">{t.subtitle}</h2>
                  <p className="mt-1 text-xs sm:text-sm text-slate-600 leading-relaxed">
                    Ask questions about district groundwater levels, extraction ratios, annual recharge, multi-year trends, or block categorization. Backed by verified CGWB open data with zero hallucinations.
                  </p>
                </div>
              </div>

              <div className="mt-6 border-t border-slate-100 pt-5">
                <div className="flex items-center gap-1.5 text-xs font-bold text-slate-600 uppercase tracking-wider">
                  <Compass className="h-3.5 w-3.5 text-sky-600" />
                  {t.examplesTitle}
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {t.examples.map((item, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleSendMessage(item.query)}
                      className="group rounded-full border border-slate-200/90 bg-white px-3.5 py-1.5 text-xs font-medium text-slate-700 shadow-2xs hover:border-sky-400 hover:bg-sky-50 hover:text-sky-900 transition-all text-left"
                    >
                      <span className="text-sky-600 mr-1.5 group-hover:translate-x-0.5 inline-block transition-transform">→</span>
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
                <div className="max-w-[85%] rounded-3xl rounded-tr-xs bg-gradient-to-r from-sky-600 to-sky-700 px-5 py-3 text-sm text-white shadow-md shadow-sky-600/15 sm:max-w-xl">
                  <p className="whitespace-pre-wrap leading-relaxed">{msg.text}</p>
                  <span className="mt-1 block text-right text-[10px] text-sky-200 font-medium">
                    {msg.timestamp}
                  </span>
                </div>
              ) : (
                <div className="w-full max-w-3xl rounded-3xl rounded-tl-xs border border-slate-200 bg-white p-5 shadow-sm sm:p-6 transition-all">
                  {/* Header info */}
                  <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-100 text-xs">
                    <div className="flex items-center gap-2">
                      <span className="flex items-center gap-1.5 font-bold text-slate-900">
                        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-sky-100 text-sky-600">
                          <Droplets className="h-3 w-3" />
                        </span>
                        INGRES Virtual Assistant
                      </span>
                      {msg.responseLanguage === "hi" && (
                        <span className="rounded-full bg-orange-50 px-2 py-0.5 text-[10px] font-semibold text-orange-700 border border-orange-200">
                          🇮🇳 हिन्दी
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-3 text-slate-400">
                      {msg.latencyMs && (
                        <span className="hidden sm:inline-flex items-center gap-1 text-[10px] font-mono text-slate-500 bg-slate-50 px-2 py-0.5 rounded-md border border-slate-200/60">
                          <Clock className="h-2.5 w-2.5 text-slate-400" />
                          {msg.latencyMs}ms
                        </span>
                      )}
                      <span className="text-[10px]">{msg.timestamp}</span>
                    </div>
                  </div>

                  {/* Formatted Message Body with Markdown formatting */}
                  <FormattedMessage content={msg.text} />

                  {/* Message Action Toolbar (Copy, Read Aloud) */}
                  <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3 text-xs text-slate-500">
                    <div className="flex items-center gap-1.5">
                      <button
                        type="button"
                        onClick={() => handleCopyMessage(msg.id, msg.text)}
                        className="inline-flex items-center gap-1 rounded-md px-2.5 py-1 text-[11px] font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors"
                      >
                        {copiedId === msg.id ? (
                          <>
                            <Check className="h-3 w-3 text-emerald-600" />
                            <span className="text-emerald-700 font-semibold">{t.copied}</span>
                          </>
                        ) : (
                          <>
                            <Copy className="h-3 w-3" />
                            <span>{t.copy}</span>
                          </>
                        )}
                      </button>

                      <button
                        type="button"
                        onClick={() => handleToggleSpeak(msg.id, msg.text, msg.responseLanguage)}
                        className={`inline-flex items-center gap-1 rounded-md px-2.5 py-1 text-[11px] font-medium transition-colors ${
                          speakingId === msg.id
                            ? "bg-sky-100 text-sky-800 font-semibold"
                            : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                        }`}
                      >
                        {speakingId === msg.id ? (
                          <>
                            <VolumeX className="h-3 w-3 text-sky-700 animate-pulse" />
                            <span>{t.stopListening}</span>
                          </>
                        ) : (
                          <>
                            <Volume2 className="h-3 w-3" />
                            <span>{t.listen}</span>
                          </>
                        )}
                      </button>
                    </div>

                    <span className="text-[10px] text-slate-400 font-medium">
                      CGWB Ground-Truth Grounded
                    </span>
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
                <div className="flex space-x-1.5">
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
            <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-800 flex items-start gap-3 shadow-xs">
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-600 mt-0.5" />
              <p className="leading-relaxed font-medium">{errorMsg}</p>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Floating Bottom Prompt Suggestions & Input Bar */}
      <footer className="sticky bottom-0 z-20 border-t border-slate-200/80 bg-white/95 p-3 sm:p-4 backdrop-blur-md shadow-lg">
        <div className="mx-auto max-w-4xl space-y-2">
          {/* Quick Query Pills */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs no-scrollbar">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider shrink-0">
              Suggestions:
            </span>
            {t.examples.slice(0, 4).map((ex, i) => (
              <button
                key={i}
                type="button"
                onClick={() => handleSendMessage(ex.query)}
                className="shrink-0 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-[11px] font-medium text-slate-700 hover:border-sky-300 hover:bg-sky-50 hover:text-sky-900 transition-all"
              >
                {ex.label}
              </button>
            ))}
          </div>

          {/* Input Form */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="relative flex items-center"
          >
            <input
              ref={inputRef}
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={t.placeholder}
              disabled={isLoading}
              className="w-full rounded-2xl border border-slate-300 bg-white py-3.5 pl-4 pr-24 text-sm text-slate-900 placeholder:text-slate-400 focus:border-sky-500 focus:outline-hidden focus:ring-3 focus:ring-sky-500/20 disabled:bg-slate-50 shadow-xs"
            />

            <div className="absolute right-2 flex items-center gap-1">
              {/* Voice Input Mic Button */}
              <button
                type="button"
                onClick={handleToggleVoiceInput}
                title={t.voiceSearch}
                className={`flex h-9 w-9 items-center justify-center rounded-xl transition-all ${
                  isListening
                    ? "bg-rose-500 text-white animate-pulse"
                    : "text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                }`}
              >
                {isListening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
              </button>

              {/* Send Button */}
              <button
                type="submit"
                disabled={isLoading || !inputMessage.trim()}
                className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-sky-600 to-cyan-500 text-white shadow-sm shadow-sky-600/30 transition-all hover:opacity-95 disabled:bg-slate-200 disabled:from-slate-200 disabled:to-slate-200 disabled:text-slate-400 disabled:shadow-none"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
          </form>
        </div>
      </footer>
    </div>
  );
}
