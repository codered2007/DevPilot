interface CodeViewerProps {
  file?: string;
}

function CodeViewer({
  file,
}: CodeViewerProps) {
  return (
    <div className="rounded-3xl border border-zinc-800 bg-zinc-900 p-6">
      <h2 className="mb-6 text-xl font-bold">
        Code Viewer
      </h2>

      {file ? (
        <pre className="overflow-auto rounded-xl bg-black p-4 text-sm">
          {file}
        </pre>
      ) : (
        <p className="text-zinc-400">
          Select a file to view it.
        </p>
      )}
    </div>
  );
}

export default CodeViewer;