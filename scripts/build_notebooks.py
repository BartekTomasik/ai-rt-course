#!/usr/bin/env python
"""Build .ipynb notebooks from jupytext "percent" sources in notebooks/src/.

Usage:  python scripts/build_notebooks.py          # (re)build all notebooks
        python scripts/build_notebooks.py --check  # fail if a notebook is out of date

Why: .py sources are easy to edit and review; .ipynb files are what Colab opens.
A line "# INCLUDE: _setup.py" is replaced by the shared setup cell, and a
"Open in Colab" badge is added at the top of every notebook.
"""
import argparse
import pathlib
import sys

import jupytext
import nbformat

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "notebooks" / "src"
OUT = ROOT / "notebooks"
REPO = "bartektomasik/ai-rt-course"
BRANCH = "main"


def build_one(src: pathlib.Path) -> str:
    text = src.read_text(encoding="utf-8")
    lines = []
    for line in text.splitlines():
        if line.startswith("# INCLUDE:"):
            inc = SRC / line.split(":", 1)[1].strip()
            lines.append(inc.read_text(encoding="utf-8"))
        else:
            lines.append(line)
    nb = jupytext.reads("\n".join(lines), fmt="py:percent")
    name = src.stem + ".ipynb"
    badge = (
        f"[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]"
        f"(https://colab.research.google.com/github/{REPO}/blob/{BRANCH}/notebooks/{name})"
    )
    nb.cells.insert(0, nbformat.v4.new_markdown_cell(badge))
    for i, c in enumerate(nb.cells):
        c.id = f"cell-{i:03d}"
        tags = c.metadata.get("tags")
        c.metadata = {"tags": tags} if tags else {}
        if c.cell_type == "code":
            c.outputs = []
            c.execution_count = None
    nb.metadata = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
        "colab": {"provenance": [], "toc_visible": True},
    }
    return nbformat.writes(nb) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    stale = []
    for src in sorted(SRC.glob("[0-9]*.py")):
        out = OUT / (src.stem + ".ipynb")
        new = build_one(src)
        if args.check:
            if not out.exists() or out.read_text(encoding="utf-8") != new:
                stale.append(out.name)
        else:
            out.write_text(new, encoding="utf-8")
            print("built", out.relative_to(ROOT))
    if stale:
        print("Notebooks out of date (run scripts/build_notebooks.py):", ", ".join(stale))
        sys.exit(1)


if __name__ == "__main__":
    main()
