interface DashboardCardProps {
  title: string;
  value: string;
  subtitle: string;
}

function DashboardCard({
  title,
  value,
  subtitle,
}: DashboardCardProps) {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6">
      <p className="text-sm text-zinc-400">
        {title}
      </p>

      <h2 className="mt-3 text-4xl font-bold">
        {value}
      </h2>

      <p className="mt-2 text-sm text-zinc-500">
        {subtitle}
      </p>
    </div>
  );
}

export default DashboardCard;