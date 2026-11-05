#!/usr/bin/env python
"""Execute course notebooks top-to-bottom (used in CI and before classes).

Usage:
    RTCOURSE_MODE=synthetic python scripts/run_notebooks.py            # all notebooks
    python scripts/run_notebooks.py notebooks/03_autosegmentacja.ipynb # selected
    python scripts/run_notebooks.py --save executed/                   # keep executed copies

Exit code 1 if any notebook fails. Default mode is the synthetic/emergency
mode, so no network or GPU is needed.
"""
import argparse
import os
import pathlib
import sys
import time

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

ROOT = pathlib.Path(__file__).resolve().parents[1]


def run(path: pathlib.Path, timeout: int, save_dir: pathlib.Path | None, verbose: bool = False) -> bool:
    nb = nbformat.read(path, as_version=4)
    client = NotebookClient(nb, timeout=timeout, kernel_name="python3",
                            resources={"metadata": {"path": str(path.parent)}})
    t = time.time()
    ok = True
    try:
        with client.setup_kernel():
            for i, cell in enumerate(nb.cells):
                if cell.cell_type != "code":
                    continue
                t0 = time.time()
                client.execute_cell(cell, i)
                dt = time.time() - t0
                if verbose:
                    print(f"     cell {i:3d}: {dt:5.1f} s", flush=True)
                if dt >= timeout - 0.5:
                    # nbclient may give up waiting for output without raising; never report that as success
                    raise TimeoutError(f"cell {i} reached the {timeout} s timeout")
    except CellExecutionError as e:
        ok = False
        print(f"FAIL {path.name}\n{str(e)[-3000:]}")
    except Exception as e:  # timeouts, dead kernel
        ok = False
        print(f"FAIL {path.name}: {type(e).__name__}: {e}")
    if ok:
        print(f"OK   {path.name}  ({time.time() - t:.0f} s)")
    if save_dir is not None:
        save_dir.mkdir(parents=True, exist_ok=True)
        nbformat.write(nb, save_dir / path.name)
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("notebooks", nargs="*")
    ap.add_argument("--timeout", type=int, default=300, help="per-cell timeout [s]")
    ap.add_argument("--save", default=None, help="folder for executed notebooks")
    ap.add_argument("-v", "--verbose", action="store_true", help="print time of every cell")
    args = ap.parse_args()
    os.environ.setdefault("RTCOURSE_MODE", "synthetic")
    # headless kernel: ipywidgets sliders can block waiting for a front end -> static images instead
    os.environ.setdefault("RTCOURSE_STATIC_PLOTS", "1")
    paths = [pathlib.Path(p) for p in args.notebooks] or sorted((ROOT / "notebooks").glob("[0-9]*.ipynb"))
    print(f"RTCOURSE_MODE={os.environ['RTCOURSE_MODE']}; {len(paths)} notebook(s)")
    results = []
    for p in paths:
        print(f"...  {p.name}", flush=True)
        results.append(run(p.resolve(), args.timeout, pathlib.Path(args.save) if args.save else None, args.verbose))
    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    main()
