import { useMemo } from "react";
import { ReactFlowProvider } from "@xyflow/react";

import { queryClient } from "./api/client";
import { ChatBox } from "./components/ChatBox";
import { Tree } from "./components/Tree";

function App() {
  const { data, error, isPending } = queryClient.useQuery("post", "/chat", {
    body: { role: "user", message: "Hello, world!" },
  });

  const initialMessages = useMemo(() => {
    return (
      data?.chat_history.map((msg) => ({
        role: msg.role,
        content: msg.message,
      })) || []
    );
  }, [data]);

  return (
    <>
      <div className="max-h-[10vh] min-h-[10vh]">
        <h1 className="text-3xl font-bold">Chat Application</h1>
        {isPending && <div>Loading chat history...</div>}
        {error && <div>Error: {JSON.stringify(error)}</div>}
        {!isPending && !error && <ChatBox initialMessages={initialMessages} />}
        {/* <ChatBox initialMessages={[]}/> */}
      </div>
      <ReactFlowProvider>
        <Tree />
      </ReactFlowProvider>
    </>
  );
}

export default App;
