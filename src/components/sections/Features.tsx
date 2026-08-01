import {
  Brain,
  GitBranch,
  FileText,
  Search,
} from "lucide-react";

const features = [
  {
    icon: Brain,
    title: "AI Code Understanding",
    description:
      "Ask questions about any repository and get context-aware answers.",
  },
  {
    icon: GitBranch,
    title: "GitHub Integration",
    description:
      "Import repositories directly from GitHub in one click.",
  },
  {
    icon: FileText,
    title: "Documentation",
    description:
      "Generate clean documentation automatically.",
  },
  {
    icon: Search,
    title: "Bug Detection",
    description:
      "Find potential issues and understand complex code faster.",
  },
];

function Features() {
  return (
    <section className="py-24">
      <h2 className="mb-12 text-center text-4xl font-bold">
        Everything you need
      </h2>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {features.map((feature) => {
          const Icon = feature.icon;

          return (
            <div
              key={feature.title}
              className="rounded-2xl border border-zinc-800 bg-zinc-900 p-6 transition hover:border-blue-500"
            >
              <Icon className="mb-5 h-10 w-10 text-blue-500" />

              <h3 className="mb-3 text-xl font-semibold">
                {feature.title}
              </h3>

              <p className="text-zinc-400">
                {feature.description}
              </p>
            </div>
          );
        })}
      </div>
    </section>
  );
}

export default Features;