import {z} from "zod";

const SettingsSchema = z.object({
  apiUrl: z.string().url(),
  env: z.enum(["development", "production", "test"]),

  nonAuthUrl: z.string(),
  jwt: z.object({
    issuer: z.string(),
  }),
});

export const settings = SettingsSchema.parse({
  apiUrl: process.env.NEXT_PUBLIC_API_URL,
  env: process.env.NODE_ENV,

  nonAuthUrl: "/auth/signin",
  jwt: {
    issuer: "https://github.com/limanAI/wallstr",
  },
});
