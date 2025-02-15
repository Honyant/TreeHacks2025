import { queryClient } from "../api/client";

export interface TreeProps {
  children?: React.ReactNode;
}

export const Tree: React.FC<TreeProps> = ({ children }) => {
  const { data, error, isPending } = queryClient.useQuery("post", "/chat", {
    body: { message: "Hello, world!" },
  });

  return (
    <div>
      {children || "Tree"}
      {isPending && <div>Loading...</div>}
      {error && <div>Error: {JSON.stringify(error)}</div>}
      {data && <div>Data: {JSON.stringify(data)}</div>}
    </div>
  );
};
