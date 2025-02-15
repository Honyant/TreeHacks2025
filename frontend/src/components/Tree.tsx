export interface TreeProps {
  children?: React.ReactNode;
}

export const Tree: React.FC<TreeProps> = ({ children }) => {
  return <div>{children || "Tree"}</div>;
};
