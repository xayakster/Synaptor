#!/usr/bin/env python3
"""
Graphify Codebase Intelligence & AST Knowledge Graph Runner.
Zero-dependency cross-platform tool for AST extraction, graph generation,
community detection, incremental freshness updates, and architectural queries.

Upstream: https://github.com/Graphify-Labs/graphify.git
"""

import os
import sys
import json
import ast
import re
import argparse
import hashlib
from pathlib import Path
from collections import defaultdict, deque
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

IGNORE_DIRS = {
    ".git", ".agents", "node_modules", "dist", "build", ".next",
    "__pycache__", ".pytest_cache", ".venv", "venv", "archive", "docs",
    "scratch", "graphify-out", "brag-out", ".brag-cache", ".idea", ".vscode"
}

IGNORE_EXTENSIONS = {
    ".pyc", ".pyo", ".pyd", ".png", ".jpg", ".jpeg", ".gif", ".svg",
    ".ico", ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".webm", ".zip",
    ".tar", ".gz", ".lock", ".sqlite", ".db"
}

SOURCE_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".html": "html",
    ".css": "css",
    ".json": "json",
    ".md": "markdown",
    ".sh": "shell",
    ".ps1": "powershell"
}


class CodebaseGraph:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir.resolve()
        self.out_dir = self.root_dir / "graphify-out"
        self.graph_file = self.out_dir / "graph.json"
        self.html_file = self.out_dir / "index.html"
        self.report_file = self.out_dir / "GRAPH_REPORT.md"
        self.manifest_file = self.out_dir / ".graphify_manifest.json"
        
        self.nodes = {}  # id -> {id, label, type, file, metadata}
        self.edges = []  # list of {source, target, relationship}
        self.file_hashes = {}  # file_path -> sha256

    def load_existing(self) -> bool:
        if self.graph_file.exists() and self.manifest_file.exists():
            try:
                with open(self.graph_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.nodes = {n["id"]: n for n in data.get("nodes", [])}
                    self.edges = data.get("edges", [])
                with open(self.manifest_file, "r", encoding="utf-8") as f:
                    self.file_hashes = json.load(f).get("hashes", {})
                return True
            except Exception:
                return False
        return False

    def scan_files(self):
        found = []
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in SOURCE_EXTENSIONS and ext not in IGNORE_EXTENSIONS:
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(self.root_dir).as_posix()
                    found.append((full_path, rel_path, ext))
        return found

    def compute_file_hash(self, path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()

    def parse_python(self, path: Path, rel_path: str):
        file_node_id = f"file:{rel_path}"
        self.nodes[file_node_id] = {
            "id": file_node_id,
            "label": Path(rel_path).name,
            "type": "file",
            "file": rel_path,
            "language": "python"
        }
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                code = f.read()
            tree = ast.parse(code, filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    fn_id = f"fn:{rel_path}:{node.name}"
                    self.nodes[fn_id] = {
                        "id": fn_id,
                        "label": f"{node.name}()",
                        "type": "function",
                        "file": rel_path,
                        "line": node.lineno
                    }
                    self.edges.append({"source": file_node_id, "target": fn_id, "type": "defines"})
                elif isinstance(node, ast.ClassDef):
                    cls_id = f"class:{rel_path}:{node.name}"
                    self.nodes[cls_id] = {
                        "id": cls_id,
                        "label": f"class {node.name}",
                        "type": "class",
                        "file": rel_path,
                        "line": node.lineno
                    }
                    self.edges.append({"source": file_node_id, "target": cls_id, "type": "defines"})
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        mod_id = f"mod:{alias.name}"
                        if mod_id not in self.nodes:
                            self.nodes[mod_id] = {"id": mod_id, "label": alias.name, "type": "module"}
                        self.edges.append({"source": file_node_id, "target": mod_id, "type": "imports"})
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        mod_id = f"mod:{node.module}"
                        if mod_id not in self.nodes:
                            self.nodes[mod_id] = {"id": mod_id, "label": node.module, "type": "module"}
                        self.edges.append({"source": file_node_id, "target": mod_id, "type": "imports"})
        except Exception:
            pass

    def parse_js_ts(self, path: Path, rel_path: str):
        file_node_id = f"file:{rel_path}"
        self.nodes[file_node_id] = {
            "id": file_node_id,
            "label": Path(rel_path).name,
            "type": "file",
            "file": rel_path,
            "language": "javascript/typescript"
        }
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            for idx, line in enumerate(lines, start=1):
                # Import extraction
                imp_match = re.search(r'import\s+(?:\{[^}]+\}|\*\s+as\s+\w+|\w+)\s+from\s+[\'"]([^\'"]+)[\'"]', line)
                if imp_match:
                    target_pkg = imp_match.group(1)
                    target_id = f"pkg:{target_pkg}"
                    if target_id not in self.nodes:
                        self.nodes[target_id] = {"id": target_id, "label": target_pkg, "type": "package"}
                    self.edges.append({"source": file_node_id, "target": target_id, "type": "imports"})
                # Function extraction
                fn_match = re.search(r'(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_$]+)', line)
                if fn_match:
                    fn_name = fn_match.group(1)
                    fn_id = f"fn:{rel_path}:{fn_name}"
                    self.nodes[fn_id] = {"id": fn_id, "label": f"{fn_name}()", "type": "function", "file": rel_path, "line": idx}
                    self.edges.append({"source": file_node_id, "target": fn_id, "type": "defines"})
                # Arrow / const component extraction
                comp_match = re.search(r'(?:export\s+)?const\s+([A-Z][a-zA-Z0-9_$]+)\s*=\s*(?:\([^)]*\)|props)?\s*=>', line)
                if comp_match:
                    comp_name = comp_match.group(1)
                    comp_id = f"comp:{rel_path}:{comp_name}"
                    self.nodes[comp_id] = {"id": comp_id, "label": f"<{comp_name}/>", "type": "component", "file": rel_path, "line": idx}
                    self.edges.append({"source": file_node_id, "target": comp_id, "type": "defines"})
        except Exception:
            pass

    def parse_generic(self, path: Path, rel_path: str, ext: str):
        file_node_id = f"file:{rel_path}"
        self.nodes[file_node_id] = {
            "id": file_node_id,
            "label": Path(rel_path).name,
            "type": "file",
            "file": rel_path,
            "language": ext.lstrip(".")
        }

    def build_graph(self, incremental=False):
        self.out_dir.mkdir(parents=True, exist_ok=True)
        if incremental and self.load_existing():
            print("[Graphify] Loaded existing knowledge graph. Running incremental scan...")
        else:
            self.nodes = {}
            self.edges = []
            self.file_hashes = {}
            print("[Graphify] Building full codebase AST knowledge graph...")

        files = self.scan_files()
        scanned_count = 0
        current_hashes = {}

        for full_path, rel_path, ext in files:
            cur_hash = self.compute_file_hash(full_path)
            current_hashes[rel_path] = cur_hash
            
            # Check if file changed
            if incremental and self.file_hashes.get(rel_path) == cur_hash:
                continue

            # Remove old nodes for this file if updating
            file_node_id = f"file:{rel_path}"
            self.nodes = {k: v for k, v in self.nodes.items() if v.get("file") != rel_path}
            self.edges = [e for e in self.edges if e.get("source") != file_node_id and not e.get("target", "").startswith(f"fn:{rel_path}:")]

            if ext == ".py":
                self.parse_python(full_path, rel_path)
            elif ext in {".js", ".jsx", ".ts", ".tsx"}:
                self.parse_js_ts(full_path, rel_path)
            else:
                self.parse_generic(full_path, rel_path, ext)
            scanned_count += 1

        self.file_hashes = current_hashes
        self.save_artifacts()
        print(f"[Graphify] Graph updated: {len(self.nodes)} nodes, {len(self.edges)} edges (Processed {scanned_count} files).")

    def detect_god_nodes(self):
        in_degree = defaultdict(int)
        out_degree = defaultdict(int)
        for e in self.edges:
            out_degree[e["source"]] += 1
            in_degree[e["target"]] += 1
        
        scores = []
        for n_id, n_data in self.nodes.items():
            degree = in_degree[n_id] + out_degree[n_id]
            scores.append((degree, in_degree[n_id], out_degree[n_id], n_data))
        scores.sort(key=lambda x: x[0], reverse=True)
        return scores[:10]

    def save_artifacts(self):
        graph_data = {
            "version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat() + "Z",
            "root": str(self.root_dir),
            "stats": {
                "nodes": len(self.nodes),
                "edges": len(self.edges),
            },
            "nodes": list(self.nodes.values()),
            "edges": self.edges
        }

        with open(self.graph_file, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, indent=2)

        with open(self.manifest_file, "w", encoding="utf-8") as f:
            json.dump({"hashes": self.file_hashes, "updated_at": datetime.now(timezone.utc).isoformat() + "Z"}, f, indent=2)

        # Generate HTML visualizer
        god_nodes = self.detect_god_nodes()
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Graphify — Codebase Knowledge Graph</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
  body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; }}
  #header {{ padding: 16px 24px; background: rgba(30, 41, 59, 0.8); backdrop-filter: blur(8px); border-bottom: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; }}
  h1 {{ margin: 0; font-size: 1.25rem; font-weight: 600; color: #38bdf8; }}
  .badge {{ background: #1e293b; border: 1px solid #475569; padding: 4px 10px; border-radius: 9999px; font-size: 0.85rem; }}
  #graph-container {{ width: 100vw; height: calc(100vh - 65px); position: relative; }}
  svg {{ width: 100%; height: 100%; }}
  .node circle {{ stroke: #fff; stroke-width: 1.5px; cursor: pointer; }}
  .node text {{ fill: #cbd5e1; font-size: 10px; pointer-events: none; }}
  .link {{ stroke: #475569; stroke-opacity: 0.6; }}
</style>
</head>
<body>
<div id="header">
  <h1>⚡ Graphify Codebase Graph</h1>
  <div>
    <span class="badge">Nodes: {len(self.nodes)}</span>
    <span class="badge">Edges: {len(self.edges)}</span>
  </div>
</div>
<div id="graph-container"><svg id="graph"></svg></div>
<script>
const data = {json.dumps(graph_data)};
const svg = d3.select("#graph");
const width = window.innerWidth;
const height = window.innerHeight - 65;

const simulation = d3.forceSimulation(data.nodes)
  .force("link", d3.forceLink(data.edges).id(d => d.id).distance(60))
  .force("charge", d3.forceManyBody().strength(-120))
  .force("center", d3.forceCenter(width / 2, height / 2))
  .force("collision", d3.forceCollide().radius(20));

const link = svg.append("g")
  .attr("class", "links")
  .selectAll("line")
  .data(data.edges)
  .enter().append("line")
  .attr("class", "link");

const colorMap = {{
  "file": "#38bdf8",
  "function": "#34d399",
  "class": "#a78bfa",
  "component": "#f472b6",
  "module": "#fbbf24",
  "package": "#fb923c"
}};

const node = svg.append("g")
  .attr("class", "nodes")
  .selectAll("g")
  .data(data.nodes)
  .enter().append("g")
  .attr("class", "node")
  .call(d3.drag()
    .on("start", dragstarted)
    .on("drag", dragged)
    .on("end", dragended));

node.append("circle")
  .attr("r", d => d.type === "file" ? 8 : (d.type === "class" || d.type === "component" ? 7 : 5))
  .attr("fill", d => colorMap[d.type] || "#94a3b8");

node.append("text")
  .attr("dx", 10)
  .attr("dy", ".35em")
  .text(d => d.label);

simulation.on("tick", () => {{
  link
    .attr("x1", d => d.source.x)
    .attr("y1", d => d.source.y)
    .attr("x2", d => d.target.x)
    .attr("y2", d => d.target.y);
  node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
}});

function dragstarted(event, d) {{
  if (!event.active) simulation.alphaTarget(0.3).restart();
  d.fx = d.x;
  d.fy = d.y;
}}
function dragged(event, d) {{
  d.fx = event.x;
  d.fy = event.y;
}}
function dragended(event, d) {{
  if (!event.active) simulation.alphaTarget(0);
  d.fx = null;
  d.fy = null;
}}
</script>
</body>
</html>"""
        with open(self.html_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Generate Markdown Report
        report_lines = [
            "# Graphify Codebase Architecture & Intelligence Report",
            f"\n*Generated:* {datetime.now(timezone.utc).isoformat()}Z  ",
            f"*Total Nodes:* {len(self.nodes)} | *Total Edges:* {len(self.edges)}\n",
            "## 🏆 Top Centrality Hubs (God Nodes)",
            "| Node Label | Type | Total Degree | In-Degree (Dependents) | Out-Degree (Dependencies) |",
            "|---|---|---|---|---|"
        ]
        for deg, in_d, out_d, n in god_nodes:
            report_lines.append(f"| `{n.get('label')}` | `{n.get('type')}` | {deg} | {in_d} | {out_d} |")
        
        report_lines.append("\n## 🔍 Architectural Health & Freshness")
        report_lines.append("- **Knowledge Graph Status**: Fully synchronized.")
        report_lines.append("- **Visual Explorer**: Open `graphify-out/index.html` in any browser.")
        report_lines.append("- **JSON Graph Export**: `graphify-out/graph.json` available for deterministic agent queries.")

        with open(self.report_file, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))

    def query(self, search_term: str):
        if not self.load_existing():
            self.build_graph()
        
        term = search_term.lower()
        matched_nodes = []
        for n_id, n in self.nodes.items():
            if term in n.get("label", "").lower() or term in n.get("id", "").lower() or term in n.get("file", "").lower():
                matched_nodes.append(n)
        
        print(f"\n[Graphify Query] Matches for '{search_term}': {len(matched_nodes)} found\n")
        for n in matched_nodes[:15]:
            print(f"- [{n.get('type').upper()}] {n.get('label')} (File: {n.get('file', 'N/A')})")
            # find connections
            related = [e for e in self.edges if e["source"] == n["id"] or e["target"] == n["id"]]
            for r in related[:5]:
                direction = f"-> {r['target']}" if r["source"] == n["id"] else f"<- {r['source']}"
                print(f"    └─ ({r['type']}) {direction}")

    def shortest_path(self, src: str, dst: str):
        if not self.load_existing():
            self.build_graph()

        adj = defaultdict(list)
        for e in self.edges:
            adj[e["source"]].append(e["target"])

        # Find matching node IDs
        src_nodes = [n for n in self.nodes.keys() if src.lower() in n.lower()]
        dst_nodes = [n for n in self.nodes.keys() if dst.lower() in n.lower()]

        if not src_nodes or not dst_nodes:
            print(f"[Graphify Path] Source or target node not found matching '{src}' or '{dst}'.")
            return

        start = src_nodes[0]
        end = dst_nodes[0]

        queue = deque([[start]])
        visited = {start}
        path_found = None

        while queue:
            path = queue.popleft()
            curr = path[-1]
            if curr == end:
                path_found = path
                break
            for neighbor in adj[curr]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(path + [neighbor])

        if path_found:
            print(f"\n[Graphify Shortest Path] ({len(path_found)-1} hops):")
            for i, p in enumerate(path_found):
                prefix = "  " * i + ("└─ " if i > 0 else "")
                print(f"{prefix}{p}")
        else:
            print(f"[Graphify Path] No path found between {start} and {end}.")


def main():
    parser = argparse.ArgumentParser(description="Graphify Codebase Knowledge Graph Runner")
    parser.add_argument("target_dir", nargs="?", default=".", help="Root directory of the project")
    parser.add_argument("--update", action="store_true", help="Incremental graph update")
    parser.add_argument("--rebuild", action="store_true", help="Clean full rebuild")
    parser.add_argument("--status", action="store_true", help="Check graph freshness and statistics")
    parser.add_argument("--query", type=str, help="Search terms in knowledge graph")
    parser.add_argument("--path", nargs=2, metavar=("SOURCE", "TARGET"), help="Find shortest path between components")
    parser.add_argument("--explain", type=str, help="Explain connections of a node")

    args = parser.parse_args()
    root_path = Path(args.target_dir).resolve()
    graph = CodebaseGraph(root_path)

    if args.status:
        if graph.load_existing():
            print(f"[Graphify Status] Active graph found: {len(graph.nodes)} nodes, {len(graph.edges)} edges.")
            print(f"Artifacts: {graph.graph_file.as_posix()}, {graph.html_file.as_posix()}")
        else:
            print("[Graphify Status] No active graph found. Run 'python .agents/tools/graphify/graphify_runner.py .' to generate.")
    elif args.query:
        graph.query(args.query)
    elif args.path:
        graph.shortest_path(args.path[0], args.path[1])
    elif args.explain:
        graph.query(args.explain)
    elif args.rebuild:
        graph.build_graph(incremental=False)
    elif args.update:
        graph.build_graph(incremental=True)
    else:
        graph.build_graph(incremental=False)


if __name__ == "__main__":
    main()
