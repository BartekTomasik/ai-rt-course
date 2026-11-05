#!/usr/bin/env python
"""Baseline submission for the challenge.

If the course pack contains TotalSegmentator masks for challenge cases
(challenge/totalseg/), the baseline is TotalSegmentator "out of the box".
Otherwise a classical HU-threshold baseline is used (lungs only, others empty).

Usage:
    python projects/challenge/baseline.py --pack course_pack --out submissions/baseline
"""
import argparse
import glob
import os
import pathlib
import sys

import numpy as np
from scipy import ndimage

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from rtcourse import autoseg  # noqa: E402
from rtcourse.case import Case  # noqa: E402


def threshold_lungs(case: Case) -> dict:
    """Very simple classical segmentation: air inside the body, split at the midline."""
    body = case.structures.get("BODY")
    if body is None:
        body = np.stack([ndimage.binary_fill_holes(s) for s in case.ct > -400])
    air = (case.ct < -400) & body
    air = ndimage.binary_opening(air, iterations=1)
    lab, n = ndimage.label(air)
    if n == 0:
        return {}
    sizes = ndimage.sum(air, lab, range(1, n + 1))
    keep = 1 + np.argsort(sizes)[::-1][:2]
    lungs = np.isin(lab, keep)
    xs = (case.origin[0] + np.arange(case.shape[2]) * case.spacing[2])[None, None, :]
    return {"Lung_R": lungs & (xs < 0), "Lung_L": lungs & (xs >= 0)}  # LPS: +x = patient left


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", default="course_pack")
    ap.add_argument("--out", default="submissions/baseline")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    for p in sorted(glob.glob(os.path.join(args.pack, "challenge", "images", "*.npz"))):
        case = Case.load_npz(p)
        ts = os.path.join(args.pack, "challenge", "totalseg", f"{case.case_id}.npz")
        masks = autoseg.load_masks(ts) if os.path.exists(ts) else threshold_lungs(case)
        autoseg.save_masks(masks, os.path.join(args.out, f"{case.case_id}.npz"))
        print(case.case_id, "->", "TotalSegmentator" if os.path.exists(ts) else "progowanie HU", sorted(masks))


if __name__ == "__main__":
    main()
