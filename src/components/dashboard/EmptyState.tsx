import { FolderGit2 } from "lucide-react";

interface EmptyStateProps {
  title: string;
  description: string;
}

function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <div className="flex h-64 flex-col items-center justify-center rounded-2xl border border-dashed border-zinc-700 bg-zinc-900/50 text-center">
      <FolderGit2
        size={42}
        className="mb-4 text-zinc-500"
      />

      <h3 className="text-xl font-semibold">
        {title}
      </h3>

      <p className="mt-2 max-w-sm text-zinc-400">
        {description}
      </p>
    </div>
  );
}

export default EmptyState;