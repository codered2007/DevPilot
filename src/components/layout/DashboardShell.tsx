import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

function DashboardShell() {
  return (
    <div className="flex">
      <Sidebar />

      <div className="flex min-h-screen flex-1 flex-col bg-[#111418] text-white">
        <Topbar />

        <main className="flex-1 p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default DashboardShell;