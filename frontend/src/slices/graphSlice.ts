import { StateCreator } from "zustand";

import type { Store } from "../store";

interface GraphSliceState {
  globalLoading: boolean;
  selectedNodeId: string | null;
}

interface GraphSliceActions {
  setGlobalLoading: (loading: boolean) => void;
  setSelectedNodeId: (id: string | null) => void;
}

export interface GraphSlice extends GraphSliceState, GraphSliceActions {}

export const createGraphSlice: StateCreator<Store, [], [], GraphSlice> = (
  set
) => ({
  globalLoading: false,
  selectedNodeId: null,
  setGlobalLoading: (loading) => set({ globalLoading: loading }),
  setSelectedNodeId: (id) => set({ selectedNodeId: id }),
});
