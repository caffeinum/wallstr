export default function SignIn() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-md rounded-lg">
        <h2 className="text-2xl font-bold text-center">Sign In</h2>
        <form className="space-y-6">
          <div className="form-control">
            <label className="label">
              <span className="label-text">Email</span>
            </label>
            <input type="email" className="input w-full" required placeholder="Enter your email" />
          </div>

          <div className="form-control">
            <label className="label">
              <span className="label-text">Password</span>
            </label>
            <input type="password" className="input input-bordered w-full" required placeholder="Enter your password" />
            <label className="label">
              <a href="#" className="label-text-alt link link-hover">
                Forgot password?
              </a>
            </label>
          </div>

          <button type="submit" className="btn btn-primary w-full">
            Sign In
          </button>
          <p className="text-sm text-center text-gray-600">
            Don’t have an account?{" "}
            <a href="/auth/signup" className="link link-primary">
              Sign up here
            </a>
          </p>
        </form>
      </div>
    </div>
  );
}
