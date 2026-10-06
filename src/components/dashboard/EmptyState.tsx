import { MessageSquareCode } from "lucide-react";

interface EmptyStateProps {
  title: string;
  description: string;
}

function EmptyState({
  title,
  description,
}: EmptyStateProps) {
  return (
    <div className="flex h-full min-h-[250px] flex-col items-center justify-center rounded-xl border border-dashed border-zinc-800 bg-[#111418] px-6 py-8 text-center">
      <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-950">
        <MessageSquareCode className="h-5 w-5 text-zinc-500" />
      </div>

      <h3 className="mt-4 text-base font-semibold text-zinc-200">
        {title}
      </h3>

      <p className="mt-2 max-w-xs text-sm leading-6 text-zinc-500">
        {description}
      </p>
    </div>
  );
}

export default EmptyState;