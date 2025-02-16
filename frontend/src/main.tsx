import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createRoot } from "react-dom/client";
import { ReactFlowProvider } from "@xyflow/react";

import App from "./App.tsx";

import "@xyflow/react/dist/style.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

createRoot(document.getElementById("root")!).render(
  <QueryClientProvider client={queryClient}>
    <ReactFlowProvider>
      <App />
    </ReactFlowProvider>
  </QueryClientProvider>
);
