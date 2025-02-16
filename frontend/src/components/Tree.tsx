import { useCallback } from "react";
import {
  ConnectionLineType,
  NodeProps,
  Panel,
  ReactFlow,
  SelectionMode,
  useEdgesState,
  useNodesState,
} from "@xyflow/react";

import { components } from "../openapi";
import {
  CustomNode,
  customNode,
  initialTree,
  layoutElements,
} from "../utils/tree";

const nodeTypes: {
  [key in components["schemas"]["Graph"]["nodes"][number]["type"]]: React.FC<
    NodeProps<CustomNode>
  >;
} = {
  text: customNode,
  image: customNode,
  link: customNode,
  audio: customNode,
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

export type TreeProps = object;
export const Tree: React.FC<TreeProps> = () => {
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
    <div style={{ width: "100vw", height: "90vh" }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        connectionLineType={ConnectionLineType.SmoothStep}
        fitView
        fitViewOptions={{
          padding: 0.1,
          duration: 1000,
          nodes: [{ id: "1" }, { id: "2" }, { id: "10" }],
        }}
        nodeTypes={nodeTypes}
        panOnScroll
        selectionOnDrag
        panOnDrag={panOnDrag}
        selectionMode={SelectionMode.Partial}
        proOptions={{ hideAttribution: true }}
      >
        <Panel position="top-right">
          <button onClick={() => onLayout("TB")}>vertical layout</button>
          <button onClick={() => onLayout("LR")}>horizontal layout</button>
        </Panel>
      </ReactFlow>
    </div>
  );
};
