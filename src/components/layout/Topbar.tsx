import { Bell, Search } from "lucide-react";

function Topbar() {
  return (
    <header className="flex h-20 items-center justify-between border-b border-zinc-800 px-8">
      <div className="flex items-center gap-3 rounded-xl bg-zinc-900 px-4 py-3">
        <Search size={18} />

        <input
          placeholder="Search repositories..."
          className="bg-transparent outline-none"
        />
      </div>

      <Bell className="text-zinc-400" />
    </header>
  );
}

export default Topbar;