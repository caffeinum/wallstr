export default function SignUp() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-md rounded-lg">
        <h2 className="text-2xl font-bold text-center">Sign Up</h2>
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
            <a href="/auth/signin" className="link link-primary">
              Sign in here
            </a>
          </p>
        </form>
      </div>
    </div>
  );
}
