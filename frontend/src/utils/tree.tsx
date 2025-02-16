import { memo } from "react";
import { type Edge, type Node, type NodeProps, Position } from "@xyflow/react";
import { Handle } from "@xyflow/react";
import { layoutFromMap } from "entitree-flex";
import { components } from "../openapi";

interface Tree {
  [k: string]: components["schemas"][];
}

export const initialTree: Tree = {
  1: {
    id: "1",
    name: "root",
    type: "input",
    children: ["2", "3"],
    siblings: ["8"],
    spouses: ["10"],
  },
  2: { id: "2", name: "child2" },
  3: {
    id: "3",
    name: "child3",
    children: ["4", "5", "11", "12", "13", "14", "15"],
    siblings: ["9"],
    spouses: ["6"],
  },
  4: { id: "4", name: "grandChild4" },
  5: { id: "5", name: "grandChild5" },
  11: { id: "11", name: "grandChild5" },
  12: { id: "12", name: "grandChild5" },
  13: { id: "13", name: "grandChild5" },
  14: { id: "14", name: "grandChild5" },
  15: { id: "15", name: "grandChild5" },
  6: { id: "6", name: "spouse of child 3", isSpouse: true },
  8: {
    id: "8",
    name: "root sibling",
    isSibling: true,
  },
  9: {
    id: "9",
    name: "child3 sibling",
    isSibling: true,
  },
  10: {
    id: "10",
    name: "root spouse",
    isSpouse: true,
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
    const isTargetSpouse = !!edge.target.isSpouse;
    const isTargetSibling = !!edge.target.isSibling;

    if (isTargetSpouse) {
      newEdge.sourceHandle = isTreeHorizontal ? Bottom : Right;
      newEdge.targetHandle = isTreeHorizontal ? Top : Left;
    } else if (isTargetSibling) {
      newEdge.sourceHandle = isTreeHorizontal ? Top : Left;
      newEdge.targetHandle = isTreeHorizontal ? Bottom : Right;
    } else {
      newEdge.sourceHandle = isTreeHorizontal ? Right : Bottom;
      newEdge.targetHandle = isTreeHorizontal ? Left : Top;
    }

    edges.push(newEdge as Edge);
  });

  entitreeNodes.forEach((node) => {
    const newNode: Partial<CustomNode> = {};

    const isSpouse = !!node?.isSpouse;
    const isSibling = !!node?.isSibling;
    const isRoot = node?.id === rootId;

    if (isSpouse) {
      newNode.sourcePosition = isTreeHorizontal ? Bottom : Right;
      newNode.targetPosition = isTreeHorizontal ? Top : Left;
    } else if (isSibling) {
      newNode.sourcePosition = isTreeHorizontal ? Top : Left;
      newNode.targetPosition = isTreeHorizontal ? Bottom : Right;
    } else {
      newNode.sourcePosition = isTreeHorizontal ? Right : Bottom;
      newNode.targetPosition = isTreeHorizontal ? Left : Top;
    }

    newNode.data = { label: node.name, direction, isRoot, ...node };
    newNode.id = node.id;
    newNode.type = "custom";

    newNode.width = nodeWidth;
    newNode.height = nodeHeight;

    newNode.position = {
      x: node.x,
      y: node.y,
    };

    nodes.push(newNode as CustomNode);
  });

  return { nodes, edges };
};

const { Top, Bottom, Left, Right } = Position;

export type CustomNode = Node<
  {
    isSpouse?: boolean;
    isSibling?: boolean;
    label: string;
    direction: string;
    isRoot?: boolean;
    children?: unknown[];
    siblings?: unknown[];
    spouses?: unknown[];
  },
  "custom"
>;

export const customNode = memo(({ data }: NodeProps<CustomNode>) => {
  const { isSpouse, isSibling, label, direction } = data;

  const isTreeHorizontal = direction === "LR";

  const getTargetPosition = () => {
    if (isSpouse) {
      return isTreeHorizontal ? Top : Left;
    } else if (isSibling) {
      return isTreeHorizontal ? Bottom : Right;
    }
    return isTreeHorizontal ? Left : Top;
  };

  const isRootNode = data?.isRoot;
  const hasChildren = !!data?.children?.length;
  const hasSiblings = !!data?.siblings?.length;
  const hasSpouses = !!data?.spouses?.length;

  return (
    <div className="px-4 py-2 shadow-md rounded-md border-2 h-[100px] w-[150px]">
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

      {/* For spouses */}
      {hasSpouses && (
        <Handle
          className={"w-16 !bg-teal-500"}
          type="source"
          position={isTreeHorizontal ? Bottom : Right}
          id={isTreeHorizontal ? Bottom : Right}
        />
      )}

      {/* For siblings */}
      {hasSiblings && (
        <Handle
          className={"w-16 !bg-teal-500"}
          type="source"
          position={isTreeHorizontal ? Top : Left}
          id={isTreeHorizontal ? Top : Left}
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
