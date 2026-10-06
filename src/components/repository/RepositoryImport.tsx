import { useState } from "react";
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  Code2,
  GitBranch,
  GitFork,
  Loader2,
  Star,
} from "lucide-react";
import { FaGithub } from "react-icons/fa";
import { useNavigate } from "react-router-dom";

import Button from "../ui/Button";
import Input from "../ui/Input";
import { importRepository } from "../../services/api";
import { useRepository } from "../../context/useRepository";

function RepositoryImport() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const { repository, setRepository } = useRepository();
  const navigate = useNavigate();

  async function handleImport() {
    if (!url.trim()) {
      setError("Please enter a GitHub repository URL.");
      return;
    }

    try {
      setLoading(true);
      setError("");

      const importedRepository = await importRepository(url);

      setRepository(importedRepository);

      navigate("/dashboard/repository");
    } catch (err) {
      console.error(err);
      setError("Repository not found or GitHub API request failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-zinc-800 bg-[#111418]">
      {/* Import form */}
      <div className="p-6 sm:p-7">
        <div className="flex items-start gap-4">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-950">
            <FaGithub className="h-5 w-5 text-zinc-200" />
          </div>

          <div className="min-w-0">
            <h3 className="text-base font-semibold text-white">
              Connect a GitHub repository
            </h3>

            <p className="mt-1 max-w-2xl text-sm leading-5 text-zinc-500">
              Enter a public repository URL to explore and analyze its
              codebase with DevPilot.
            </p>
          </div>
        </div>

        <div className="mt-6">
          <label
            htmlFor="repository-url"
            className="mb-2 block text-xs font-medium uppercase tracking-wider text-zinc-500"
          >
            Repository URL
          </label>

          <div className="flex flex-col gap-3 sm:flex-row">
            <div className="min-w-0 flex-1">
              <Input
                id="repository-url"
                value={url}
                onChange={(e) => {
                  setUrl(e.target.value);

                  if (error) {
                    setError("");
                  }
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !loading) {
                    handleImport();
                  }
                }}
                placeholder="https://github.com/facebook/react"
                disabled={loading}
              />
            </div>

            <Button
              onClick={handleImport}
              disabled={loading}
              className="shrink-0 gap-2 sm:min-w-[150px]"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Importing...
                </>
              ) : (
                <>
                  <FaGithub className="h-4 w-4" />
                  Import
                </>
              )}
            </Button>
          </div>

          <p className="mt-2 text-xs text-zinc-600">
            Example: github.com/facebook/react
          </p>
        </div>

        {error && (
          <div className="mt-4 flex items-start gap-3 rounded-lg border border-red-500/20 bg-red-500/[0.06] px-4 py-3">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />

            <div>
              <p className="text-sm font-medium text-red-300">
                Import failed
              </p>
              <p className="mt-0.5 text-sm text-red-400/80">
                {error}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Imported repository */}
      {repository && (
        <div className="border-t border-zinc-800 bg-zinc-950/40 p-6 sm:p-7">
          <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
            <div className="min-w-0">
              <div className="flex items-center gap-2.5">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-emerald-500/20 bg-emerald-500/[0.06]">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                </div>

                <div className="min-w-0">
                  <p className="text-xs font-medium uppercase tracking-wider text-emerald-400">
                    Repository imported
                  </p>

                  <h3
                    className="mt-1 truncate text-lg font-semibold text-white"
                    title={repository.name}
                  >
                    {repository.name}
                  </h3>
                </div>
              </div>

              {repository.description && (
                <p className="mt-4 max-w-2xl text-sm leading-6 text-zinc-400">
                  {repository.description}
                </p>
              )}
            </div>

            <Button
              variant="secondary"
              className="shrink-0 gap-2"
              onClick={() => navigate("/dashboard/repository")}
            >
              Open repository
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>

          <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-3 border-t border-zinc-800/70 pt-5 text-sm text-zinc-500">
            <span className="inline-flex items-center gap-2">
              <Star className="h-4 w-4" />
              {repository.stars}
            </span>

            <span className="inline-flex items-center gap-2">
              <GitFork className="h-4 w-4" />
              {repository.forks}
            </span>

            <span className="inline-flex items-center gap-2">
              <GitBranch className="h-4 w-4" />
              {repository.branch}
            </span>

            {repository.language && (
              <span className="inline-flex items-center gap-2">
                <Code2 className="h-4 w-4" />
                {repository.language}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default RepositoryImport;