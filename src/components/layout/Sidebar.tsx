import { Link } from "react-router-dom";
import {
  LayoutDashboard,
  FolderGit2,
  MessageSquare,
  FileText,
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
    icon: MessageSquare,
    label: "AI Chat",
    path: "/dashboard/chat",
  },
  {
    icon: FileText,
    label: "Documentation",
    path: "/dashboard/docs",
  },
  {
    icon: Settings,
    label: "Settings",
    path: "/dashboard/settings",
  },
];

function Sidebar() {
  return (
    <aside className="flex h-screen w-72 flex-col border-r border-zinc-800 bg-[#0B0D10] p-6">
      <h1 className="mb-10 text-2xl font-bold text-white">
        DevPilot
      </h1>

      <nav className="space-y-2">
        {menu.map((item) => {
          const Icon = item.icon;

          return (
            <Link
              key={item.label}
              to={item.path}
              className="flex items-center gap-3 rounded-xl px-4 py-3 text-zinc-400 transition hover:bg-zinc-900 hover:text-white"
            >
              <Icon size={20} />

              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}

export default Sidebar;