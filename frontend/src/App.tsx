import { useMemo } from "react";
import { useCallback, useEffect, useState } from "react";
import {
  ConnectionLineType,
  MiniMap,
  NodeProps,
  OnSelectionChangeFunc,
  ReactFlow,
  SelectionMode,
  useEdgesState,
  useNodesState,
  useReactFlow,
} from "@xyflow/react";

import { queryClient } from "./api/client";
import { ChatBox } from "./components/ChatBox";
import {
  CustomNode,
  customNode,
  initialTree,
  layoutElements,
} from "./utils/tree";
import { components } from "./openapi";

const nodeTypes: {
  [key in components["schemas"]["ChatMessageOut"]["graph"][string]["type"]]: React.FC<
    NodeProps<CustomNode>
  >;
} = {
  text: customNode,
  question: customNode,
  email: customNode,
  call: customNode,
  file: customNode,
  search: customNode,
  root: customNode,
};

const { nodes: layoutedNodes, edges: layoutedEdges } =
  layoutElements(initialTree);

// import { components } from "../openapi";
// const fetchedNodes: components["schemas"]["Graph"]["nodes"] = [];
// const fetchedEdges: components["schemas"]["Graph"]["edges"] = [];

const panOnDrag = [1, 2];

function App() {
  const { data, error, isPending } = queryClient.useQuery("post", "/chat", {
    body: { role: "user", message: "Hello, world!" },
  });

  const initialMessages = useMemo(() => {
    return (
      data?.chat_history.map((msg) => ({
        role: msg.role,
        content: msg.message,
      })) || []
    );
  }, [data]);

  const [nodes, setNodes, onNodesChange] =
    useNodesState<CustomNode>(layoutedNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(layoutedEdges);

  const onLayout = useCallback(
    (direction: "TB" | "LR") => {
      const { nodes: layoutedNodes, edges: layoutedEdges } = layoutElements(
        initialTree,
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

  const fitViewNodes = useMemo(() => {
    const root = nodes.find((node) => node.data.isRoot);
    const children = nodes
      .filter((node) => root?.data.children?.includes(node.id))
      .map((node) => ({ id: node.id }));
    return children.slice(2);
  }, [nodes]);

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
            zoom: 1,
            duration: 1000,
          }
        );
      }
    }
  }, [nodes, selectedNodes, setCenter]);

  return (
    <div className="w-screen h-screen">
      <div className="max-h-[10vh] min-h-[10vh]">
        {isPending ? (
          <div>Loading chat history...</div>
        ) : error ? (
          <div>Error: {JSON.stringify(error)}</div>
        ) : (
          <ChatBox initialMessages={initialMessages} />
        )}
      </div>

      <div style={{ width: "100vw", height: "90%" }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onSelectionChange={onChange}
          connectionLineType={ConnectionLineType.SmoothStep}
          fitView
          fitViewOptions={{
            padding: 0.2,
            duration: 1000,
            minZoom: 0.0001,
            nodes: fitViewNodes,
          }}
          nodeTypes={nodeTypes}
          panOnScroll
          selectionOnDrag
          panOnDrag={panOnDrag}
          selectionMode={SelectionMode.Partial}
          proOptions={{ hideAttribution: true }}
          nodesDraggable={false}
        >
          <MiniMap
            nodeStrokeWidth={3}
            position={"top-left"}
            bgColor="#1d232a"
            maskColor="transparent"
            maskStrokeColor="#fff"
            maskStrokeWidth={1.5}
            style={{ border: "1px dashed #fff", borderRadius: 10 }}
            pannable
          />
        </ReactFlow>
      </div>
    </div>
  );
}

export default App;
