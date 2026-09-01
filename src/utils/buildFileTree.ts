export interface TreeNode {
  name: string;
  path: string;
  type: "file" | "folder";
  children?: TreeNode[];
}

interface FileItem {
  path: string;
  type: string;
}

export function buildFileTree(
  files: FileItem[]
): TreeNode[] {
  const root: TreeNode[] = [];

  for (const file of files) {
    const parts = file.path.split("/");

    let current = root;
    let currentPath = "";

    parts.forEach((part, index) => {
      currentPath = currentPath
        ? `${currentPath}/${part}`
        : part;

      const isLast = index === parts.length - 1;

      let node = current.find(
        (item) => item.name === part
      );

      if (!node) {
        const isFolder =
          !isLast || file.type === "tree";

        node = {
          name: part,
          path: currentPath,
          type: isFolder ? "folder" : "file",
          ...(isFolder ? { children: [] } : {}),
        };

        current.push(node);
      }

      if (node.children) {
        current = node.children;
      }
    });
  }

  return root;
}