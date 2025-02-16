import { useMemo } from "react";
import { useCallback, useEffect, useState } from "react";
import {
  applyEdgeChanges,
  applyNodeChanges,
  ConnectionLineType,
  MiniMap,
  NodeProps,
  OnEdgesChange,
  OnNodesChange,
  OnSelectionChangeFunc,
  ReactFlow,
  SelectionMode,
  useReactFlow,
} from "@xyflow/react";
import { useShallow } from "zustand/shallow";

import { useClient } from "./api/client";
import { ChatBox } from "./components/ChatBox";
import { ExpandBox } from "./components/ExpandBox";
import { CustomNode, customNode } from "./utils/tree";
import { components } from "./openapi";
import { useStore } from "./store";

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

// const { nodes: layoutedNodes, edges: layoutedEdges } =
//   layoutElements(initialTree);

// import { components } from "../openapi";
// const fetchedNodes: components["schemas"]["Graph"]["nodes"] = [];
// const fetchedEdges: components["schemas"]["Graph"]["edges"] = [];

const panOnDrag = [1, 2];

function App() {
  const {
    nodes,
    setNodes,
    edges,
    setEdges,
    setGraph,
    globalLoading,
    setSelectedNodeId,
  } = useStore(
    useShallow((state) => ({
      nodes: state.nodes,
      setNodes: state.setNodes,
      edges: state.edges,
      setEdges: state.setEdges,
      setGraph: state.setGraph,
      globalLoading: state.globalLoading,
      setSelectedNodeId: state.setSelectedNodeId,
    }))
  );

  const onNodesChange: OnNodesChange<CustomNode> = useCallback(
    (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
    [setNodes]
  );
  const onEdgesChange: OnEdgesChange = useCallback(
    (changes) => setEdges((edgs) => applyEdgeChanges(changes, edgs)),
    [setEdges]
  );

  const { setCenter } = useReactFlow();

  const queryClient = useClient();
  const startMutation = queryClient.useMutation("post", "/start", {});

  useEffect(() => {
    (async () => {
      try {
        const data = await startMutation.mutateAsync({});
        const { nodes: layoutedNodes } = setGraph(data.graph);
        const rootNode = layoutedNodes.find((node) => node.data.isRoot)!;

        setCenter(
          rootNode.position.x + (rootNode.width ? rootNode.width / 2 : 0),
          rootNode.position.y + (rootNode.height ? rootNode.height / 2 : 0),
          {
            zoom: 1,
            duration: 1000,
          }
        );
      } catch (error) {
        console.error(error);
      }
    })();
  }, []);

  const [selectedNodes, setSelectedNodes] = useState<string[]>([]);

  const onChange: OnSelectionChangeFunc = useCallback(
    ({ nodes }) => {
      setSelectedNodes(nodes.map((node) => node.id));
      if (nodes.length === 1) {
        setSelectedNodeId(nodes[0].id);
      } else if (nodes.length === 0) {
        setSelectedNodeId(null);
      }
    },
    [setSelectedNodeId]
  );

  const [selectedNode, setSelectedNode] = useState<CustomNode | null>(null);

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
        setSelectedNode(node);
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
      } else {
        setSelectedNode(null);
      }
    }
  }, [nodes, selectedNodes, setCenter]);

  return (
    <div className="w-screen h-screen">
      <div className="max-h-[10vh] min-h-[10vh]">
        {selectedNode ? <ChatBox initialMessages={[]} /> : null}
        {selectedNode && (
          <ExpandBox node={selectedNode as unknown as CustomNode} />
        )}
        {globalLoading && <div>Loading...</div>}
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
          onPaneClick={() => {
            setSelectedNodes([]);
            setSelectedNode(null);
          }}
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
