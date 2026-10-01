import { Bell, LogOut, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

interface GithubUser {
  login: string;
  name: string | null;
  avatar_url: string;
}

function Topbar() {
  const navigate = useNavigate();

  const [user, setUser] = useState<GithubUser | null>(null);
  const [loggingOut, setLoggingOut] = useState(false);

  useEffect(() => {
    const fetchCurrentUser = async () => {
      try {
        const response = await fetch("http://localhost:8000/auth/me", {
          credentials: "include",
        });

        if (!response.ok) {
          return;
        }

        const data = await response.json();
        setUser(data.user);
      } catch (error) {
        console.error("Failed to fetch authenticated user:", error);
      }
    };

    fetchCurrentUser();
  }, []);

  const handleLogout = async () => {
    setLoggingOut(true);

    try {
      await fetch("http://localhost:8000/auth/logout", {
        method: "POST",
        credentials: "include",
      });
    } catch (error) {
      console.error("Logout failed:", error);
    } finally {
      navigate("/login", { replace: true });
    }
  };

  const displayName = user?.name || user?.login || "Developer";

  return (
    <header className="flex h-20 items-center justify-between border-b border-zinc-800/80 bg-[#111418] px-6 lg:px-8">
      {/* Search */}
      <div className="flex w-full max-w-md items-center gap-3 rounded-lg border border-zinc-800 bg-zinc-900/70 px-3.5 py-2.5 transition-colors focus-within:border-zinc-700">
        <Search className="h-4 w-4 shrink-0 text-zinc-500" />

        <input
          type="text"
          placeholder="Search repositories..."
          className="w-full bg-transparent text-sm text-zinc-200 outline-none placeholder:text-zinc-500"
        />

        <kbd className="hidden rounded border border-zinc-800 bg-zinc-950 px-1.5 py-0.5 font-mono text-[10px] text-zinc-500 sm:block">
          /
        </kbd>
      </div>

      {/* Account */}
      <div className="ml-6 flex items-center gap-4">
        <button
          type="button"
          aria-label="Notifications"
          className="rounded-lg p-2 text-zinc-500 transition-colors hover:bg-zinc-900 hover:text-zinc-200"
        >
          <Bell className="h-5 w-5" />
        </button>

        <div className="h-8 w-px bg-zinc-800" />

        <div className="flex items-center gap-3">
          {user?.avatar_url ? (
            <img
              src={user.avatar_url}
              alt={displayName}
              className="h-9 w-9 rounded-full border border-zinc-700"
            />
          ) : (
            <div className="h-9 w-9 animate-pulse rounded-full bg-zinc-800" />
          )}

          <div className="hidden min-w-0 sm:block">
            <p className="max-w-[140px] truncate text-sm font-medium text-zinc-200">
              {displayName}
            </p>

            {user?.login && (
              <p className="max-w-[140px] truncate text-xs text-zinc-500">
                @{user.login}
              </p>
            )}
          </div>

          <button
            type="button"
            onClick={handleLogout}
            disabled={loggingOut}
            className="inline-flex items-center gap-2 rounded-lg border border-zinc-800 px-3 py-2 text-sm text-zinc-400 transition-colors hover:border-zinc-700 hover:bg-zinc-900 hover:text-zinc-100 disabled:pointer-events-none disabled:opacity-50"
          >
            <LogOut className="h-4 w-4" />
            <span className="hidden md:inline">
              {loggingOut ? "Logging out..." : "Logout"}
            </span>
          </button>
        </div>
      </div>
    </header>
  );
}

export default Topbar;