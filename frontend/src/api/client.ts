import createFetchClient from "openapi-fetch";
import createClient from "openapi-react-query";

import { paths } from "../openapi";

export const useClient = () => {
  const fetchClient = createFetchClient<paths>({
    baseUrl: "http://localhost:8000/",
  });
  return createClient(fetchClient);
};
