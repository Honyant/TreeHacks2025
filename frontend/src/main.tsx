import { StrictMode } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { createRoot } from "react-dom/client";
import createFetchClient from "openapi-fetch";
import createClient from "openapi-react-query";

import App from "./App.tsx";
import { paths } from "./openapi";

import "./index.css";

const fetchClient = createFetchClient<paths>({
  baseUrl: "https://myapi.dev/v1/",
});
const queryClient = createClient(fetchClient);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>
);
