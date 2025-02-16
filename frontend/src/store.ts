import { create } from "zustand";

import { createGraphSlice, GraphSlice } from "./slices/graphSlice";

export type Store = GraphSlice;

export const useStore = create<Store>()((...a) => ({
  ...createGraphSlice(...a),
}));
