import createFetchClient from "openapi-fetch";
import createClient from "openapi-react-query";

import { paths } from "../openapi";

const fetchClient = createFetchClient<paths>({
  baseUrl: "http://localhost:8000/",
});
export const queryClient = createClient(fetchClient);
