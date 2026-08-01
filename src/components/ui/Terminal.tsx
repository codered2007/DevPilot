import { motion } from "framer-motion";

function Terminal() {
  return (
    <motion.div
      initial={{ opacity: 0, x: 40 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{
        duration: 0.6,
        delay: 0.2,
      }}
      className="overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900 shadow-2xl"
    >
      {/* Header */}
      <div className="flex items-center gap-2 border-b border-zinc-800 px-5 py-4">
        <div className="h-3 w-3 rounded-full bg-red-500" />
        <div className="h-3 w-3 rounded-full bg-yellow-500" />
        <div className="h-3 w-3 rounded-full bg-green-500" />

        <span className="ml-3 text-sm text-zinc-500">
          devpilot-terminal
        </span>
      </div>

      {/* Body */}
      <div className="space-y-4 p-6 font-mono text-sm leading-7">
        <div>
          <span className="text-blue-400">$</span>{" "}
          <span>analyze repository</span>
        </div>

        <div className="text-emerald-400">
          ✓ Repository indexed successfully
        </div>

        <div>
          <span className="text-blue-400">$</span>{" "}
          <span>explain auth.ts</span>
        </div>

        <div className="rounded-lg bg-zinc-800/60 p-3 text-zinc-300">
          Authentication uses JWT middleware with protected routes and
          refresh tokens.
        </div>

        <div>
          <span className="text-blue-400">$</span>{" "}
          <span>find bugs</span>
        </div>

        <div className="text-yellow-400">
          ⚠ 3 possible issues detected
        </div>
      </div>
    </motion.div>
  );
}

export default Terminal;