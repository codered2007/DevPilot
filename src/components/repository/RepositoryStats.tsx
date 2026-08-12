interface Props {
  stats: ReturnType<typeof import("../../utils/repositoryStats").getRepositoryStats>;
}

function RepositoryStats({ stats }: Props) {
  const cards = [
    ["📁 Folders", stats.folders],
    ["📄 Files", stats.files],
    ["📘 TypeScript", stats.ts + stats.tsx],
    ["🟨 JavaScript", stats.js + stats.jsx],
    ["📝 Markdown", stats.md],
    ["🐍 Python", stats.py],
    ["☕ Java", stats.java],
    ["📦 JSON", stats.json],
  ];

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {cards.map(([title, value]) => (
        <div
          key={String(title)}
          className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5"
        >
          <p className="text-sm text-zinc-400">
            {title}
          </p>

          <h2 className="mt-2 text-3xl font-bold">
            {value}
          </h2>
        </div>
      ))}
    </div>
  );
}

export default RepositoryStats;