import { memo } from "react";
import { type Edge, type Node, type NodeProps, Position } from "@xyflow/react";
import { Handle } from "@xyflow/react";
import { layoutFromMap } from "entitree-flex";
import { twMerge } from "tailwind-merge";
import { useShallow } from "zustand/shallow";

import { components } from "../openapi";
import { useStore } from "../store";

import dumpTree from "./dump.json";

interface RawTree {
  [k: string]: Partial<
    components["schemas"]["ChatMessageOut"]["graph"][string]
  >;
}

export type CustomNode = Node<
  Partial<
    Omit<components["schemas"]["ChatMessageOut"]["graph"][string], "type"> & {
      label: string;
      direction: string;
      isRoot: boolean;
    }
  >,
  components["schemas"]["ChatMessageOut"]["graph"][string]["type"]
>;

export const nodeClassNames: {
  [k in components["schemas"]["ChatMessageOut"]["graph"][string]["type"]]: React.ComponentProps<"div">["className"];
} = {
  root: "bg-gray-100",
  text: "bg-blue-100",
  question: "bg-green-100",
  email: "bg-yellow-100",
  call: "bg-purple-100",
  file: "bg-orange-100",
  search: "bg-red-100",
};

export const initialTree = dumpTree as unknown as RawTree;

const nodeWidth = 250;
const nodeHeight = 150;

enum Orientation {
  Vertical = "vertical",
  Horizontal = "horizontal",
}

const entitreeSettings = {
  clone: true, // returns a copy of the input, if your application does not allow editing the original object
  enableFlex: true, // has slightly better perfomance if turned off (node.width, node.height will not be read)
  firstDegreeSpacing: 100, // spacing in px between nodes belonging to the same source, eg children with same parent
  nextAfterAccessor: "spouses", // the side node prop used to go sideways, AFTER the current node
  nextAfterSpacing: 100, // the spacing of the "side" nodes AFTER the current node
  nextBeforeAccessor: "siblings", // the side node prop used to go sideways, BEFORE the current node
  nextBeforeSpacing: 100, // the spacing of the "side" nodes BEFORE the current node
  nodeHeight, // default node height in px
  nodeWidth, // default node width in px
  orientation: Orientation.Vertical, // "vertical" to see parents top and children bottom, "horizontal" to see parents left and
  rootX: 0, // set root position if other than 0
  rootY: 0, // set root position if other than 0
  secondDegreeSpacing: 100, // spacing in px between nodes not belonging to same parent eg "cousin" nodes
  sourcesAccessor: "parents", // the prop used as the array of ancestors ids
  sourceTargetSpacing: 100, // the "vertical" spacing between nodes in vertical orientation, horizontal otherwise
  targetsAccessor: "children", // the prop used as the array of children ids
};

export const layoutElements = (
  tree: typeof initialTree,
  direction: "TB" | "LR" = "LR"
) => {
  const isTreeHorizontal = direction === "LR";

  const rootNode = Object.values(tree).find((node) => node.type === "root");
  if (!rootNode || !rootNode.id) {
    console.error("No root node found in the tree.");
    return { nodes: [], edges: [] };
  }

  const { nodes: entitreeNodes, rels: entitreeEdges } = layoutFromMap(
    rootNode.id,
    tree,
    {
      ...entitreeSettings,
      orientation: isTreeHorizontal
        ? Orientation.Horizontal
        : Orientation.Vertical,
    }
  );

  const nodes: CustomNode[] = [],
    edges: Edge[] = [];

  entitreeEdges.forEach((edge) => {
    const sourceNode = edge.source.id;
    const targetNode = edge.target.id;

    const newEdge: Partial<Edge> = {};

    newEdge.id = "e" + sourceNode + targetNode;
    newEdge.source = sourceNode;
    newEdge.target = targetNode;
    newEdge.type = "smoothstep";
    newEdge.animated = true;

    // Check if target node is spouse or sibling
    newEdge.sourceHandle = isTreeHorizontal ? Right : Bottom;
    newEdge.targetHandle = isTreeHorizontal ? Left : Top;

    edges.push(newEdge as Edge);
  });

  entitreeNodes.forEach((node) => {
    const newNode: CustomNode = {
      data: {
        name: node.name,
        direction,
        isRoot: node.type === "root",
        ...node,
      },
      id: node.id ?? "",
      position: {
        x: node.x,
        y: node.y,
      },
      type: node.type ?? "text",
      height: nodeHeight,
      width: nodeWidth,
    };

    nodes.push(newNode);
  });

  return { nodes, edges };
};

const { Top, Bottom, Left, Right } = Position;

export const customNode = memo(({ data, type }: NodeProps<CustomNode>) => {
  const { selectedNodeId, globalLoading } = useStore(
    useShallow((state) => ({
      selectedNodeId: state.selectedNodeId,
      globalLoading: state.globalLoading,
    }))
  );
  const { name, direction, content } = data;

  const isTreeHorizontal = direction === "LR";

  const getTargetPosition = () => {
    return isTreeHorizontal ? Left : Top;
  };

  const isRootNode = data?.isRoot;
  const hasChildren = !!data?.children?.length;

  return (
    <div
      className={twMerge(
        "flex flex-col shadow-md rounded-md border-2",
        nodeClassNames[type],
        selectedNodeId === data.id && !globalLoading && "border-pink-600"
      )}
      style={{
        minWidth: nodeWidth,
        minHeight: nodeHeight,
        maxWidth: nodeWidth,
        maxHeight: nodeHeight,
      }}
    >
      {selectedNodeId === data.id && globalLoading && (
        <svg
          height="100%"
          width="100%"
          style={{ position: "absolute", marginLeft: -2, marginTop: -2 }}
          xmlns="http://www.w3.org/2000/svg"
        >
          <rect
            rx="12"
            ry="12"
            style={{
              strokeDasharray: 260,
              strokeWidth: 5,
              position: "relative",
              fill: "transparent",
              stroke: "oklch(0.592 0.249 0.584)",
              animation: "svgAnimation 2.5s linear infinite",
            }}
            height="100%"
            width="100%"
            stroke-linejoin="round"
          />
        </svg>
      )}
      <div className="text-sm text-center text-slate-700 font-bold mx-4 pt-2">
        {(name?.length ?? 0 > 50) ? name?.substring(0, 50) + "..." : name}
      </div>
      <div className="mt-2 text-xs text-slate-500 font-extralight overflow-ellipsis overflow-hidden max-h-full mx-4 pb-2">
        {content}
      </div>
      {hasChildren && (
        <Handle
          className={"w-16 !bg-teal-500"}
          type="source"
          position={isTreeHorizontal ? Right : Bottom}
          id={isTreeHorizontal ? Right : Bottom}
        />
      )}
      {/* Target Handle */}
      {!isRootNode && (
        <Handle
          className={"w-16 !bg-teal-500"}
          type={"target"}
          position={getTargetPosition()}
          id={getTargetPosition()}
        />
      )}
    </div>
  );
});
