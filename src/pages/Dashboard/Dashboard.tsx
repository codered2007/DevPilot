import { useEffect, useState } from "react";
import {
  ArrowUpRight,
  GitBranch,
  Sparkles,
} from "lucide-react";

import EmptyState from "../../components/dashboard/EmptyState";
import RepositoryCard from "../../components/repository/RepositoryCard";
import RepositoryImport from "../../components/repository/RepositoryImport";
import { getRepositoryTree } from "../../services/api";
import { useRepository } from "../../context/useRepository";

interface GithubUser {
  id: number;
  login: string;
  name: string | null;
  avatar_url: string;
  email: string | null;
}

function Dashboard() {
  const [user, setUser] = useState<GithubUser | null>(null);
  const [fileCount, setFileCount] = useState(0);
  const [loadingFiles, setLoadingFiles] = useState(false);

  const { repository } = useRepository();

  useEffect(() => {
    const fetchCurrentUser = async () => {
      try {
        const response = await fetch(
          "http://localhost:8000/auth/me",
          {
            credentials: "include",
          }
        );

        if (!response.ok) {
          return;
        }

        const data = await response.json();
        setUser(data.user);
      } catch (error) {
        console.error(
          "Failed to fetch authenticated user:",
          error
        );
      }
    };

    fetchCurrentUser();
  }, []);

  useEffect(() => {
    const fetchFileCount = async () => {
      if (!repository) {
        setFileCount(0);
        return;
      }

      try {
        setLoadingFiles(true);

        const tree = await getRepositoryTree(
          repository.owner,
          repository.repo
        );

        const files = Array.isArray(tree)
          ? tree.filter(
              (item: { type: string }) =>
                item.type === "blob"
            )
          : [];

        setFileCount(files.length);
      } catch (error) {
        console.error(
          "Failed to fetch repository file count:",
          error
        );
        setFileCount(0);
      } finally {
        setLoadingFiles(false);
      }
    };

    fetchFileCount();
  }, [repository]);

  const displayName =
    user?.name || user?.login || "Developer";

  return (
    <div className="mx-auto w-full max-w-[1440px] space-y-6 sm:space-y-8">
      {/* Welcome */}
      <section className="relative overflow-hidden rounded-2xl border border-zinc-800 bg-[#111418]">
        <div className="pointer-events-none absolute inset-0">
          <div className="absolute -right-24 -top-32 h-72 w-72 rounded-full bg-blue-500/[0.07] blur-3xl" />
          <div className="absolute bottom-0 left-1/3 h-32 w-64 rounded-full bg-blue-400/[0.03] blur-3xl" />
        </div>

        <div className="relative flex min-w-0 items-center justify-between gap-6 px-5 py-6 sm:gap-8 sm:px-8 sm:py-8">
          <div className="min-w-0">
            <div className="mb-3 flex items-center gap-2">
              <span className="inline-flex max-w-full items-center gap-1.5 rounded-full border border-blue-500/20 bg-blue-500/[0.08] px-2.5 py-1 text-xs font-medium text-blue-400">
                <Sparkles className="h-3.5 w-3.5 shrink-0" />
                Developer workspace
              </span>
            </div>

            <h1 className="max-w-full truncate text-2xl font-bold tracking-tight text-white sm:text-4xl">
              Welcome back, {displayName}
            </h1>

            <p className="mt-3 max-w-2xl text-sm leading-6 text-zinc-400 sm:text-base">
              Explore repositories, understand your codebase, and work with
              DevPilot&apos;s AI-powered development tools.
            </p>
          </div>

          {user?.avatar_url && (
            <div className="hidden shrink-0 sm:block">
              <div className="rounded-full border border-zinc-700/80 bg-zinc-900 p-1 shadow-xl shadow-black/20">
                <img
                  src={user.avatar_url}
                  alt={displayName}
                  className="h-14 w-14 rounded-full"
                />
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Repository overview */}
      <section className="flex min-w-0 flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <h2 className="text-lg font-semibold tracking-tight text-white">
            Repository overview
          </h2>

          <p className="mt-1 text-sm leading-5 text-zinc-500">
            Your connected repositories in this workspace.
          </p>
        </div>

        <div className="flex w-full items-center gap-4 rounded-xl border border-zinc-800 bg-zinc-900/50 px-5 py-4 sm:w-auto sm:min-w-[220px]">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-950">
            <GitBranch className="h-4 w-4 text-blue-400" />
          </div>

          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
              Repositories
            </p>

            <p className="mt-0.5 text-xl font-semibold text-white">
              {repository ? 1 : 0}
            </p>
          </div>
        </div>
      </section>

      {/* Import repository */}
      <section className="min-w-0">
        <div className="mb-4">
          <h2 className="text-lg font-semibold tracking-tight text-white">
            Import repository
          </h2>

          <p className="mt-1 max-w-2xl text-sm leading-5 text-zinc-500">
            Connect a GitHub repository to start analyzing it with DevPilot.
          </p>
        </div>

        <RepositoryImport />
      </section>

      {/* Workspace */}
      <section className="min-w-0">
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div className="min-w-0">
            <h2 className="text-lg font-semibold tracking-tight text-white">
              Your workspace
            </h2>

            <p className="mt-1 max-w-2xl text-sm leading-5 text-zinc-500">
              Repositories and AI activity from your DevPilot workspace.
            </p>
          </div>

          <span className="flex w-fit items-center gap-1.5 text-xs text-zinc-600">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            Workspace ready
          </span>
        </div>

        <div className="grid min-w-0 gap-5 lg:grid-cols-2">
          {repository ? (
            <RepositoryCard
              name={repository.name}
              description={repository.description}
              branch={repository.branch}
              stars={repository.stars}
              files={loadingFiles ? 0 : fileCount}
              indexed={false}
            />
          ) : (
            <EmptyState
              title="No repository connected"
              description="Import a GitHub repository to start using DevPilot."
            />
          )}

          <EmptyState
            title="No AI conversations"
            description="Start chatting with your code after importing a repository."
          />
        </div>
      </section>

      {/* Workspace hint */}
      <section className="flex min-w-0 items-start justify-between gap-4 rounded-xl border border-zinc-800/70 bg-zinc-900/30 px-4 py-4 sm:items-center sm:px-5">
        <div className="min-w-0">
          <p className="text-sm font-medium text-zinc-300">
            Ready to explore your code?
          </p>

          <p className="mt-1 text-xs leading-5 text-zinc-500">
            Open a repository to access analysis, AI chat, architecture,
            dependencies, and security tools.
          </p>
        </div>

        <ArrowUpRight className="mt-0.5 hidden h-4 w-4 shrink-0 text-zinc-600 sm:block" />
      </section>
    </div>
  );
}

export default Dashboard;