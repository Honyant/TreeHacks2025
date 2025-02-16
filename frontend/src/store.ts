import { create } from "zustand";

import { ChatSlice,createChatSlice } from "./slices/chatSlice";
import { createGraphSlice, GraphSlice } from "./slices/graphSlice";

export type Store = GraphSlice & ChatSlice;

export const useStore = create<Store>()((...a) => ({
  ...createGraphSlice(...a),
  ...createChatSlice(...a),
}));