import RepositoryImport from "../../components/repository/RepositoryImport";
import RepositoryCard from "../../components/repository/RepositoryCard";
import EmptyState from "../../components/dashboard/EmptyState";

function Dashboard() {
  return (
    <div className="space-y-10">
      {/* Welcome */}
      <div>
        <h1 className="text-4xl font-bold">
          Welcome back 👋
        </h1>

        <p className="mt-2 text-zinc-400">
          Import your first repository to start using DevPilot.
        </p>
      </div>

      {/* Repository Import */}
      <RepositoryImport />

      {/* Dashboard Content */}
      <div className="grid gap-6 lg:grid-cols-2">
        <RepositoryCard
          name="DevPilot"
          description="AI Software Engineering Workspace"
          branch="main"
          stars={15}
          files={142}
          indexed={true}
        />

        <EmptyState
          title="No AI conversations"
          description="Start chatting with your code after importing a repository."
        />
      </div>
    </div>
  );
}

export default Dashboard;