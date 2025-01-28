import SignInForm from "@/components/auth/SignInForm";

export default function SignIn() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-md rounded-lg">
        <SignInForm urls={{signUp: "/auth/signup", forgotPassword: "/auth/forgot-password"}} />
      </div>
    </div>
  );
}
