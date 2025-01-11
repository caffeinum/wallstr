import SignUpForm from "@/components/auth/SignUpForm";

export default function SignUp() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-md rounded-lg">
        <SignUpForm urls={{ signIn: "/auth/signin" }} />
      </div>
    </div>
  );
}
