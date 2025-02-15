import React, { useEffect, useRef, useState } from "react";

export const ChatBox: React.FC = () => {
  const [isOpen, setIsOpen] = useState(true);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");

  const toggleChat = () => {
    setIsOpen((prev) => !prev);
  };

  const handleSend = () => {
    if (input.trim() !== "") {
      setMessages((prev) => [
        ...prev,
        { role: "user", content: input.trim() },
        { role: "server", content: "server chat response" },
      ]);
      setInput("");
    }
  };

  type Message = {
    role: "user" | "server";
    content: string;
  };

  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="fixed top-4 right-4 flex flex-col space-y-2">
      <button
        onClick={toggleChat}
        className="bg-gray-700 text-white p-3 rounded-full shadow-lg focus:outline-none inline-block w-auto"
      >
        {isOpen ? "Minimize Chat" : "Open Chat"}
      </button>
      {isOpen && (
        <div className="w-96 h-120 bg-white border border-gray-300 rounded-lg shadow-lg flex flex-col">
          {/* header */}
          <div className="p-4 border-b border-gray-200 bg-blue-5 rounded-full0">
            <h2 className="text-lg font-semibold text-gray-800">Chat</h2>
          </div>

          {/* chat messages */}
          <div className="p-4 flex-1 overflow-y-auto">
            {messages.length === 0 ? (
              <p className="text-gray-500 text-sm">No messages yet...</p>
            ) : (
              messages.map((msg, idx) => {
                const isUser = msg.role === "user";
                return (
                  <div
                    key={idx}
                    className={`mb-2 flex ${isUser ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`inline-block text-sm px-4 py-2 rounded-lg whitespace-normal text-wrap break-words max-w-[80%]
                                                ${
                                                  isUser
                                                    ? "bg-green-100 text-gray-700 text-right" // user
                                                    : "bg-blue-100 text-gray-700 text-left" // server
                                                }`}
                    >
                      {msg.content}
                    </div>
                  </div>
                );
              })
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* input box */}
          <div className="p-2 border-t border-gray-200">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSend();
              }}
              placeholder="Type your message..."
              className="w-full border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-400 text-black text-sm"
            />
          </div>
        </div>
      )}
    </div>
  );
};
