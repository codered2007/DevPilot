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
        onClick={() => onSelectFile(node.path)}
        style={{ paddingLeft: `${level * 16 + 8}px` }}
        className={`flex w-full items-center gap-2 rounded-lg py-2 text-left transition
          ${
            active
              ? "bg-blue-600 text-white"
              : "hover:bg-zinc-800 text-zinc-300"
          }`}
      >
        <File size={16} />
        <span className="truncate">{node.name}</span>
      </button>
    );
  }

  return (
    <>
      <button
        onClick={() => setOpen(!open)}
        style={{ paddingLeft: `${level * 16 + 8}px` }}
        className="flex w-full items-center gap-2 rounded-lg py-2 text-left transition hover:bg-zinc-800"
      >
        {open ? (
          <ChevronDown size={16} />
        ) : (
          <ChevronRight size={16} />
        )}

        {open ? (
          <FolderOpen size={16} className="text-yellow-400" />
        ) : (
          <Folder size={16} className="text-yellow-400" />
        )}

        <span>{node.name}</span>
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
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
      <div className="mb-4 flex items-center gap-2 rounded-lg bg-zinc-800 px-3 py-2">
        <Search size={18} className="text-zinc-400" />

        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search files..."
          className="w-full bg-transparent outline-none"
        />
      </div>

      <div className="max-h-[650px] overflow-y-auto">
        {filteredTree.length === 0 ? (
          <p className="text-center text-zinc-500">
            No files found.
          </p>
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