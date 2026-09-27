import {
  Background,
  Controls,
  ReactFlow,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import type {
  ArchitectureDependency,
} from "../services/api";

interface ArchitectureGraphProps {
  dependencies: ArchitectureDependency[];
  onFileSelect?: (path: string) => void;
}

const NODE_WIDTH = 280;
const NODE_HEIGHT = 90;
const HORIZONTAL_GAP = 100;
const VERTICAL_GAP = 90;

function isLocalFile(path: string) {
  return (
    path.includes("/") ||
    path.endsWith(".py") ||
    path.endsWith(".js") ||
    path.endsWith(".jsx") ||
    path.endsWith(".ts") ||
    path.endsWith(".tsx") ||
    path.endsWith(".java") ||
    path.endsWith(".go") ||
    path.endsWith(".rs") ||
    path.endsWith(".cpp") ||
    path.endsWith(".c")
  );
}

function normalizeDependencies(
  dependencies: ArchitectureDependency[]
) {
  return [...dependencies].sort((a, b) => {
    const sourceCompare =
      a.source.localeCompare(b.source);

    if (sourceCompare !== 0) {
      return sourceCompare;
    }

    const targetCompare =
      a.target.localeCompare(b.target);

    if (targetCompare !== 0) {
      return targetCompare;
    }

    return a.type.localeCompare(b.type);
  });
}

function buildLayers(
  dependencies: ArchitectureDependency[]
): Map<string, number> {
  const nodes = new Set<string>();
  const outgoing = new Map<string, string[]>();
  const incomingCount = new Map<string, number>();

  for (const dependency of dependencies) {
    nodes.add(dependency.source);
    nodes.add(dependency.target);

    if (!outgoing.has(dependency.source)) {
      outgoing.set(dependency.source, []);
    }

    outgoing
      .get(dependency.source)!
      .push(dependency.target);

    if (!incomingCount.has(dependency.target)) {
      incomingCount.set(dependency.target, 0);
    }

    incomingCount.set(
      dependency.target,
      incomingCount.get(dependency.target)! + 1
    );

    if (!incomingCount.has(dependency.source)) {
      incomingCount.set(dependency.source, 0);
    }
  }

  for (const [source, targets] of outgoing) {
    outgoing.set(
      source,
      [...targets].sort((a, b) =>
        a.localeCompare(b)
      )
    );
  }

  const layers = new Map<string, number>();
  const queue: string[] = [];

  const sortedNodes = Array.from(nodes).sort(
    (a, b) => a.localeCompare(b)
  );

  for (const node of sortedNodes) {
    if ((incomingCount.get(node) ?? 0) === 0) {
      queue.push(node);
      layers.set(node, 0);
    }
  }

  let processed = 0;

  while (queue.length > 0) {
    const current = queue.shift()!;
    processed += 1;

    const currentLayer =
      layers.get(current) ?? 0;

    for (const target of outgoing.get(current) ?? []) {
      const nextLayer = currentLayer + 1;

      layers.set(
        target,
        Math.max(
          layers.get(target) ?? 0,
          nextLayer
        )
      );

      const remaining =
        (incomingCount.get(target) ?? 0) - 1;

      incomingCount.set(target, remaining);

      if (remaining === 0) {
        queue.push(target);

        queue.sort((a, b) =>
          a.localeCompare(b)
        );
      }
    }
  }

  /*
   * Handle cyclic dependencies deterministically.
   */
  if (processed < nodes.size) {
    const unprocessed = sortedNodes.filter(
      (node) => !layers.has(node)
    );

    const maxLayer = Math.max(
      -1,
      ...Array.from(layers.values())
    );

    unprocessed.forEach((node, index) => {
      layers.set(
        node,
        maxLayer + 1 + index
      );
    });
  }

  return layers;
}

function createNodes(
  dependencies: ArchitectureDependency[]
): Node[] {
  const paths = Array.from(
    new Set(
      dependencies.flatMap((dependency) => [
        dependency.source,
        dependency.target,
      ])
    )
  ).sort((a, b) => a.localeCompare(b));

  const layers = buildLayers(dependencies);

  const nodesByLayer = new Map<
    number,
    string[]
  >();

  for (const path of paths) {
    const layer = layers.get(path) ?? 0;

    if (!nodesByLayer.has(layer)) {
      nodesByLayer.set(layer, []);
    }

    nodesByLayer.get(layer)!.push(path);
  }

  const sortedLayers = Array.from(
    nodesByLayer.keys()
  ).sort((a, b) => a - b);

  const positions = new Map<
    string,
    { x: number; y: number }
  >();

  for (const layer of sortedLayers) {
    const layerNodes =
      nodesByLayer.get(layer)!;

    layerNodes.sort((a, b) =>
      a.localeCompare(b)
    );

    const layerWidth =
      layerNodes.length * NODE_WIDTH +
      Math.max(0, layerNodes.length - 1) *
        HORIZONTAL_GAP;

    const startX = Math.max(
      40,
      (1400 - layerWidth) / 2
    );

    layerNodes.forEach((path, index) => {
      positions.set(path, {
        x:
          startX +
          index *
            (NODE_WIDTH + HORIZONTAL_GAP),
        y:
          layer *
          (NODE_HEIGHT + VERTICAL_GAP),
      });
    });
  }

  return paths.map((path) => {
    const position = positions.get(path) ?? {
      x: 40,
      y: 40,
    };

    const local = isLocalFile(path);

    return {
      id: path,
      position,
      data: {
        label: (
          <div
            style={{
              width: NODE_WIDTH - 32,
              fontSize: 12,
              lineHeight: 1.5,
            }}
          >
            <div
              style={{
                fontWeight: 600,
                marginBottom: 4,
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
              title={path}
            >
              {path}
            </div>

            <div
              style={{
                fontSize: 11,
                opacity: 0.65,
              }}
            >
              {local
                ? "Source file"
                : "External dependency"}
            </div>
          </div>
        ),
      },
      style: {
        width: NODE_WIDTH,
        minHeight: NODE_HEIGHT,
        padding: 16,
        borderRadius: 12,
        border:
          "1px solid rgba(148, 163, 184, 0.35)",
        background: "#111827",
        color: "#f8fafc",
        boxShadow:
          "0 8px 24px rgba(0, 0, 0, 0.18)",
      },
    };
  });
}

function createEdges(
  dependencies: ArchitectureDependency[]
): Edge[] {
  return dependencies.map(
    (dependency, index) => ({
      id: `architecture-edge-${index}`,
      source: dependency.source,
      target: dependency.target,
      label:
        dependency.type || undefined,
      animated: false,
      style: {
        strokeWidth: 1.5,
      },
      labelStyle: {
        fontSize: 10,
        fontWeight: 500,
        fill: "#cbd5e1",
      },
      labelBgStyle: {
        fill: "#111827",
        fillOpacity: 0.95,
      },
    })
  );
}

export default function ArchitectureGraph({
  dependencies,
  onFileSelect,
}: ArchitectureGraphProps) {
  if (!dependencies.length) {
    return (
      <div className="flex min-h-[320px] items-center justify-center rounded-xl border border-slate-700 bg-slate-950/40 p-8 text-sm text-slate-400">
        No architecture dependencies were
        detected.
      </div>
    );
  }

  const normalizedDependencies =
    normalizeDependencies(dependencies);

  const nodes = createNodes(
    normalizedDependencies
  );

  const edges = createEdges(
    normalizedDependencies
  );

  return (
    <div className="overflow-hidden rounded-xl border border-slate-700 bg-slate-950">
      <div className="border-b border-slate-800 px-4 py-3">
        <div className="text-sm font-semibold text-white">
          Dependency Graph
        </div>

        <div className="mt-1 text-xs text-slate-400">
          {nodes.length} nodes · {edges.length}{" "}
          dependencies
        </div>
      </div>

      <div className="architecture-graph h-[620px]">
        <style>
          {`
            .architecture-graph .react-flow__controls {
              background: #111827;
              border: 1px solid #334155;
              border-radius: 8px;
              overflow: hidden;
              box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
            }

            .architecture-graph .react-flow__controls-button {
              background: #111827;
              border-bottom: 1px solid #334155;
              color: #e2e8f0;
              fill: #e2e8f0;
            }

            .architecture-graph .react-flow__controls-button:hover {
              background: #1e293b;
            }

            .architecture-graph .react-flow__controls-button svg {
              fill: #e2e8f0;
              stroke: #e2e8f0;
            }

            .architecture-graph .react-flow__controls-button:last-child {
              border-bottom: none;
            }

            .architecture-graph .react-flow__attribution {
              background: rgba(15, 23, 42, 0.85);
              color: #64748b;
            }
          `}
        </style>

        <ReactFlow
          nodes={nodes}
          edges={edges}
          fitView
          minZoom={0.2}
          maxZoom={2}
          onNodeClick={(_, node) => {
            if (
              onFileSelect &&
              isLocalFile(node.id)
            ) {
              onFileSelect(node.id);
            }
          }}
        >
          <Background
            gap={24}
            size={1}
          />

          <Controls
            showZoom
            showFitView
            showInteractive
          />
        </ReactFlow>
      </div>
    </div>
  );
}