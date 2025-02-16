import { memo } from "react";
import { type Edge, type Node, type NodeProps, Position } from "@xyflow/react";
import { Handle } from "@xyflow/react";
import { layoutFromMap } from "entitree-flex";
import { twMerge } from "tailwind-merge";

import { components } from "../openapi";

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

export const initialTree: RawTree = {
  1: {
    id: "1",
    name: "root",
    type: "text",
    children: ["2", "3"],
  },
  2: { id: "2", name: "child2" },
  3: {
    id: "3",
    name: "child3",
    type: "audio",
    children: ["4", "5", "11", "12", "13", "14", "15"],
  },
  4: { id: "4", name: "grandChild4" },
  5: { id: "5", name: "grandChild5" },
  11: { id: "11", name: "grandChild5" },
  12: { id: "12", name: "grandChild5" },
  13: { id: "13", name: "grandChild5" },
  14: { id: "14", name: "grandChild5" },
  15: { id: "15", name: "grandChild5", type: "image" },
  6: { id: "6", type: "link", name: "spouse of child 3" },
  8: {
    id: "8",
    name: "root sibling",
  },
  9: {
    id: "9",
    name: "child3 sibling",
  },
  10: {
    id: "10",
    name: "root spouse",
  },
};

const nodeWidth = 150;
const nodeHeight = 100;

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
  rootId: string,
  direction: "TB" | "LR" = "TB"
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
  const { label, direction } = data;

  const isTreeHorizontal = direction === "LR";

  const getTargetPosition = () => {
    return isTreeHorizontal ? Left : Top;
  };

  const isRootNode = data?.isRoot;
  const hasChildren = !!data?.children?.length;

  return (
    <div
      className={twMerge(
        "px-4 py-2 shadow-md rounded-md border-2 h-[100px] w-[150px]",
        nodeClassNames[type]
      )}
    >
      <div className="flex">
        <div className="rounded-full min-w-12 min-h-12 justify-center items-center flex border-2">
          {data.direction}
        </div>
        <div className="ml-2">
          <div className="text-lg font-bold">{label}</div>
        </div>
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
