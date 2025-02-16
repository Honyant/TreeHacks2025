import { useCallback } from "react";
import { useShallow } from "zustand/shallow";

import { useClient } from "../api/client";
import { useStore } from "../store";
import { nodeClassNames } from "../utils/tree";

export const ExpandBox: React.FC = () => {
  const queryClient = useClient();

  const { nodes, selectedNodeId, globalLoading, setGlobalLoading, setGraph } =
    useStore(
      useShallow((state) => ({
        nodes: state.nodes,
        selectedNodeId: state.selectedNodeId,
        globalLoading: state.globalLoading,
        setGlobalLoading: state.setGlobalLoading,
        setGraph: state.setGraph,
      }))
    );

  const generateMutation = queryClient.useMutation("post", "/generate", {});

  const research = useCallback(async () => {
    if (!selectedNodeId) return;
    setGlobalLoading(true);
    let data;
    try {
      data = await generateMutation.mutateAsync({
        body: {
          active_node_uuid: selectedNodeId,
        },
      });
      setGlobalLoading(false);
      if (data) {
        setGraph(data.graph);
      }
    } catch (error) {
      setGlobalLoading(false);
      console.error(error);
    }
  }, [selectedNodeId, setGlobalLoading, generateMutation, setGraph]);

  const node = nodes.find((n) => n.id === selectedNodeId);
  if (!node) return null;

  const { data, type } = node;
  const node_color =
    type !== undefined ? nodeClassNames[type] : nodeClassNames["text"];

  return (
    <div>
      <div className="card h-96 w-96 shadow-xl fixed top-4 right-4 z-10 mb-2 flex flex-col">
        <div
          className={`flex flex-col h-full border-b rounded-lg gap-2 p-4 ${node_color}`}
        >
          <h2 className="text-xl font-bold pl-2 text-black mt-4 text-center">
            {data.name}
          </h2>
          <div className="flex justify-center">
            <hr className="h-0.5 w-[80%] justify-center mt-2 mb-2 border-0 bg-black"></hr>
          </div>
          <div className="flex-1 overflow-y-auto mb-4">
            <div className="flex justify-center h-full p-2">
              <p className="text-black">{data.content}</p>
            </div>
          </div>
          <button
            className="btn btn-primary"
            onClick={() => !globalLoading && research()}
          >
            {globalLoading ? "Loading..." : "Research"}
          </button>
        </div>
      </div>
    </div>
  );
};
