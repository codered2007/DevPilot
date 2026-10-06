import { useState } from "react";
import { NavLink } from "react-router-dom";
import {
  FolderGit2,
  LayoutDashboard,
  Menu,
  Settings,
  X,
} from "lucide-react";

const menu = [
  {
    icon: LayoutDashboard,
    label: "Dashboard",
    path: "/dashboard",
  },
  {
    icon: FolderGit2,
    label: "Repositories",
    path: "/dashboard/repository",
  },
  {
    icon: Settings,
    label: "Settings",
    path: "/dashboard/settings",
  },
];

function Sidebar() {
  const [mobileOpen, setMobileOpen] = useState(false);

  const closeMobileMenu = () => {
    setMobileOpen(false);
  };

  const navigation = (
    <nav className="flex-1 px-3 py-6">
      <p className="mb-3 px-3 text-[11px] font-semibold uppercase tracking-wider text-zinc-600">
        Workspace
      </p>

      <div className="space-y-1">
        {menu.map((item) => {
          const Icon = item.icon;

          return (
            <NavLink
              key={item.label}
              to={item.path}
              end={item.path === "/dashboard"}
              onClick={closeMobileMenu}
              className={({ isActive }) =>
                `group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-zinc-900 text-white"
                    : "text-zinc-400 hover:bg-zinc-900/70 hover:text-zinc-200"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon
                    className={`h-[18px] w-[18px] ${
                      isActive
                        ? "text-blue-400"
                        : "text-zinc-500 group-hover:text-zinc-300"
                    }`}
                  />

                  <span>{item.label}</span>
                </>
              )}
            </NavLink>
          );
        })}
      </div>
    </nav>
  );

  const brand = (
    <div className="flex h-20 items-center border-b border-zinc-800/80 px-6">
      <NavLink
        to="/dashboard"
        onClick={closeMobileMenu}
        className="flex items-center gap-2.5 transition-opacity hover:opacity-90"
      >
        <span className="font-mono text-sm font-bold tracking-tight text-blue-400">
          &gt;_
        </span>

        <span className="text-xl font-semibold tracking-tight text-white">
          DevPilot
        </span>
      </NavLink>
    </div>
  );

  const footer = (
    <div className="border-t border-zinc-800/80 p-4">
      <p className="px-2 text-xs text-zinc-600">
        AI-powered developer workspace
      </p>
    </div>
  );

  return (
    <>
      {/* Mobile menu button */}
      <button
        type="button"
        aria-label="Open navigation"
        aria-expanded={mobileOpen}
        onClick={() => setMobileOpen(true)}
        className="fixed left-4 top-4 z-40 flex h-10 w-10 items-center justify-center rounded-lg border border-zinc-800 bg-[#0B0D10] text-zinc-400 shadow-lg transition-colors hover:bg-zinc-900 hover:text-white lg:hidden"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Mobile backdrop */}
      {mobileOpen && (
        <button
          type="button"
          aria-label="Close navigation"
          onClick={closeMobileMenu}
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-[1px] lg:hidden"
        />
      )}

      {/* Mobile sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-zinc-800/80 bg-[#0B0D10] shadow-2xl transition-transform duration-200 lg:hidden ${
          mobileOpen
            ? "translate-x-0"
            : "-translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between border-b border-zinc-800/80">
          {brand}

          <button
            type="button"
            aria-label="Close navigation"
            onClick={closeMobileMenu}
            className="mr-4 rounded-lg p-2 text-zinc-500 transition-colors hover:bg-zinc-900 hover:text-white"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {navigation}

        {footer}
      </aside>

      {/* Desktop sidebar */}
      <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-zinc-800/80 bg-[#0B0D10] lg:flex">
        {brand}

        {navigation}

        {footer}
      </aside>
    </>
  );
}

export default Sidebar;