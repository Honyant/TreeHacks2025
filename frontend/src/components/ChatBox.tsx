import React, { useEffect, useRef, useState } from "react";

import { queryClient } from "../api/client";
import { useStore } from "../store";

export type Message = {
  role: "user" | "assistant";
  content: string;
};

interface ChatBoxProps {
  initialMessages?: Message[];
}

export const ChatBox: React.FC<ChatBoxProps> = ({ initialMessages = [] }) => {
  const setGlobalLoading = useStore((state) => state.setGlobalLoading);

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
      const { data, isLoading, isFetched } = queryClient.useQuery(
        "post",
        "/chat",
        {
          body: { role: "user", message: trimmedInput },
          refetchOnWindowFocus: false,
        }
      );

      if (isLoading) {
        setGlobalLoading(true);
      }
      if (isFetched) {
        setGlobalLoading(false);
      }

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
    <div className="card w-96 shadow-xl fixed bottom-4 right-4 z-10 mb-4">
      {isOpen && (
        <div
          className={`
            w-96 h-96 bg-base-content border rounded-lg shadow-lg flex flex-col
            transition-all duration-300 bg-gray-100
            ${isOpen ? "opacity-100" : "opacity-0 pointer-events-none"}
          `}
        >
          {/* header */}
          <div className="p-4 border-b rounded-t-lg bg-base-content px-2">
            <h2 className="text-2xl font-bold pl-2 text-black">Chat</h2>
            <hr className="h-px w-1/2 justify-center m-1 border-0 bg-black"></hr>
          </div>

          {!hasInitialMessages() && (
            <div className="p-2 text-center rounded-lg m-2 bg-red-200 mx-4">
              <h2 className="text-red-800 text-xl font-bold">
                Unable to load chat.
              </h2>
            </div>
          )}
          {/* chat messages */}
          <div className={`p-4 flex-1 overflow-y-auto rounded-lg`}>
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
                      className={`inline-block text-sm px-4 py-2 rounded-lg text-wrap break-words max-w-[80%] text-black ${
                        isUser
                          ? "chat chat-end chat-bubble text-right bg-blue-200" // user
                          : "chat chat-start chat-bubble text-left bg-green-200" // assistant
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
                  className="file-input file-input-bordered file-input-neutral w-full rounded-lg text-black text-bold bg-base-content"
                  onChange={handleFileChange}
                />
                <button
                  type="button"
                  className="btn bg-blue-200 text-black rounded-lg"
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
                  if (e.key === "Enter") {
                    handleSend();
                  }
                }}
                placeholder="Type your message..."
                className="w-full input rounded-lg pr-10 bg-base-content text-black border-2 border-black"
              />
              <button
                type="button"
                onClick={toggleFileUpload}
                className="btn btn-circle btn-sm bg-blue-200 text-black text-2xl text-bold absolute inset-y-0 my-auto right-2 no-animation"
              >
                +
              </button>
            </div>
          </div>
        </div>
      )}
      <button onClick={toggleChat} className="btn mt-4 bg-blue-200 text-black">
        {isOpen ? "Minimize Chat" : "Open Chat"}
      </button>
    </div>
  );
};
