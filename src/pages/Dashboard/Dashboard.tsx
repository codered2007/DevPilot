import { useEffect, useState } from "react";
import { GitBranch } from "lucide-react";

import RepositoryImport from "../../components/repository/RepositoryImport";
import RepositoryCard from "../../components/repository/RepositoryCard";
import EmptyState from "../../components/dashboard/EmptyState";

interface GithubUser {
  id: number;
  login: string;
  name: string | null;
  avatar_url: string;
  email: string | null;
}

function Dashboard() {
  const [user, setUser] = useState<GithubUser | null>(null);

  useEffect(() => {
    const fetchCurrentUser = async () => {
      try {
        const response = await fetch("http://localhost:8000/auth/me", {
          credentials: "include",
        });

        if (!response.ok) {
          return;
        }

        const data = await response.json();
        setUser(data.user);
      } catch (error) {
        console.error("Failed to fetch authenticated user:", error);
      }
    };

    fetchCurrentUser();
  }, []);

  const displayName = user?.name || user?.login || "Developer";

  return (
    <div className="space-y-10">
      {/* Welcome */}
      <section>
        <div className="flex items-start justify-between gap-6">
          <div>
            <p className="mb-2 text-sm font-medium text-blue-400">
              Developer workspace
            </p>

            <h1 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Welcome back, {displayName} 👋
            </h1>

            <p className="mt-2 max-w-2xl text-zinc-400">
              Explore repositories, understand your codebase, and work with
              DevPilot&apos;s AI-powered development tools.
            </p>
          </div>

          {user?.avatar_url && (
            <img
              src={user.avatar_url}
              alt={displayName}
              className="h-12 w-12 rounded-full border border-zinc-800"
            />
          )}
        </div>
      </section>

      {/* Repository Overview */}
      <section className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5">
          <div className="flex items-center justify-between">
            <p className="text-sm text-zinc-400">Repositories</p>

            <GitBranch className="h-5 w-5 text-zinc-500" />
          </div>

          <p className="mt-3 text-2xl font-semibold text-white">1</p>

          <p className="mt-1 text-xs text-zinc-500">
            Connected workspace
          </p>
        </div>
      </section>

      {/* Repository Import */}
      <section>
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-white">
            Import repository
          </h2>

          <p className="mt-1 text-sm text-zinc-500">
            Connect a GitHub repository to start analyzing it with DevPilot.
          </p>
        </div>

        <RepositoryImport />
      </section>

      {/* Dashboard Content */}
      <section>
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-white">
            Your workspace
          </h2>

          <p className="mt-1 text-sm text-zinc-500">
            Repositories and AI activity from your DevPilot workspace.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <RepositoryCard
            name="DevPilot"
            description="AI Software Engineering Workspace"
            branch="main"
            stars={15}
            files={142}
            indexed={true}
          />

          <EmptyState
            title="No AI conversations"
            description="Start chatting with your code after importing a repository."
          />
        </div>
      </section>
    </div>
  );
}

export default Dashboard;