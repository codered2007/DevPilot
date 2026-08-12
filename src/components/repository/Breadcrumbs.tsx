interface Props {
  path: string;
}

function Breadcrumbs({ path }: Props) {
  if (!path) return null;

  const parts = path.split("/");

  return (
    <div className="mb-3 flex flex-wrap items-center gap-2 text-sm text-zinc-400">
      {parts.map((part, index) => (
        <div
          key={index}
          className="flex items-center gap-2"
        >
          <span>{part}</span>

          {index < parts.length - 1 && (
            <span className="text-zinc-600">›</span>
          )}
        </div>
      ))}
    </div>
  );
}

export default Breadcrumbs;