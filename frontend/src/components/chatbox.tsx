"use client";
import React, { useState } from "react";

const Chat: React.FC = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState<string[]>([]);
    const [input, setInput] = useState("");

    const toggleChat = () => {
        setIsOpen((prev) => !prev);
    };

    const handleSend = () => {
        if (input.trim() !== "") {
            setMessages((prev) => [...prev, input.trim()]);
            setInput("");
        }
    };

    return (
        <div className="fixed top-4 w-120 h-500 right-4 flex flex-col items-end space-y-2">
            <button
                onClick={toggleChat}
                className="bg-gray-700 text-white p-3 rounded-full shadow-lg focus:outline-none"
            >
                {isOpen ? "Minimize Chat" : "Open Chat"}
            </button>
            {isOpen && (
                <div className="w-80 h-96 bg-white border border-gray-300 rounded-lg shadow-lg flex flex-col">
                    <div className="p-4 border-b border-gray-200 bg-blue-50">
                        <h2 className="text-lg font-semibold">Chat</h2>
                    </div>
                    <div className="p-4 flex-1 overflow-y-auto max-h-96 max-w-96">
                        {messages.length === 0 ? (
                            <p className="text-gray-500 text-sm">No messages yet...</p>
                        ) : (
                            messages.map((msg, idx) => (
                                <div key={idx} className="mb-2">
                                    <div className="inline-block text-sm px-4 py-2 bg-blue-100 text-gray-700 rounded-lg break-words whitespace-normal">
                                        {msg}
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                    <div className="p-2 border-t border-gray-200">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === "Enter") handleSend();
                            }}
                            placeholder="Type your message..."
                            className="w-full border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-400 text-black"
                        />
                    </div>
                </div>
            )}
        </div>
    );
};

export default Chat;
