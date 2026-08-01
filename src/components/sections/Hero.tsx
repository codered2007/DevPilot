import { motion } from "framer-motion";
import Button from "../ui/Button";
import Terminal from "../ui/Terminal";

function Hero() {
  return (
    <section className="grid min-h-[85vh] items-center gap-16 lg:grid-cols-2">
      {/* Left Content */}
      <motion.div
        initial={{ opacity: 0, x: -40 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.6 }}
      >
        <p className="mb-4 inline-flex rounded-full border border-blue-500/30 bg-blue-500/10 px-4 py-1 text-sm text-blue-400">
          AI-powered Developer Assistant
        </p>

        <h1 className="text-5xl font-bold leading-tight lg:text-7xl">
          AI that understands your code.
        </h1>

        <p className="mt-6 max-w-xl text-lg text-zinc-400">
          Import GitHub repositories, understand unfamiliar codebases,
          generate documentation, review pull requests, and chat with
          your entire project using AI.
        </p>

        <div className="mt-10 flex gap-4">
          <Button>Get Started</Button>
          <Button variant="secondary">View GitHub</Button>
        </div>
      </motion.div>

      {/* Right Content */}
      <Terminal />
    </section>
  );
}

export default Hero;