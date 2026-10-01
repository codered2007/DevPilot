import {
  Bot,
  GitBranch,
  Network,
  Search,
  ShieldCheck,
  ClipboardCheck,
  ArrowRight,
} from "lucide-react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import Navbar from "../../components/layout/Navbar";

const features = [
  {
    icon: Search,
    title: "Repository Explorer",
    description:
      "Navigate GitHub repositories, inspect files, and understand how the codebase is organized.",
  },
  {
    icon: Bot,
    title: "AI Codebase Chat",
    description:
      "Ask questions about a repository and get answers grounded in the actual codebase.",
  },
  {
    icon: Network,
    title: "Architecture Analysis",
    description:
      "Visualize how modules and components connect to understand the structure of unfamiliar projects.",
  },
  {
    icon: ClipboardCheck,
    title: "AI Code Review",
    description:
      "Analyze repositories for code quality issues, potential problems, and actionable improvements.",
  },
  {
    icon: GitBranch,
    title: "Dependency Analysis",
    description:
      "Inspect project dependencies and understand the technologies your repository relies on.",
  },
  {
    icon: ShieldCheck,
    title: "Security Analysis",
    description:
      "Scan dependencies for known vulnerabilities and surface security findings with useful context.",
  },
];

function Features() {
  return (
    <div className="min-h-screen bg-[#0D1117] text-white">
      <Navbar />

      <main className="relative overflow-hidden">
        {/* Background texture */}
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.18]"
          style={{
            backgroundImage: `
              radial-gradient(
                circle at 20% 20%,
                rgba(88, 166, 255, 0.12) 1px,
                transparent 1px
              ),
              radial-gradient(
                circle at 80% 60%,
                rgba(139, 148, 158, 0.08) 1px,
                transparent 1px
              )
            `,
            backgroundSize: "32px 32px, 48px 48px",
          }}
        />

        {/* Top glow */}
        <div
          className="pointer-events-none absolute left-1/2 top-0 h-[500px] w-[900px] -translate-x-1/2 opacity-60"
          style={{
            background:
              "radial-gradient(ellipse at center top, rgba(56, 139, 253, 0.10), transparent 65%)",
          }}
        />

        <div className="relative mx-auto max-w-6xl px-6 py-24 lg:px-8">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mx-auto max-w-3xl text-center"
          >
            <p className="mb-4 text-sm font-medium text-blue-400">
              DevPilot features
            </p>

            <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl lg:text-6xl">
              Everything you need to
              <br />
              <span className="text-stone-300">
                understand a codebase.
              </span>
            </h1>

            <p className="mx-auto mt-6 max-w-2xl text-base leading-7 text-zinc-400 sm:text-lg">
              Explore, analyze, review, and understand GitHub repositories
              from one AI-powered developer workspace.
            </p>
          </motion.div>

          {/* Features */}
          <div className="mt-20 grid overflow-hidden rounded-xl border border-zinc-800/80 bg-zinc-800/70 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature, index) => {
              const Icon = feature.icon;

              return (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{
                    duration: 0.4,
                    delay: 0.08 * index,
                  }}
                  className="border-b border-r border-zinc-800/80 bg-[#0D1117] p-8 transition-colors duration-200 hover:bg-[#11161D]"
                >
                  <div className="mb-6 flex h-11 w-11 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-900 text-blue-400">
                    <Icon className="h-5 w-5" />
                  </div>

                  <h2 className="text-base font-semibold text-white">
                    {feature.title}
                  </h2>

                  <p className="mt-3 text-sm leading-6 text-zinc-500">
                    {feature.description}
                  </p>
                </motion.div>
              );
            })}
          </div>

          {/* Bottom CTA */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.6 }}
            className="mt-20 flex flex-col items-center text-center"
          >
            <p className="text-sm text-zinc-500">
              Ready to explore your codebase?
            </p>

            <Link
              to="/login"
              className="group mt-4 inline-flex items-center rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-500"
            >
              Get Started
              <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-0.5" />
            </Link>
          </motion.div>
        </div>
      </main>
    </div>
  );
}

export default Features;