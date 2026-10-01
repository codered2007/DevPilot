import { motion } from "framer-motion";
import { ArrowRight, Code2, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import Navbar from "../../components/layout/Navbar";

function About() {
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

        <div className="relative mx-auto max-w-5xl px-6 py-24 lg:px-8">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mx-auto max-w-3xl text-center"
          >
            <p className="mb-4 text-sm font-medium text-blue-400">
              About DevPilot
            </p>

            <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl lg:text-6xl">
              Understand code.
              <br />
              <span className="text-stone-300">
                Build with confidence.
              </span>
            </h1>

            <p className="mx-auto mt-6 max-w-2xl text-base leading-7 text-zinc-400 sm:text-lg">
              DevPilot is an AI-powered developer workspace designed to make
              unfamiliar codebases easier to explore, understand, analyze,
              and improve.
            </p>
          </motion.div>

          {/* What is DevPilot */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.15 }}
            className="mt-20 grid gap-px overflow-hidden rounded-xl border border-zinc-800/80 bg-zinc-800/80 md:grid-cols-2"
          >
            <div className="bg-[#0D1117] p-8 sm:p-10">
              <div className="mb-5 flex h-11 w-11 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-900 text-blue-400">
                <Code2 className="h-5 w-5" />
              </div>

              <h2 className="text-xl font-semibold text-white">
                Why DevPilot?
              </h2>

              <p className="mt-4 text-sm leading-7 text-zinc-500">
                Large repositories can be difficult to understand, especially
                when you are joining an existing project or working with
                unfamiliar technologies.
              </p>

              <p className="mt-4 text-sm leading-7 text-zinc-500">
                DevPilot brings the tools needed to understand those
                repositories into a single workspace instead of making
                developers jump between different tools.
              </p>
            </div>

            <div className="bg-[#0D1117] p-8 sm:p-10">
              <div className="mb-5 flex h-11 w-11 items-center justify-center rounded-lg border border-zinc-800 bg-zinc-900 text-blue-400">
                <Sparkles className="h-5 w-5" />
              </div>

              <h2 className="text-xl font-semibold text-white">
                What makes it different?
              </h2>

              <p className="mt-4 text-sm leading-7 text-zinc-500">
                DevPilot is designed around the repository itself. AI
                explanations, codebase conversations, architecture analysis,
                reviews, dependency analysis, and security analysis all work
                with the context of the project.
              </p>

              <p className="mt-4 text-sm leading-7 text-zinc-500">
                The goal is not simply to generate code, but to help developers
                understand the code they already have.
              </p>
            </div>
          </motion.section>

          {/* Workflow */}
          <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.25 }}
            className="mt-16"
          >
            <div className="mb-8">
              <p className="text-sm font-medium text-blue-400">
                Built around your workflow
              </p>

              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-white">
                From repository to understanding.
              </h2>
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              <div className="rounded-xl border border-zinc-800 bg-[#0D1117] p-6">
                <span className="font-mono text-sm text-blue-400">01</span>

                <h3 className="mt-4 text-base font-semibold text-white">
                  Connect
                </h3>

                <p className="mt-2 text-sm leading-6 text-zinc-500">
                  Connect a GitHub repository and explore its files and
                  structure.
                </p>
              </div>

              <div className="rounded-xl border border-zinc-800 bg-[#0D1117] p-6">
                <span className="font-mono text-sm text-blue-400">02</span>

                <h3 className="mt-4 text-base font-semibold text-white">
                  Analyze
                </h3>

                <p className="mt-2 text-sm leading-6 text-zinc-500">
                  Analyze architecture, dependencies, security, and code
                  quality.
                </p>
              </div>

              <div className="rounded-xl border border-zinc-800 bg-[#0D1117] p-6">
                <span className="font-mono text-sm text-blue-400">03</span>

                <h3 className="mt-4 text-base font-semibold text-white">
                  Understand
                </h3>

                <p className="mt-2 text-sm leading-6 text-zinc-500">
                  Ask questions and use the repository context to understand
                  how everything fits together.
                </p>
              </div>
            </div>
          </motion.section>

          {/* CTA */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="mt-20 flex flex-col items-center text-center"
          >
            <h2 className="text-2xl font-semibold text-white">
              Explore DevPilot
            </h2>

            <p className="mt-3 text-sm text-zinc-500">
              See what DevPilot can do with your codebase.
            </p>

            <div className="mt-6 flex flex-col gap-3 sm:flex-row">
              <Link
                to="/login"
                className="group inline-flex items-center justify-center rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-500"
              >
                Get Started
                <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-0.5" />
              </Link>

              <a
                href="https://github.com/codered2007/DevPilot"
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center justify-center gap-2 rounded-lg border border-zinc-800 bg-zinc-900/50 px-5 py-2.5 text-sm font-medium text-zinc-300 transition-colors hover:border-zinc-700 hover:bg-zinc-900 hover:text-white"
              >
                <span className="font-mono text-xs">git</span>
View on GitHub
              </a>
            </div>
          </motion.div>
        </div>
      </main>
    </div>
  );
}

export default About;