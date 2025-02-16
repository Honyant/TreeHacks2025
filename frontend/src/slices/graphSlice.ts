import { Edge } from "@xyflow/react";
import { StateCreator } from "zustand";

import { components } from "../openapi";
import type { Store } from "../store";
import { CustomNode, layoutElements } from "../utils/tree";

interface GraphSliceState {
  nodes: CustomNode[];
  edges: Edge[];
  globalLoading: boolean;
  selectedNodeId: string | null;
}

interface GraphSliceActions {
  setGlobalLoading: (loading: boolean) => void;
  setSelectedNodeId: (id: string | null) => void;
  setGraph: (graph: components["schemas"]["ChatMessageOut"]["graph"]) => {
    nodes: CustomNode[];
    edges: Edge[];
  };
  setNodes: (mutator: (prevNodes: CustomNode[]) => CustomNode[]) => void;
  setEdges: (mutator: (prevEdges: Edge[]) => Edge[]) => void;
}

export interface GraphSlice extends GraphSliceState, GraphSliceActions {}

export const createGraphSlice: StateCreator<Store, [], [], GraphSlice> = (
  set
) => ({
  globalLoading: false,
  selectedNodeId: "0",
  nodes: [],
  edges: [],
  setGlobalLoading: (loading) => set({ globalLoading: loading }),
  setSelectedNodeId: (id) => set({ selectedNodeId: id }),
  setGraph: (graph) => {
    const { nodes: layoutedNodes, edges: layoutedEdges } =
      layoutElements(graph);
    set({
      nodes: layoutedNodes,
      edges: layoutedEdges,
    });
    return { nodes: layoutedNodes, edges: layoutedEdges };
  },
  setNodes: (mutator) => set((state) => ({ nodes: mutator(state.nodes) })),
  setEdges: (mutator) => set((state) => ({ edges: mutator(state.edges) })),
});
