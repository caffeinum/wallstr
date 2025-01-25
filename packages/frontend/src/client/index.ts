import {settings} from "@/conf";

import {client} from "./sdk";

client.setConfig({
  baseUrl: settings.apiUrl,
});

client.interceptors.request.use(async (req) => {
  return req;
});

export * from "./sdk";
