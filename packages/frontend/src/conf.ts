import {z} from "zod";

const SettingsSchema = z.object({
  API_URL: z.string().url(),
  ENV: z.enum(["development", "production", "test"]),

  NON_AUTH_URL: z.string(),
  jwt: z.object({
    issuer: z.string(),
  }),
});

export const settings = SettingsSchema.parse({
  API_URL: process.env.NEXT_PUBLIC_API_URL,
  ENV: process.env.NODE_ENV,

  NON_AUTH_URL: "/auth/signin",
  jwt: {
    issuer: "https://github.com/limanAI/wallstr",
  },
});
