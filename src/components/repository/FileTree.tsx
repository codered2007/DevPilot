import { useMemo, useState } from "react";
import {
  ChevronDown,
  ChevronRight,
  Folder,
  FolderOpen,
  File,
  Search,
} from "lucide-react";
import type { TreeNode } from "../../utils/buildFileTree";

interface Props {
  nodes: TreeNode[];
  onSelectFile: (path: string) => void;
}

interface TreeItemProps {
  node: TreeNode;
  level?: number;
  selectedFile: string;
  onSelectFile: (path: string) => void;
}

function filterTree(nodes: TreeNode[], search: string): TreeNode[] {
  if (!search) return nodes;

  return nodes
    .map((node) => {
      if (node.type === "file") {
        return node.path.toLowerCase().includes(search.toLowerCase())
          ? node
          : null;
      }

      const children = filterTree(node.children ?? [], search);

      if (
        children.length > 0 ||
        node.name.toLowerCase().includes(search.toLowerCase())
      ) {
        return {
          ...node,
          children,
        };
      }

      return null;
    })
    .filter(Boolean) as TreeNode[];
}

function TreeItem({
  node,
  level = 0,
  selectedFile,
  onSelectFile,
}: TreeItemProps) {
  const [open, setOpen] = useState(true);

  if (node.type === "file") {
    const active = selectedFile === node.path;

    return (
      <button
        type="button"
        onClick={() => onSelectFile(node.path)}
        style={{ paddingLeft: `${level * 14 + 10}px` }}
        className={`group flex w-full items-center gap-2 rounded-md py-1.5 pr-2 text-left text-sm transition-colors ${
          active
            ? "bg-blue-500/10 text-blue-300 ring-1 ring-inset ring-blue-500/20"
            : "text-zinc-400 hover:bg-zinc-800/70 hover:text-zinc-200"
        }`}
      >
        <File
          className={`h-4 w-4 shrink-0 ${
            active
              ? "text-blue-400"
              : "text-zinc-600 group-hover:text-zinc-400"
          }`}
        />

        <span className="truncate">{node.name}</span>
      </button>
    );
  }

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        style={{ paddingLeft: `${level * 14 + 6}px` }}
        className="group flex w-full items-center gap-1.5 rounded-md py-1.5 pr-2 text-left text-sm text-zinc-400 transition-colors hover:bg-zinc-800/70 hover:text-zinc-200"
      >
        {open ? (
          <ChevronDown className="h-3.5 w-3.5 shrink-0 text-zinc-600" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5 shrink-0 text-zinc-600" />
        )}

        {open ? (
          <FolderOpen className="h-4 w-4 shrink-0 text-blue-400" />
        ) : (
          <Folder className="h-4 w-4 shrink-0 text-blue-400" />
        )}

        <span className="truncate">{node.name}</span>
      </button>

      {open &&
        node.children?.map((child) => (
          <TreeItem
            key={child.path}
            node={child}
            level={level + 1}
            selectedFile={selectedFile}
            onSelectFile={onSelectFile}
          />
        ))}
    </>
  );
}

function FileTree({ nodes, onSelectFile }: Props) {
  const [search, setSearch] = useState("");
  const [selectedFile, setSelectedFile] = useState("");

  const filteredTree = useMemo(
    () => filterTree(nodes, search),
    [nodes, search]
  );

  function handleSelect(path: string) {
    setSelectedFile(path);
    onSelectFile(path);
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-zinc-800/80 bg-zinc-900/60">
      {/* Header */}
      <div className="border-b border-zinc-800/80 px-4 py-3.5">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-zinc-200">
              Explorer
            </h2>

            <p className="mt-0.5 text-xs text-zinc-600">
              Repository files
            </p>
          </div>

          <span className="rounded-md bg-zinc-800 px-2 py-1 text-[10px] font-medium uppercase tracking-wide text-zinc-500">
            Files
          </span>
        </div>
      </div>

      {/* Search */}
      <div className="border-b border-zinc-800/80 p-3">
        <div className="flex items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-950/70 px-3 py-2 transition-colors focus-within:border-zinc-700">
          <Search className="h-4 w-4 shrink-0 text-zinc-600" />

          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search files..."
            className="w-full bg-transparent text-sm text-zinc-200 outline-none placeholder:text-zinc-600"
          />

          {search && (
            <button
              type="button"
              onClick={() => setSearch("")}
              className="text-xs text-zinc-600 transition-colors hover:text-zinc-300"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* File Tree */}
      <div className="max-h-[650px] overflow-y-auto p-2">
        {filteredTree.length === 0 ? (
          <div className="px-4 py-10 text-center">
            <File className="mx-auto h-6 w-6 text-zinc-700" />

            <p className="mt-3 text-sm text-zinc-500">
              No files found.
            </p>

            {search && (
              <p className="mt-1 text-xs text-zinc-600">
                Try a different search term.
              </p>
            )}
          </div>
        ) : (
          filteredTree.map((node) => (
            <TreeItem
              key={node.path}
              node={node}
              selectedFile={selectedFile}
              onSelectFile={handleSelect}
            />
          ))
        )}
      </div>
    </div>
  );
}

export default FileTree;