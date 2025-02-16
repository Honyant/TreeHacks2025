import { useCallback } from "react";
import {
  ConnectionLineType,
  Panel,
  ReactFlow,
  SelectionMode,
  useEdgesState,
  useNodesState,
} from "@xyflow/react";

import { queryClient } from "../api/client";
import {
  CustomNode,
  customNode,
  initialTree,
  layoutElements,
} from "../utils/tree";

const nodeTypes = {
  custom: customNode,
};

const { nodes: layoutedNodes, edges: layoutedEdges } = layoutElements(
  initialTree,
  "1",
  "LR"
);

// import { components } from "../openapi";
// const fetchedNodes: components["schemas"]["Graph"]["nodes"] = [];
// const fetchedEdges: components["schemas"]["Graph"]["edges"] = [];

const panOnDrag = [1, 2];

export interface TreeProps {
  children?: React.ReactNode;
}
export const Tree: React.FC<TreeProps> = ({ children }) => {
  const { data, error, isPending } = queryClient.useQuery("post", "/chat", {
    body: { role: "user", message: "Hello, world!" },
  });

  const [nodes, setNodes, onNodesChange] =
    useNodesState<CustomNode>(layoutedNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(layoutedEdges);

  const onLayout = useCallback(
    (direction: "TB" | "LR") => {
      const { nodes: layoutedNodes, edges: layoutedEdges } = layoutElements(
        initialTree,
        "1",
        direction
      );

      setNodes([...layoutedNodes]);
      setEdges([...layoutedEdges]);
    },
    [setNodes, setEdges]
  );

  return (
    <div style={{ width: "100vw", height: "100vh" }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        connectionLineType={ConnectionLineType.SmoothStep}
        fitView
        nodeTypes={nodeTypes}
        panOnScroll
        selectionOnDrag
        panOnDrag={panOnDrag}
        selectionMode={SelectionMode.Partial}
      >
        <Panel position="top-right">
          <button onClick={() => onLayout("TB")}>vertical layout</button>
          <button onClick={() => onLayout("LR")}>horizontal layout</button>
        </Panel>
      </ReactFlow>
    </div>
  );
};
