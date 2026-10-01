import { useState } from "react";
import { FaGithub } from "react-icons/fa";

function Login() {
  const [loading, setLoading] = useState(false);

  const handleGithubLogin = () => {
    setLoading(true);
    window.location.href = "http://localhost:8000/auth/github";
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0B0D10] px-6">
      <div className="w-full max-w-md rounded-2xl border border-zinc-800 bg-zinc-900 p-8">
        <h1 className="text-3xl font-bold text-white">
          Welcome to DevPilot
        </h1>

        <p className="mt-3 text-zinc-400">
          Sign in to start analyzing repositories with AI.
        </p>

        <button
          type="button"
          onClick={handleGithubLogin}
          disabled={loading}
          className="mt-8 flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-500 disabled:pointer-events-none disabled:opacity-70"
        >
          {loading ? (
            <>
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
              Connecting to GitHub...
            </>
          ) : (
            <>
              <FaGithub size={20} />
              Continue with GitHub
            </>
          )}
        </button>

        <p className="mt-6 text-center text-sm text-zinc-500">
          Sign in securely with your GitHub account.
        </p>
      </div>
    </div>
  );
}

export default Login;