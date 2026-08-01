import { FaGithub } from "react-icons/fa";
import Button from "../../components/ui/Button";

function Login() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0B0D10] px-6">
      <div className="w-full max-w-md rounded-2xl border border-zinc-800 bg-zinc-900 p-8">
        <h1 className="text-3xl font-bold text-white">
          Welcome to DevPilot
        </h1>

        <p className="mt-3 text-zinc-400">
          Sign in to start analyzing repositories with AI.
        </p>


<Button className="mt-8 flex w-full items-center justify-center gap-2">
  <FaGithub size={20} />
  Continue with GitHub
</Button>

        <p className="mt-6 text-center text-sm text-zinc-500">
          More providers coming soon.
        </p>
      </div>
    </div>
  );
}

export default Login;