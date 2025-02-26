import SignInForm from "@/components/auth/SignInForm";
import { api } from "@/api";

export default async function SignIn() {
  const { data: config } = await api.default.getConfig();

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-md rounded-lg">
        <SignInForm
          urls={{ signUp: "/auth/signup", forgotPassword: "/auth/forgot-password" }}
          authProviders={config?.auth.providers || []}
          allowSignup={config?.auth.allow_signup ?? true}
        />
      </div>
    </div>
  );
}
