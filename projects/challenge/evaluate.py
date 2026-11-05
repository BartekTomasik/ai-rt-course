#!/usr/bin/env python
"""Automatic scoring for the challenge "Pobij bazowy Dice".

Checks the submission format and computes Dice / HD95 per structure against
the hidden ground truth (kept by the instructor, never shared).

Usage:
    python projects/challenge/evaluate.py --submission moj_zespol/ --ground-truth instructor_private/challenge_gt \
        --team "Zespół A" [--leaderboard leaderboard.csv]
    python projects/challenge/evaluate.py --submission moj_zespol/ --images course_pack/challenge/images --check-only

Submission format: one file <case_id>.npz per held-out case, containing either
  * boolean arrays named Lung_L, Lung_R, Heart, Esophagus, SpinalCord with the CT shape (z, y, x), or
  * the packed format written by rtcourse.autoseg.save_masks (key 'shape' + packed bits).
A missing structure or case scores Dice = 0 (HD95 = 100 mm penalty).
"""
import argparse
import glob
import os
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from rtcourse import metrics  # noqa: E402

STRUCTURES = ["Lung_L", "Lung_R", "Heart", "Esophagus", "SpinalCord"]
HD_PENALTY = 100.0


def load_submission_file(path, shape=None):
    f = np.load(path, allow_pickle=False)
    if "shape" in f.files:
        shp = tuple(int(x) for x in f["shape"])
        n = int(np.prod(shp))
        masks = {k: np.unpackbits(f[k])[:n].reshape(shp).astype(bool) for k in f.files if k not in ("shape", "spacing")}
    else:
        masks = {k: np.asarray(f[k]).astype(bool) for k in f.files if k != "spacing"}
    problems = []
    for k, v in masks.items():
        if shape is not None and tuple(v.shape) != tuple(shape):
            problems.append(f"{os.path.basename(path)}: '{k}' ma kształt {v.shape}, oczekiwano {tuple(shape)}")
    unknown = sorted(set(masks) - set(STRUCTURES))
    if unknown:
        problems.append(f"{os.path.basename(path)}: nieznane struktury {unknown} (zostaną pominięte)")
    return masks, problems


def reference_shapes(folder):
    """{case_id: (shape, spacing)} from ground-truth or image folder."""
    out = {}
    for p in sorted(glob.glob(os.path.join(folder, "*.npz"))):
        f = np.load(p, allow_pickle=False)
        cid = pathlib.Path(p).stem
        if "ct" in f.files:
            out[cid] = (f["ct"].shape, tuple(f["spacing"].tolist()))
        else:
            out[cid] = (tuple(int(x) for x in f["shape"]), tuple(f["spacing"].tolist()) if "spacing" in f.files else None)
    return out


def check(submission, refs):
    problems = []
    for cid, (shape, _) in refs.items():
        p = os.path.join(submission, f"{cid}.npz")
        if not os.path.exists(p):
            problems.append(f"brak pliku {cid}.npz")
            continue
        masks, pr = load_submission_file(p, shape)
        problems += pr
        miss = [s for s in STRUCTURES if s not in masks]
        if miss:
            problems.append(f"{cid}.npz: brak struktur {miss} (Dice = 0)")
    return problems


def score(submission, gt_dir, spacing_dir=None):
    rows = []
    spacings = reference_shapes(spacing_dir) if spacing_dir else {}
    for p in sorted(glob.glob(os.path.join(gt_dir, "*.npz"))):
        cid = pathlib.Path(p).stem
        f = np.load(p)
        shape = tuple(int(x) for x in f["shape"])
        n = int(np.prod(shape))
        spacing = tuple(f["spacing"].tolist()) if "spacing" in f.files else (spacings.get(cid, (None, (1, 1, 1)))[1] or (1, 1, 1))
        gt = {k: np.unpackbits(f[k])[:n].reshape(shape).astype(bool) for k in f.files if k in STRUCTURES}
        sp = os.path.join(submission, f"{cid}.npz")
        sub = load_submission_file(sp, shape)[0] if os.path.exists(sp) else {}
        for s in STRUCTURES:
            if s not in gt:
                continue
            m = sub.get(s)
            if m is None or m.shape != gt[s].shape:
                rows.append({"case": cid, "structure": s, "Dice": 0.0, "HD95_mm": HD_PENALTY})
                continue
            hd = metrics.hd95(gt[s], m, spacing)
            rows.append({"case": cid, "structure": s, "Dice": metrics.dice(gt[s], m), "HD95_mm": min(hd, HD_PENALTY)})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--submission", required=True)
    ap.add_argument("--ground-truth", help="folder z etykietami (tylko prowadzący)")
    ap.add_argument("--images", help="folder challenge/images (do sprawdzenia formatu bez etykiet)")
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--team", default=None)
    ap.add_argument("--leaderboard", default=None, help="plik CSV z rankingiem (dopisuje wynik)")
    args = ap.parse_args()

    ref_dir = args.ground_truth or args.images
    if not ref_dir:
        sys.exit("Podaj --ground-truth albo --images")
    refs = reference_shapes(ref_dir)
    problems = check(args.submission, refs)
    print("Sprawdzenie formatu:", "OK" if not problems else f"{len(problems)} uwag")
    for p in problems:
        print("  -", p)
    if args.check_only or not args.ground_truth:
        sys.exit(1 if any("kształt" in p or "brak pliku" in p for p in problems) else 0)

    df = score(args.submission, args.ground_truth, args.images)
    per_structure = df.groupby("structure")[["Dice", "HD95_mm"]].mean().round(3)
    print(per_structure)
    mean_dice = float(df["Dice"].mean())
    mean_hd = float(df["HD95_mm"].mean())
    print(f"\nWYNIK: średni Dice = {mean_dice:.4f} | średni HD95 = {mean_hd:.2f} mm")
    if args.leaderboard:
        team = args.team or pathlib.Path(args.submission).name
        row = pd.DataFrame([{"team": team, "mean_Dice": round(mean_dice, 4), "mean_HD95_mm": round(mean_hd, 2),
                             **{f"Dice_{k}": v for k, v in per_structure["Dice"].items()}}])
        if os.path.exists(args.leaderboard):
            row = pd.concat([pd.read_csv(args.leaderboard), row], ignore_index=True)
            row = row.sort_values("mean_Dice", ascending=False).drop_duplicates("team", keep="first")
        row.sort_values("mean_Dice", ascending=False).to_csv(args.leaderboard, index=False)
        print(f"Ranking zapisany: {args.leaderboard}")


if __name__ == "__main__":
    main()
