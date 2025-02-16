import { useCallback, useEffect, useState } from "react";
import {
  ConnectionLineType,
  NodeProps,
  OnSelectionChangeFunc,
  Panel,
  ReactFlow,
  SelectionMode,
  useEdgesState,
  useNodesState,
  useReactFlow,
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

  const [selectedNodes, setSelectedNodes] = useState<string[]>([]);

  const onChange: OnSelectionChangeFunc = useCallback(({ nodes }) => {
    setSelectedNodes(nodes.map((node) => node.id));
  }, []);

  const { setCenter } = useReactFlow();

  useEffect(() => {
    if (selectedNodes.length === 1) {
      const node = nodes.find((node) => node.id === selectedNodes[0]);
      if (node) {
        setCenter(
          node.position.x +
            (node.measured?.width ? node.measured.width / 2 : 0),
          node.position.y +
            (node.measured?.height ? node.measured.height / 2 : 0),
          {
            zoom: 1.5,
            duration: 1000,
          }
        );
      }
    }
  }, [nodes, selectedNodes, setCenter]);

  return (
    <div style={{ width: "100vw", height: "90vh" }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onSelectionChange={onChange}
        connectionLineType={ConnectionLineType.SmoothStep}
        fitView
        fitViewOptions={{
          padding: 0.1,
          duration: 1000,
          nodes: [{ id: "1" }, { id: "2" }, { id: "3" }],
        }}
        nodeTypes={nodeTypes}
        panOnScroll
        selectionOnDrag
        panOnDrag={panOnDrag}
        selectionMode={SelectionMode.Partial}
        proOptions={{ hideAttribution: true }}
        nodesDraggable={false}
      >
        <Panel position="top-right">
          <button onClick={() => onLayout("TB")}>vertical layout</button>
          <button onClick={() => onLayout("LR")}>horizontal layout</button>
        </Panel>
      </ReactFlow>
    </div>
  );
};
