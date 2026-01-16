#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate a Mermaid flowchart from a fixed-format xray report.

Layout rule you requested
- Leaf nodes are defined purely by max_depth
  depth == max_depth is leaf
  depth < max_depth is non leaf
- Non leaf siblings stay horizontal
- Leaf siblings under the same parent are stacked vertically

Defaults
- --max-depth 3

Assumptions about report format
- There is a section starting with: === named_modules
- After that, each non-empty line follows:
    <module_path><spaces><class_name>
  Example:
    visual.blocks.0.attn.qkv    Linear
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from collections import defaultdict
from typing import Dict, List, Optional, Tuple


NAMED_MODULES_HEADER_RE = re.compile(r"^===\s+named_modules\b", re.IGNORECASE)
SECTION_HEADER_RE = re.compile(r"^===\s+\S+")
LINE_RE = re.compile(r"^(?P<path>\S+)\s+(?P<cls>.+?)\s*$")


@dataclass(frozen=True)
class Node:
    path: str
    cls: Optional[str]  # None for implicit parents


def path_depth(path: str) -> int:
    return len(path.split("."))


def sanitize_label(s: str) -> str:
    # User requirement: do not include parentheses in text
    s = s.replace("(", "").replace(")", "")
    s = s.replace("[", "").replace("]", "")
    s = s.replace("{", "").replace("}", "")
    return s


def mermaid_id_for_path(path: str) -> str:
    # Mermaid node ids: keep alnum and underscore only
    out = []
    for ch in path:
        if ch.isalnum() or ch == "_":
            out.append(ch)
        else:
            out.append("_")
    if out and out[0].isdigit():
        out.insert(0, "n_")
    return "".join(out)


def parse_named_modules(report_text: str) -> Dict[str, Node]:
    lines = report_text.splitlines()
    in_named = False
    nodes: Dict[str, Node] = {}

    for raw in lines:
        line = raw.rstrip("\n")

        if not in_named:
            if NAMED_MODULES_HEADER_RE.match(line.strip()):
                in_named = True
            continue

        # stop at next === section
        if SECTION_HEADER_RE.match(line.strip()) and not NAMED_MODULES_HEADER_RE.match(line.strip()):
            break

        if not line.strip():
            continue

        m = LINE_RE.match(line)
        if not m:
            continue

        path = m.group("path").strip()
        cls = m.group("cls").strip()
        nodes[path] = Node(path=path, cls=cls)

    return nodes


def ensure_parents(nodes: Dict[str, Node]) -> Dict[str, Node]:
    out = dict(nodes)
    for p in list(nodes.keys()):
        parts = p.split(".")
        for i in range(1, len(parts)):
            parent = ".".join(parts[:i])
            if parent not in out:
                out[parent] = Node(path=parent, cls=None)
    return out


def filter_by_max_depth(nodes: Dict[str, Node], max_depth: int) -> Dict[str, Node]:
    # Keep all nodes with depth <= max_depth
    kept = {p: n for p, n in nodes.items() if path_depth(p) <= max_depth}
    # Ensure connectivity for kept nodes
    kept = ensure_parents(kept)
    kept = {p: n for p, n in kept.items() if path_depth(p) <= max_depth}
    return kept


def build_tree(nodes: Dict[str, Node]) -> Dict[str, List[str]]:
    tree: Dict[str, List[str]] = defaultdict(list)
    for path in nodes.keys():
        if "." not in path:
            continue
        parent = path.rsplit(".", 1)[0]
        if parent in nodes:
            tree[parent].append(path)
    # sort children for stable output
    for parent in list(tree.keys()):
        tree[parent] = sorted(set(tree[parent]))
    return tree


def node_label(node: Node) -> str:
    if node.cls:
        s = f"{node.path} {node.cls}"
    else:
        s = node.path
    return sanitize_label(s)


def emit_leaf_stack(
    lines: List[str],
    parent: str,
    leaf_children: List[str],
    stack_id: str,
) -> None:
    if not leaf_children:
        return

    leaf_children = sorted(leaf_children)

    lines.append(f"  subgraph {stack_id}")
    lines.append("    direction TB")

    # Make a vertical chain
    for a, b in zip(leaf_children, leaf_children[1:]):
        lines.append(f"    {mermaid_id_for_path(a)} --> {mermaid_id_for_path(b)}")

    lines.append("  end")

    # Connect parent to the first leaf in the stack
    lines.append(f"  {mermaid_id_for_path(parent)} --> {mermaid_id_for_path(leaf_children[0])}")


def generate_mermaid(
    nodes: Dict[str, Node],
    max_depth: int,
    root_label: str,
) -> str:
    # Global direction LR so non leaf sibling fanout stays horizontal
    lines: List[str] = []
    lines.append("flowchart LR")

    root_id = "Model"
    lines.append(f"  {root_id}[{sanitize_label(root_label)}]")

    # Declare nodes
    for path, node in sorted(nodes.items(), key=lambda x: (path_depth(x[0]), x[0])):
        nid = mermaid_id_for_path(path)
        lbl = node_label(node)
        lines.append(f"  {nid}[{lbl}]")

    # Root connects to top-level nodes
    top_level = sorted([p for p in nodes.keys() if "." not in p])
    for t in top_level:
        lines.append(f"  {root_id} --> {mermaid_id_for_path(t)}")

    # Build parent children
    tree = build_tree(nodes)

    # Emit edges with your layout rule
    stack_counter = 0
    for parent in sorted(tree.keys()):
        children = tree[parent]

        leaf_children = [c for c in children if path_depth(c) == max_depth]
        nonleaf_children = [c for c in children if path_depth(c) < max_depth]

        # Non leaf fanout stays horizontal
        for c in nonleaf_children:
            lines.append(f"  {mermaid_id_for_path(parent)} --> {mermaid_id_for_path(c)}")

        # Leaf siblings vertical stack
        if leaf_children:
            stack_counter += 1
            stack_id = f"leafstack_{mermaid_id_for_path(parent)}_{stack_counter}"
            emit_leaf_stack(lines, parent, leaf_children, stack_id)

    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate Mermaid graph from xray report")
    ap.add_argument("--report", required=True, help="Path to QWen3_xray.report")
    ap.add_argument("--out", required=True, help="Output markdown file path")
    ap.add_argument("--max-depth", type=int, default=3, help="Leaf depth, default 3")
    ap.add_argument("--root-label", default="Qwen3VLModel", help="Root node label")

    args = ap.parse_args()

    with open(args.report, "r", encoding="utf-8") as f:
        report_text = f.read()

    explicit = parse_named_modules(report_text)
    if not explicit:
        raise SystemExit("Could not find named_modules section or it was empty")

    # Build full node set and filter by depth
    all_nodes = ensure_parents(explicit)
    nodes = filter_by_max_depth(all_nodes, args.max_depth)

    mermaid = generate_mermaid(nodes, max_depth=args.max_depth, root_label=args.root_label)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("```mermaid\n")
        f.write(mermaid)
        f.write("```\n")

    print(f"Wrote: {args.out}")


if __name__ == "__main__":
    main()
