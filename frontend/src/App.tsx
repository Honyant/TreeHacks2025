import { queryClient } from "./api/client";
import { ChatBox } from "./components/ChatBox";
import { Tree } from "./components/Tree";

function App() {
  const { data, error, isPending } = queryClient.useQuery("post", "/chat", {
    body: { role: "user", message: "Hello, world!" },
  },);

  const initialMessages =
    (data)?.chat_history.map((msg) => ({
      role: msg.role,
      content: msg.message,
    })) || [];

  return (
    <>
     <h1 className="text-3xl font-bold underline">Hello world!</h1>
      <div>
        <h1 className="text-3xl font-bold">Chat Application</h1>
        {isPending && <div>Loading chat history...</div>}
        {error && <div>Error: {JSON.stringify(error)}</div>}
        {!isPending && !error && (<ChatBox initialMessages={initialMessages} />)}
        {(isPending || error) && (<ChatBox initialMessages={[]} />)}
      </div>
      <Tree />
    </>
  );
}

export default App;
