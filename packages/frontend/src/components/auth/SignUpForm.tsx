"use client";
import { useCallback } from "react";
import { useForm } from "react-hook-form";

export default function SignUpForm({ urls }: { urls: { signIn: string } }) {
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
      <h2 className="text-2xl font-bold text-center">Sign Up</h2>
      <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
        <div className="space-y-1">
          <label className="label" htmlFor="email">
            Email
          </label>
          <input className="input w-full" id="email" type="email" placeholder="Enter your email" />
        </div>

        <div className="space-y-1">
          <label className="label" htmlFor="password">
            Password
          </label>
          <input
            className="input w-full"
            id="password"
            type="password"
            {...register("password", { required: true })}
            placeholder="Enter your password"
          />
          {errors.password && <span className="text-error">Field is required</span>}
        </div>

        <button type="submit" className="btn btn-primary w-full">
          Create Account
        </button>

        <div className="divider">or sign up with</div>

        <div className="flex flex-col space-y-2">
          <a className="btn btn-outline w-full" href="#">
            Sign up with Google
          </a>

          <a className="btn btn-outline w-full" href="#">
            Sign up with GitHub
          </a>
        </div>

        <p className="text-sm text-center text-gray-600">
          Already have an account?{" "}
          <a href={urls.signIn} className="link link-primary">
            Sign in here
          </a>
        </p>
      </form>
    </div>
  );
}
