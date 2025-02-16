import { CustomNode } from "../utils/tree";

interface ChatBoxProps {
  node: CustomNode;
}

export const ExpandBox: React.FC<ChatBoxProps> = ({ node }) => {
  const { data, type } = node;

  return (
    <div>
      <h1>{data.name}</h1>
      <p>{data.content}</p>
      <span>{type}</span>
    </div>
  );
};
