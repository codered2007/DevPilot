import Card from "../ui/Card";

function RepositoryOverview() {
  return (
    <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
      <Card className="p-6">
        <p className="text-zinc-400">Files</p>
        <h2 className="mt-2 text-3xl font-bold">142</h2>
      </Card>

      <Card className="p-6">
        <p className="text-zinc-400">Functions</p>
        <h2 className="mt-2 text-3xl font-bold">63</h2>
      </Card>

      <Card className="p-6">
        <p className="text-zinc-400">Classes</p>
        <h2 className="mt-2 text-3xl font-bold">18</h2>
      </Card>

      <Card className="p-6">
        <p className="text-zinc-400">AI Status</p>
        <h2 className="mt-2 text-3xl font-bold text-green-400">
          Ready
        </h2>
      </Card>
    </div>
  );
}

export default RepositoryOverview;