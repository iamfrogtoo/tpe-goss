"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";

interface FeedbackMessage {
    id: string;
    name: string;
    content: string;
    timestamp: string;
}

export default function FeedbackPage() {
    const router = useRouter();
    const [messages, setMessages] = useState<FeedbackMessage[]>([]);
    const [name, setName] = useState("");
    const [content, setContent] = useState("");
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState("");
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const fetchMessages = async () => {
        try {
            const res = await fetch("/api/feedback");
            if (!res.ok) throw new Error("Failed to fetch");
            const data = await res.json();
            // Data returns latest first, but we want to render oldest first (top to bottom)
            setMessages(data.reverse());
        } catch (err) {
            console.error("Error fetching messages:", err);
            setError("無法載入留言，請稍後再試。");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        // Load initial nickname from localStorage if available
        const savedName = localStorage.getItem("goss_nickname");
        if (savedName) setName(savedName);

        fetchMessages();
        // Poll for new messages every 15 seconds
        const interval = setInterval(fetchMessages, 15000);
        return () => clearInterval(interval);
    }, []);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        // Scroll to bottom when messages load or a new message is added
        scrollToBottom();
    }, [messages]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");

        if (!name.trim()) {
            setError("請輸入暱稱");
            return;
        }

        if (!content.trim()) {
            setError("請輸入留言內容");
            return;
        }

        setSubmitting(true);
        try {
            // Save nickname for convenience
            localStorage.setItem("goss_nickname", name.trim());

            const res = await fetch("/api/feedback", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ name, content }),
            });

            if (!res.ok) throw new Error("Failed to post message");

            const newMessage = await res.json();
            setMessages((prev) => [...prev, newMessage]);
            setContent(""); // Clear input
        } catch (err) {
            console.error("Error posting message:", err);
            setError("發送失敗，請重試。");
        } finally {
            setSubmitting(false);
        }
    };

    const formatTime = (isoString: string) => {
        const date = new Date(isoString);
        return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
    };

    return (
        <div className="container-goss min-h-screen flex flex-col pb-[20px]">
            {/* Header */}
            <div className="flex items-center mb-[20px] border-b border-[#333] pb-[15px] pt-[10px] sticky top-0 bg-[#0d0d0d] z-20">
                <button
                    onClick={() => router.push("/")}
                    className="flex items-center justify-center w-[40px] h-[40px] bg-[#222] rounded-full text-white text-[20px] mr-[15px] border-none cursor-pointer hover:bg-[#333] transition-colors shadow-md"
                >
                    ←
                </button>
                <div className="flex flex-col">
                    <div className="text-[24px] font-black text-[#00f260]">
                        機場留言板
                    </div>
                    <div className="text-[12px] text-[#888]">
                        TPE GOSS 即時交流區
                    </div>
                </div>
            </div>

            {/* Messages Area */}
            <div className="flex-1 bg-[#1a1a1a] rounded-[10px] border border-[#333] p-[15px] overflow-y-auto mb-[20px] flex flex-col gap-[15px] max-h-[60vh]">
                {loading ? (
                    <div className="text-center text-[#666] my-auto">載入中...</div>
                ) : messages.length === 0 ? (
                    <div className="text-center text-[#666] my-auto">
                        <div className="text-[30px] mb-[10px]">💬</div>
                        尚無留言，成為第一個發言的人吧！
                    </div>
                ) : (
                    <>
                        {messages.map((msg) => {
                            const isMe = msg.name === name;
                            return (
                                <div key={msg.id} className={`flex flex-col max-w-[85%] ${isMe ? 'self-end items-end' : 'self-start items-start'}`}>
                                    <div className="text-[11px] text-[#888] mb-[4px] px-[5px] flex items-center gap-[5px]">
                                        <span className="font-bold text-[#aaa]">{msg.name}</span>
                                        <span>•</span>
                                        <span>{formatTime(msg.timestamp)}</span>
                                    </div>
                                    <div className={`p-[12px] rounded-[12px] break-words text-[14px] ${isMe
                                            ? 'bg-[#00f260]/20 border border-[#00f260]/30 text-white rounded-tr-[4px]'
                                            : 'bg-[#2a2a2a] border border-[#444] text-[#ddd] rounded-tl-[4px]'
                                        }`}>
                                        {msg.content}
                                    </div>
                                </div>
                            );
                        })}
                        <div ref={messagesEndRef} />
                    </>
                )}
            </div>

            {/* Input Area */}
            <form onSubmit={handleSubmit} className="bg-[#1a1a1a] rounded-[10px] border border-[#333] p-[15px]">
                {error && <div className="text-[#ff4b4b] text-[12px] mb-[10px]">{error}</div>}

                <div className="mb-[15px]">
                    <label className="block text-[12px] text-[#888] mb-[5px] ml-[5px]">暱稱 (單位/職稱)</label>
                    <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="例如: 長榮地勤 小王"
                        maxLength={30}
                        className="w-full bg-[#0d0d0d] border border-[#444] rounded-[8px] p-[10px] text-white text-[14px] focus:outline-none focus:border-[#00f260] transition-colors"
                    />
                </div>

                <div className="mb-[15px]">
                    <label className="block text-[12px] text-[#888] mb-[5px] ml-[5px]">訊息內容</label>
                    <textarea
                        value={content}
                        onChange={(e) => setContent(e.target.value)}
                        placeholder="輸入想分享的資訊或回報狀況..."
                        rows={3}
                        maxLength={500}
                        className="w-full bg-[#0d0d0d] border border-[#444] rounded-[8px] p-[10px] text-white text-[14px] focus:outline-none focus:border-[#00f260] transition-colors resize-none"
                    />
                </div>

                <button
                    type="submit"
                    disabled={submitting}
                    className="w-full bg-[#00f260] text-black font-bold py-[12px] rounded-[8px] transition-colors hover:bg-[#00d655] disabled:bg-[#444] disabled:text-[#888] flex items-center justify-center gap-[5px]"
                >
                    {submitting ? '發送中...' : '送出留言 ✈️'}
                </button>
            </form>
        </div>
    );
}
