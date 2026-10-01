import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  FolderGit2,
  Settings,
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
  return (
    <aside className="sticky top-0 flex h-screen w-64 shrink-0 flex-col border-r border-zinc-800/80 bg-[#0B0D10]">
      {/* Brand */}
      <div className="flex h-20 items-center border-b border-zinc-800/80 px-6">
        <NavLink
          to="/dashboard"
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

      {/* Navigation */}
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

      {/* Footer */}
      <div className="border-t border-zinc-800/80 p-4">
        <p className="px-2 text-xs text-zinc-600">
          AI-powered developer workspace
        </p>
      </div>
    </aside>
  );
}

export default Sidebar;