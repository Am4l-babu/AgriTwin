"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { ArrowLeft, Send, Bot, User, Loader2, Sparkles, Thermometer, Droplets, Sun, Sprout } from "lucide-react";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
    sensorSnapshot?: Record<string, unknown> | null;
    timestamp: Date;
}

const SUGGESTIONS = [
    "How are the plants doing right now?",
    "Is the temperature safe for microgreens?",
    "Should I water the plants?",
    "Explain the current light conditions",
    "Give me a full farm status report",
    "What actions should I take right now?",
];

export default function AIAssistantPage() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [aiOnline, setAiOnline] = useState<boolean | null>(null);
    const bottomRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    // Check AI status on mount
    useEffect(() => {
        fetch(`${BACKEND}/api/v1/ai/status`)
            .then((r) => r.json())
            .then((d) => setAiOnline(d.ollama_reachable && d.model_available))
            .catch(() => setAiOnline(false));
    }, []);

    // Auto-scroll to bottom
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const sendMessage = async (text?: string) => {
        const msg = (text ?? input).trim();
        if (!msg || loading) return;
        setInput("");

        const userMsg: Message = {
            id: crypto.randomUUID(),
            role: "user",
            content: msg,
            timestamp: new Date(),
        };
        setMessages((prev) => [...prev, userMsg]);
        setLoading(true);

        try {
            const res = await fetch(`${BACKEND}/api/v1/ai/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: msg,
                    include_sensor_data: true,
                    farm_id: "farm_001",
                }),
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({ detail: "Unknown error" }));
                throw new Error(err.detail || `HTTP ${res.status}`);
            }

            const data = await res.json();
            const botMsg: Message = {
                id: crypto.randomUUID(),
                role: "assistant",
                content: data.reply,
                sensorSnapshot: data.sensor_snapshot,
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, botMsg]);
        } catch (e: unknown) {
            const errorMessage = e instanceof Error ? e.message : "Failed to get response";
            const errMsg: Message = {
                id: crypto.randomUUID(),
                role: "assistant",
                content: `⚠️ Error: ${errorMessage}`,
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errMsg]);
        } finally {
            setLoading(false);
            inputRef.current?.focus();
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 flex flex-col">
            {/* Header */}
            <header className="flex items-center gap-4 px-6 py-4 border-b border-white/5 bg-slate-950/80 backdrop-blur-md sticky top-0 z-20">
                <Link href="/" className="text-white/40 hover:text-white/70 transition-colors">
                    <ArrowLeft size={20} />
                </Link>
                <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center">
                        <Sparkles size={18} className="text-white" />
                    </div>
                    <div>
                        <h1 className="text-white font-semibold text-sm tracking-tight">Farm AI Assistant</h1>
                        <p className="text-[11px] text-white/40 font-mono">
                            LLaMA 3 · {aiOnline === null ? "checking…" : aiOnline ? "online" : "offline"}
                        </p>
                    </div>
                </div>
                <div className={`ml-auto w-2 h-2 rounded-full ${
                    aiOnline === null ? "bg-yellow-500 animate-pulse" : aiOnline ? "bg-emerald-500" : "bg-red-500"
                }`} />
            </header>

            {/* Messages area */}
            <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4 max-w-3xl w-full mx-auto">
                {messages.length === 0 && (
                    <div className="text-center mt-20 space-y-6">
                        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-500/20 to-fuchsia-500/20 border border-violet-500/20 flex items-center justify-center mx-auto">
                            <Bot size={32} className="text-violet-400" />
                        </div>
                        <div>
                            <h2 className="text-white/80 text-lg font-medium">Farm AI Assistant</h2>
                            <p className="text-white/30 text-sm mt-1 max-w-sm mx-auto">
                                Ask about your plants, sensor readings, or get growing recommendations.
                                I&apos;ll use live sensor data to give you accurate answers.
                            </p>
                        </div>

                        {/* Suggestion chips */}
                        <div className="flex flex-wrap gap-2 justify-center max-w-lg mx-auto">
                            {SUGGESTIONS.map((s) => (
                                <button
                                    key={s}
                                    onClick={() => sendMessage(s)}
                                    disabled={loading}
                                    className="px-3 py-1.5 text-xs rounded-full border border-white/10 text-white/50 hover:text-white/80 hover:border-violet-500/40 hover:bg-violet-500/10 transition-all"
                                >
                                    {s}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {messages.map((msg) => (
                    <div key={msg.id} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                        {msg.role === "assistant" && (
                            <div className="w-7 h-7 rounded-lg bg-violet-500/20 flex items-center justify-center flex-shrink-0 mt-1">
                                <Bot size={14} className="text-violet-400" />
                            </div>
                        )}
                        <div className={`max-w-[80%] space-y-2 ${msg.role === "user" ? "items-end" : "items-start"}`}>
                            <div
                                className={`px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                                    msg.role === "user"
                                        ? "bg-violet-600 text-white rounded-br-md"
                                        : "bg-white/5 text-white/80 border border-white/5 rounded-bl-md"
                                }`}
                            >
                                {msg.content}
                            </div>

                            {/* Sensor snapshot badge */}
                            {msg.sensorSnapshot && (
                                <div className="flex gap-2 flex-wrap">
                                    {msg.sensorSnapshot.temperature != null && (
                                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-orange-500/10 text-orange-400 text-[10px] font-mono">
                                            <Thermometer size={10} /> {String(msg.sensorSnapshot.temperature)}°C
                                        </span>
                                    )}
                                    {msg.sensorSnapshot.humidity != null && (
                                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-cyan-500/10 text-cyan-400 text-[10px] font-mono">
                                            <Droplets size={10} /> {String(msg.sensorSnapshot.humidity)}%
                                        </span>
                                    )}
                                    {msg.sensorSnapshot.light_level != null && (
                                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-400 text-[10px] font-mono">
                                            <Sun size={10} /> {String(msg.sensorSnapshot.light_level)}%
                                        </span>
                                    )}
                                    {msg.sensorSnapshot.soil_moisture != null && (
                                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-400 text-[10px] font-mono">
                                            <Sprout size={10} /> {String(msg.sensorSnapshot.soil_moisture)}%
                                        </span>
                                    )}
                                </div>
                            )}

                            <p className="text-[10px] text-white/20 font-mono">
                                {msg.timestamp.toLocaleTimeString()}
                            </p>
                        </div>
                        {msg.role === "user" && (
                            <div className="w-7 h-7 rounded-lg bg-white/10 flex items-center justify-center flex-shrink-0 mt-1">
                                <User size={14} className="text-white/60" />
                            </div>
                        )}
                    </div>
                ))}

                {loading && (
                    <div className="flex gap-3">
                        <div className="w-7 h-7 rounded-lg bg-violet-500/20 flex items-center justify-center flex-shrink-0">
                            <Bot size={14} className="text-violet-400" />
                        </div>
                        <div className="px-4 py-3 rounded-2xl bg-white/5 border border-white/5 rounded-bl-md">
                            <Loader2 size={16} className="text-violet-400 animate-spin" />
                        </div>
                    </div>
                )}

                <div ref={bottomRef} />
            </div>

            {/* Input bar */}
            <div className="sticky bottom-0 border-t border-white/5 bg-slate-950/90 backdrop-blur-md px-4 py-4">
                <div className="max-w-3xl mx-auto flex gap-3">
                    <input
                        ref={inputRef}
                        type="text"
                        placeholder="Ask about your farm…"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                        disabled={loading}
                        className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-white/30 outline-none focus:border-violet-500/50 focus:ring-1 focus:ring-violet-500/20 transition-all disabled:opacity-50"
                    />
                    <button
                        onClick={() => sendMessage()}
                        disabled={!input.trim() || loading}
                        className="px-4 rounded-xl bg-violet-600 hover:bg-violet-500 disabled:opacity-30 disabled:hover:bg-violet-600 text-white transition-all"
                    >
                        <Send size={18} />
                    </button>
                </div>
            </div>
        </div>
    );
}
