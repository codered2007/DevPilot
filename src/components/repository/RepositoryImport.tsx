import { useState } from "react";
import { FaGithub } from "react-icons/fa";
import { useNavigate } from "react-router-dom";

import Button from "../ui/Button";
import Input from "../ui/Input";
import { importRepository } from "../../services/api";
import { useRepository } from "../../context/RepositoryContext";

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
    <div className="rounded-3xl border border-zinc-800 bg-zinc-900 p-8">
      <h2 className="text-3xl font-bold">
        Import Repository
      </h2>

      <p className="mt-3 text-zinc-400">
        Import any public GitHub repository and let DevPilot analyze
        your codebase.
      </p>

      <div className="mt-8">
        <label className="mb-3 block text-sm text-zinc-400">
          GitHub Repository URL
        </label>

        <Input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://github.com/facebook/react"
        />
      </div>

      <Button
        onClick={handleImport}
        disabled={loading}
        className="mt-6 flex items-center gap-2"
      >
        <FaGithub />
        {loading ? "Importing..." : "Import Repository"}
      </Button>

      {error && (
        <p className="mt-4 text-sm text-red-400">
          {error}
        </p>
      )}

      {repository && (
        <div className="mt-8 rounded-2xl border border-zinc-800 bg-[#0B0D10] p-6">
          <h3 className="text-2xl font-bold">
            {repository.name}
          </h3>

          <p className="mt-2 text-zinc-400">
            {repository.description}
          </p>

          <div className="mt-6 flex flex-wrap gap-6 text-sm text-zinc-400">
            <span>⭐ {repository.stars}</span>
            <span>🍴 {repository.forks}</span>
            <span>🌿 {repository.branch}</span>
            <span>{repository.language}</span>
          </div>

          <Button
            className="mt-6"
            onClick={() => navigate("/dashboard/repository")}
          >
            Analyze Repository
          </Button>
        </div>
      )}
    </div>
  );
}

export default RepositoryImport;