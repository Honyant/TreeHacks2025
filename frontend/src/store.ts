import { create } from "zustand";
import { createGraphSlice, GraphSlice } from "./slices/graphSlice";
import { createChatSlice, ChatSlice } from "./slices/chatSlice";

export type Store = GraphSlice & ChatSlice;

export const useStore = create<Store>()((...a) => ({
  ...createGraphSlice(...a),
  ...createChatSlice(...a),
}));