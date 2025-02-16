import React, { useEffect, useRef, useState } from "react";


export type Message = {
  role: "user" | "assistant";
  content: string;
};

interface ChatBoxProps {
  initialMessages?: Message[];
}

export const ChatBox: React.FC<ChatBoxProps> = ({ initialMessages = [] }) => {
  const [isOpen, setIsOpen] = useState(true);
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState("");

  const toggleChat = () => {
    setIsOpen((prev) => !prev);
  };

  const handleSend = () => {
    if (input.trim() !== "") {
      setMessages((prev) => [
        ...prev,
        { role: "user", content: input.trim() },
        { role: "assistant", content: "insert server message" },
      ]);
      setInput("");
    }
  };

  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="card bg-base-100 w-96 shadow-xl fixed top-4 right-4 flex flex-col z-10">
      <button onClick={toggleChat} className="btn btn-primary">
        {isOpen ? "Minimize Chat" : "Open Chat"}
      </button>
      {isOpen && (
        <div className="w-96 h-120 bg-base-content border rounded-lg shadow-lg flex flex-col my-2">
          {/* header */}
          <div className="p-4 border-b rounded-lg bg-base-300">
            <h2 className="text-lg font-semibold">Chat</h2>
          </div>

          {/* chat messages */}
          <div className="p-4 flex-1 overflow-y-auto bg-base-content rounded-lg">
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
                      className={`inline-block text-sm px-4 py-2 rounded-lg text-wrap break-words max-w-[80%]
                                                ${isUser
                          ? "chat chat-end chat-bubble text-right" // user
                          : "chat chat-start chat-bubble text-left" // assistant
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
          <div className="input-bordered rounded-full">
            <input type="file" className="file-input w-full rounded-lg" />
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSend();
              }}
              placeholder="Type your message..."
              className="w-full input rounded-lg"
            />
          </div>
        </div>
      )}
    </div>
  );
};


