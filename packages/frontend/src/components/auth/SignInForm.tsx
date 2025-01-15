"use client";
import {useCallback, useState} from "react";
import {useForm} from "react-hook-form";
import {useRouter} from "next/navigation";

interface SignInFormData {
  email: string;
  password: string;
}

export default function SignInForm({urls}: {urls: {forgotPassword: string; signUp: string}}) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const {
    handleSubmit,
    register,
    formState: {errors, isSubmitting},
  } = useForm<SignInFormData>();

  const onSubmit = useCallback(
    async (data: SignInFormData) => {
      try {
        setError(null);
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/signin`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(data),
        });

        if (!res.ok) {
          if (res.status === 401) {
            setError("Incorrect email or password");
          } else {
            const errorData = await res.json();
            setError(errorData.detail || "Something went wrong");
          }
          return;
        }

        const {token} = await res.json();
        localStorage.setItem("access_token", token);

        router.push("/");
      } catch {
        setError("Network error. Please try again.");
      }
    },
    [router],
  );

  return (
    <div>
      <h2 className="text-2xl font-bold text-center">Sign In</h2>
      <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
        {error && (
          <div className="alert alert-error">
            <span>{error}</span>
          </div>
        )}

        <div className="space-y-1">
          <label className="label" htmlFor="email">
            Email
          </label>
          <input
            className={`input w-full ${errors.email ? "input-error" : ""}`}
            id="email"
            type="email"
            {...register("email", {
              required: "Email is required",
              pattern: {
                value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                message: "Invalid email address",
              },
            })}
            placeholder="Enter your email"
          />
          {errors.email && <span className="text-error text-sm">{errors.email.message}</span>}
        </div>

        <div className="space-y-1">
          <label className="label" htmlFor="password">
            Password
          </label>
          <input
            className={`input w-full ${errors.password ? "input-error" : ""}`}
            id="password"
            type="password"
            {...register("password", {
              required: "Password is required",
            })}
            placeholder="Enter your password"
          />
          {errors.password && <span className="text-error text-sm">{errors.password.message}</span>}
          <div className="text-sm text-right">
            <a href={urls.forgotPassword} className="label link link-hover">
              Forgot password?
            </a>
          </div>
        </div>

        <button type="submit" className="btn btn-primary w-full" disabled={isSubmitting}>
          {isSubmitting ? "Signing In..." : "Sign In"}
        </button>

        <div className="divider">or sign in with</div>

        <div className="flex flex-col space-y-2">
          <button className="btn btn-outline w-full" disabled>
            Sign in with Google
          </button>

          <button className="btn btn-outline w-full" disabled>
            Sign in with GitHub
          </button>
        </div>

        <p className="text-sm text-center text-gray-600">
          Don&apos;t have an account?{" "}
          <a href={urls.signUp} className="link link-primary">
            Sign up here
          </a>
        </p>
      </form>
    </div>
  );
}
