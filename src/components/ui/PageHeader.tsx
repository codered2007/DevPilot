interface PageHeaderProps {
  title: string;
  description: string;
}

function PageHeader({
  title,
  description,
}: PageHeaderProps) {
  return (
    <div>
      <h1 className="text-4xl font-bold">
        {title}
      </h1>

      <p className="mt-2 text-zinc-400">
        {description}
      </p>
    </div>
  );
}

export default PageHeader;