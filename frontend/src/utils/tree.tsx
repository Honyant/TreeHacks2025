import { memo } from "react";
import { type Edge, type Node, type NodeProps, Position } from "@xyflow/react";
import { Handle } from "@xyflow/react";
import { layoutFromMap } from "entitree-flex";
import { twMerge } from "tailwind-merge";

import { components } from "../openapi";

import dumpTree from "./dump.json";

interface RawTree {
  [k: string]: Partial<components["schemas"]["Graph"]["nodes"][number]>;
}

export type CustomNode = Node<
  Partial<
    Omit<components["schemas"]["Graph"]["nodes"][number], "type"> & {
      label: string;
      direction: string;
      isRoot: boolean;
    }
  >,
  components["schemas"]["Graph"]["nodes"][number]["type"]
>;

const nodeClassNames: {
  [k in components["schemas"]["Graph"]["nodes"][number]["type"]]: React.ComponentProps<"div">["className"];
} = {
  text: "bg-blue-100",
  image: "bg-green-100",
  link: "bg-yellow-100",
  audio: "bg-red-100",
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
  direction: "TB" | "LR" = "LR",
  rootId: string = "285ab462-37cf-40b2-a654-3a94d7ef8e05"
) => {
  const isTreeHorizontal = direction === "LR";

  const { nodes: entitreeNodes, rels: entitreeEdges } = layoutFromMap(
    rootId,
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
      data: { name: node.name, direction, isRoot: node.id === rootId, ...node },
      id: node.id ?? "",
      position: {
        x: node.x,
        y: node.y,
      },
      type: node.type ?? "text",
    };

    nodes.push(newNode);
  });

  return { nodes, edges };
};

const { Top, Bottom, Left, Right } = Position;

export const customNode = memo(({ data, type }: NodeProps<CustomNode>) => {
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
        "flex flex-col px-4 py-2 shadow-md rounded-md border-2",
        nodeClassNames[type]
      )}
      style={{
        minWidth: nodeWidth,
        minHeight: nodeHeight,
        maxWidth: nodeWidth,
        maxHeight: nodeHeight,
      }}
    >
      <div className="text-sm text-center text-slate-700 font-bold">
        {(name?.length ?? 0 > 50) ? name?.substring(0, 50) + "..." : name}
      </div>
      <div className="mt-2 text-xs text-slate-500 font-extralight overflow-ellipsis overflow-hidden max-h-full">
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
