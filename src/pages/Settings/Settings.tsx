import {
  ExternalLink,
  Info,
  User,
} from "lucide-react";
import { FaGithub } from "react-icons/fa";
import { useEffect, useState } from "react";

interface GithubUser {
  id: number;
  login: string;
  name: string | null;
  avatar_url: string;
  email: string | null;
}

function Settings() {
  const [user, setUser] = useState<GithubUser | null>(null);
  const [loading, setLoading] = useState(true);

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
      } finally {
        setLoading(false);
      }
    };

    fetchCurrentUser();
  }, []);

  const displayName =
    user?.name || user?.login || "Developer";

  return (
    <div className="mx-auto w-full max-w-5xl space-y-6 sm:space-y-8">
      {/* Page header */}
      <section>
        <p className="text-sm font-medium text-blue-400">
          Workspace
        </p>

        <h1 className="mt-1 text-2xl font-bold tracking-tight text-white sm:text-3xl">
          Settings
        </h1>

        <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-500">
          Manage your DevPilot account and workspace
          information.
        </p>
      </section>

      {/* Account */}
      <section className="overflow-hidden rounded-xl border border-zinc-800 bg-[#111418]">
        <div className="border-b border-zinc-800 px-4 py-4 sm:px-6 sm:py-5">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-950">
              <User className="h-4 w-4 text-blue-400" />
            </div>

            <div className="min-w-0">
              <h2 className="text-sm font-semibold text-white">
                Account
              </h2>

              <p className="mt-0.5 text-xs text-zinc-500">
                Your connected GitHub account.
              </p>
            </div>
          </div>
        </div>

        <div className="p-4 sm:p-6">
          {loading ? (
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 animate-pulse rounded-full bg-zinc-800" />

              <div className="space-y-2">
                <div className="h-3 w-32 animate-pulse rounded bg-zinc-800" />
                <div className="h-2.5 w-24 animate-pulse rounded bg-zinc-900" />
              </div>
            </div>
          ) : user ? (
            <div className="flex min-w-0 flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex min-w-0 items-center gap-4">
                <img
                  src={user.avatar_url}
                  alt={displayName}
                  className="h-12 w-12 shrink-0 rounded-full border border-zinc-700"
                />

                <div className="min-w-0">
                  <p
                    className="truncate text-sm font-medium text-zinc-100"
                    title={displayName}
                  >
                    {displayName}
                  </p>

                  <p
                    className="mt-1 truncate text-xs text-zinc-500"
                    title={`@${user.login}`}
                  >
                    @{user.login}
                  </p>

                  {user.email && (
                    <p
                      className="mt-1 truncate text-xs text-zinc-600"
                      title={user.email}
                    >
                      {user.email}
                    </p>
                  )}
                </div>
              </div>

              <a
                href={`https://github.com/${user.login}`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex w-full shrink-0 items-center justify-center gap-2 rounded-lg border border-zinc-800 px-3.5 py-2 text-sm font-medium text-zinc-300 transition-colors hover:border-zinc-700 hover:bg-zinc-900 hover:text-white sm:w-auto"
              >
                <FaGithub className="h-4 w-4" />
                View GitHub
                <ExternalLink className="h-3.5 w-3.5 text-zinc-500" />
              </a>
            </div>
          ) : (
            <p className="text-sm text-zinc-500">
              Unable to load your GitHub account.
            </p>
          )}
        </div>
      </section>

      {/* GitHub Integration */}
      <section className="overflow-hidden rounded-xl border border-zinc-800 bg-[#111418]">
        <div className="border-b border-zinc-800 px-4 py-4 sm:px-6 sm:py-5">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-950">
              <FaGithub className="h-4 w-4 text-zinc-300" />
            </div>

            <div className="min-w-0">
              <h2 className="text-sm font-semibold text-white">
                GitHub integration
              </h2>

              <p className="mt-0.5 text-xs leading-5 text-zinc-500">
                DevPilot uses your GitHub connection to access
                repositories.
              </p>
            </div>
          </div>
        </div>

        <div className="divide-y divide-zinc-800/70">
          <div className="flex flex-col gap-3 px-4 py-5 sm:flex-row sm:items-center sm:justify-between sm:gap-6 sm:px-6">
            <div className="min-w-0">
              <p className="text-sm font-medium text-zinc-200">
                Connection status
              </p>

              <p className="mt-1 text-xs leading-5 text-zinc-500">
                Your GitHub account is connected to DevPilot.
              </p>
            </div>

            <span className="w-fit shrink-0 rounded-full border border-emerald-500/20 bg-emerald-500/[0.08] px-2.5 py-1 text-xs font-medium text-emerald-400">
              Connected
            </span>
          </div>

          <div className="flex flex-col gap-3 px-4 py-5 sm:flex-row sm:items-center sm:justify-between sm:gap-6 sm:px-6">
            <div className="min-w-0">
              <p className="text-sm font-medium text-zinc-200">
                Repository access
              </p>

              <p className="mt-1 text-xs leading-5 text-zinc-500">
                Use your connected GitHub account to work with
                repositories available to DevPilot.
              </p>
            </div>

            <span className="shrink-0 text-xs text-zinc-600">
              GitHub OAuth
            </span>
          </div>
        </div>
      </section>

      {/* About */}
      <section className="overflow-hidden rounded-xl border border-zinc-800 bg-[#111418]">
        <div className="border-b border-zinc-800 px-4 py-4 sm:px-6 sm:py-5">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-950">
              <Info className="h-4 w-4 text-zinc-400" />
            </div>

            <div className="min-w-0">
              <h2 className="text-sm font-semibold text-white">
                About DevPilot
              </h2>

              <p className="mt-0.5 text-xs text-zinc-500">
                Application information.
              </p>
            </div>
          </div>
        </div>

        <div className="space-y-4 px-4 py-5 sm:px-6">
          <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between sm:gap-6">
            <span className="text-sm text-zinc-400">
              Application
            </span>

            <span className="text-sm font-medium text-zinc-200">
              DevPilot
            </span>
          </div>

          <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between sm:gap-6">
            <span className="text-sm text-zinc-400">
              Version
            </span>

            <span className="font-mono text-xs text-zinc-500">
              0.1.0
            </span>
          </div>

          <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between sm:gap-6">
            <span className="text-sm text-zinc-400">
              Project
            </span>

            <a
              href="https://github.com/codered2007/DevPilot"
              target="_blank"
              rel="noreferrer"
              className="inline-flex w-fit items-center gap-2 text-sm text-blue-400 transition-colors hover:text-blue-300"
            >
              GitHub
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Settings;