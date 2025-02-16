import React, { useEffect, useRef, useState } from "react";

import { queryClient } from "../api/client";

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
  const [showFileUpload, setShowFileUpload] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const toggleChat = () => setIsOpen((prev) => !prev);

  const hasInitialMessages = () => initialMessages.length > 0;

  const handleSend = async () => {
    const trimmedInput = input.trim();
    if (!trimmedInput) return;
    // add user message to state
    setMessages((prev) => [...prev, { role: "user", content: trimmedInput }]);
    setInput("");

    try {
      const { data } = queryClient.useQuery("post", "/chat", {
        body: { role: "user", message: trimmedInput },
        refetchOnWindowFocus: false,
      });

      if (data) {
        const chatHistory = data.chat_history || ["", ""];
        const assistantMessage = chatHistory[chatHistory.length - 1];
        if (assistantMessage && assistantMessage.role === "assistant") {
          setMessages((prev) => [
            ...prev,
            { role: "assistant", content: assistantMessage.message },
          ]);
        }
      }
    } catch (error) {
      console.error("Error sending message:", error);
    }
  };

  const toggleFileUpload = () => setShowFileUpload((prev) => !prev);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      setSelectedFile(event.target.files[0]);
    }
  };

  const handleFileUpload = () => {
    if (!selectedFile) {
      console.log("No file selected");
      return;
    }
    // upload file to backend
    console.log("Uploading file:", selectedFile);
    setSelectedFile(null);
    setShowFileUpload(false);
  };

  return (
    <div className="card bg-base-100 w-96 shadow-xl fixed top-4 right-4 z-10 mb-4">
      <button onClick={toggleChat} className="btn btn-primary">
        {isOpen ? "Minimize Chat" : "Open Chat"}
      </button>

      {!hasInitialMessages() && (
        <div className="p-4 flex-1 overflow-y-auto bg-red-800 rounded-lg mt-4">
          <h2>Unable to load chat.</h2>
        </div>
      )}

      {isOpen && (
        <div
          className={`
            w-96 h-96 bg-base-content border rounded-lg shadow-lg flex flex-col mt-4 right-4
            transition-all duration-300
            ${isOpen ? "opacity-100" : "opacity-0 pointer-events-none"}
          `}
        >
          {/* header */}
          <div className="p-4 border-b rounded-lg bg-base-300 gap-2 px-2">
            <h2 className="text-lg font-semibold pl-2">Chat</h2>
          </div>

          {/* chat messages */}
          <div className="p-4 flex-1 overflow-y-auto bg-base-content rounded-lg">
            {messages.length === 0 ? (
              <p className="text-gray-500 text-sm">No messages yet...</p>
            ) : (
              messages.map((msg, index) => {
                const isUser = msg.role === "user";
                return (
                  <div
                    key={index}
                    className={`mb-2 flex ${isUser ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`inline-block text-sm px-4 py-2 rounded-lg text-wrap break-words max-w-[80%] ${isUser
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
          <div className="input-bordered rounded-full py-2 top-2 flex flex-col gap-2 px-2">
            {showFileUpload && (
              <div className="flex items-center gap-2">
                <input
                  type="file"
                  className="file-input w-full rounded-lg"
                  onChange={handleFileChange}
                />
                <button
                  type="button"
                  className="btn btn-primary rounded-lg"
                  onClick={handleFileUpload}
                >
                  Upload
                </button>
              </div>
            )}
            <div className="relative w-full">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") { handleSend(); }
                }}
                placeholder="Type your message..."
                className="w-full input rounded-lg pr-10"
              />
              <button
                type="button"
                onClick={toggleFileUpload}
                className="btn btn-primary btn-circle btn-sm text-xl absolute inset-y-0 my-auto right-2 no-animation"
              >
                +
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
