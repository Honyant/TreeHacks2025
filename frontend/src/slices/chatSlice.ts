import { StateCreator } from "zustand";

import { Message } from "../components/ChatBox";
import type { Store } from "../store";

interface ChatSliceState {
  isOpen: boolean;
  messages: Message[];
  input: string;
  showFileUpload: boolean;
  selectedFile: File | null;
}

interface ChatSliceActions {
  toggleChat: () => void;
  addMessage: (message: Message) => void;
  setInput: (input: string) => void;
  toggleFileUpload: () => void;
  setSelectedFile: (file: File | null) => void;
  clearMessages: () => void;
}

export interface ChatSlice extends ChatSliceState, ChatSliceActions {}

export const createChatSlice: StateCreator<Store, [], [], ChatSlice> = (set, get) => ({
  isOpen: true,
  messages: [],
  input: "",
  showFileUpload: false,
  selectedFile: null,
  toggleChat: () => set({ isOpen: !get().isOpen }),
  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),
  setInput: (input) => set({ input }),
  toggleFileUpload: () => set({ showFileUpload: !get().showFileUpload }),
  setSelectedFile: (file) => set({ selectedFile: file }),
  clearMessages: () => set({ messages: [] }),
});
