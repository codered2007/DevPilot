import { Link, NavLink } from "react-router-dom";
import { ChevronDown } from "lucide-react";

function Navbar() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-zinc-800/80 bg-[#0B0D10]">
      <div className="mx-auto flex h-16 max-w-7xl items-center px-6 lg:px-8">
        {/* Logo */}
        <Link
          to="/"
          className="flex items-center gap-2.5 text-white transition-opacity hover:opacity-90"
        >
          <span className="font-mono text-sm font-bold tracking-tight text-blue-400">
            &gt;_
          </span>

          <span className="text-xl font-semibold tracking-tight text-white">
            DevPilot
          </span>
        </Link>

        {/* Navigation */}
        <nav className="ml-10 hidden items-center gap-1 md:flex">
          <NavLink
            to="/features"
            className={({ isActive }) =>
              `rounded-md border px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? "border-zinc-800 bg-zinc-900 text-white"
                  : "border-transparent text-zinc-400 hover:bg-zinc-900 hover:text-white"
              }`
            }
          >
            Features
          </NavLink>

          <NavLink
            to="/about"
            className={({ isActive }) =>
              `rounded-md border px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? "border-zinc-800 bg-zinc-900 text-white"
                  : "border-transparent text-zinc-400 hover:bg-zinc-900 hover:text-white"
              }`
            }
          >
            About
          </NavLink>

          <a
            href="https://github.com/codered2007/DevPilot"
            target="_blank"
            rel="noreferrer"
            className="rounded-md border border-transparent px-3 py-2 text-sm font-medium text-zinc-400 transition-colors hover:bg-zinc-900 hover:text-white"
          >
            GitHub
          </a>
        </nav>

        <div className="flex-1" />

        {/* Actions */}
        <div className="flex items-center gap-2">
          <Link
            to="/login"
            className="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-blue-500"
          >
            Get Started
          </Link>

          <button
            type="button"
            aria-label="Open navigation menu"
            className="ml-1 rounded-lg p-2 text-zinc-400 transition-colors hover:bg-zinc-900 hover:text-white md:hidden"
          >
            <ChevronDown className="h-5 w-5" />
          </button>
        </div>
      </div>
    </header>
  );
}

export default Navbar;