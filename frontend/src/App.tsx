import { useCallback, useEffect } from "react";
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
    selectedNodeId,
    setSelectedNodeId,
  } = useStore(
    useShallow((state) => ({
      nodes: state.nodes,
      setNodes: state.setNodes,
      edges: state.edges,
      setEdges: state.setEdges,
      setGraph: state.setGraph,
      globalLoading: state.globalLoading,
      selectedNodeId: state.selectedNodeId,
      setSelectedNodeId: state.setSelectedNodeId,
    }))
  );

  const { setCenter } = useReactFlow();

  const onNodesChange: OnNodesChange<CustomNode> = useCallback(
    (changes) => {
      if (changes.some((c) => c.type === "add")) {
        const selectedNode = nodes.find((node) => node.id === selectedNodeId);
        if (!selectedNode) return;
        setCenter(
          selectedNode.position.x +
            (selectedNode.width ? selectedNode.width / 2 : 0),
          selectedNode.position.y +
            (selectedNode.height ? selectedNode.height / 2 : 0),
          {
            zoom: 0.7,
            duration: 1000,
          }
        );
      }
      setNodes((nds) => applyNodeChanges(changes, nds));
    },
    [setNodes, nodes, setCenter, selectedNodeId]
  );
  const onEdgesChange: OnEdgesChange = useCallback(
    (changes) => setEdges((edgs) => applyEdgeChanges(changes, edgs)),
    [setEdges]
  );

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

  const onChange: OnSelectionChangeFunc = useCallback(
    ({ nodes }) => {
      if (nodes.length === 1) {
        setSelectedNodeId(nodes[0].id);
        const node = nodes[0];
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
      } else if (nodes.length === 0) {
        setSelectedNodeId(null);
      }
    },
    [setSelectedNodeId, setCenter]
  );

  return (
    <div className="w-screen h-screen">
      <div className="max-h-[10vh] min-h-[10vh]">
        {selectedNodeId ? <ChatBox initialMessages={[]} /> : null}
        {selectedNodeId && <ExpandBox />}
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
          }}
          nodeTypes={nodeTypes}
          panOnScroll
          selectionOnDrag
          panOnDrag={panOnDrag}
          selectionMode={SelectionMode.Partial}
          proOptions={{ hideAttribution: true }}
          nodesDraggable={false}
          onPaneClick={() => {
            setSelectedNodeId(null);
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
