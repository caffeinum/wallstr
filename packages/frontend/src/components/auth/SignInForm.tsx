"use client";
import { useCallback } from "react";
import { useForm } from "react-hook-form";

export default function SignInForm({ urls }: { urls: { forgotPassword: string; signUp: string } }) {
  const {
    handleSubmit,
    register,
    formState: { errors },
  } = useForm();

  // @ts-expect-error: Missed type for data
  const onSubmit = useCallback((data) => {
    console.log(data);
  }, []);

  return (
    <div>
      <h2 className="text-2xl font-bold text-center">Sign In</h2>
      <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
        <div className="space-y-1">
          <label className="label">Email</label>
          <input type="email" className="input w-full" placeholder="Enter your email" />
        </div>

        <div className="space-y-1">
          <label className="label">Password</label>
          <input
            className="input w-full"
            type="password"
            {...register("password", { required: true })}
            placeholder="Enter your password"
          />
          {errors.password && <span className="text-error">Field is required</span>}
          <div className="text-sm text-right">
            <a href={urls.forgotPassword} className="label link link-hover">
              Forgot password?
            </a>
          </div>
        </div>

        <button type="submit" className="btn btn-primary w-full">
          Sign In
        </button>

        <p className="text-sm text-center text-gray-600">
          Don’t have an account?{" "}
          <a href={urls.signUp} className="link link-primary">
            Sign up here
          </a>
        </p>
      </form>
    </div>
  );
}
