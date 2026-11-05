"""Autosegmentation: TotalSegmentator wrapper + simulated "AI" errors.

Fallback strategy used in the notebooks:
1. real data + GPU (or patience on CPU) -> run TotalSegmentator live,
2. otherwise -> load masks precomputed by the instructor (course pack),
3. otherwise (synthetic phantom) -> `simulate_autoseg()`, which applies
   typical, clinically observed error patterns to the reference contours.
"""
from __future__ import annotations

import os

import numpy as np
from scipy import ndimage

from .case import Case

# TotalSegmentator (v2) class names -> course structure names
TOTALSEG_MAP = {
    "Lung_L": ["lung_upper_lobe_left", "lung_lower_lobe_left"],
    "Lung_R": ["lung_upper_lobe_right", "lung_middle_lobe_right", "lung_lower_lobe_right"],
    "Heart": ["heart"],
    "Esophagus": ["esophagus"],
    "SpinalCord": ["spinal_cord"],
}

# Default "simulated model" error profile. Every entry is something seen in
# real autosegmentation validation studies (see instructor guide, block 3).
DEFAULT_ERRORS = {
    "Lung_L": {"boundary_noise_mm": 3.0},
    "Lung_R": {"boundary_noise_mm": 3.0},
    "Heart": {"dilate_mm": 4.0, "drop_cranial_frac": 0.1},  # pericardial fat + great vessels convention
    "Esophagus": {"shift_mm": (0.0, 3.0, 2.0), "drop_caudal_frac": 0.25},  # GE junction missed
    "SpinalCord": {"dilate_mm": 3.0},  # cord vs canal convention
}


def _grow(mask, spacing, mm):
    """Dilate (mm>0) or erode (mm<0) by a physical distance."""
    if mm == 0:
        return mask.copy()
    if mm > 0:
        return ndimage.distance_transform_edt(~mask, sampling=spacing) <= mm
    return ndimage.distance_transform_edt(mask, sampling=spacing) > -mm


def perturb_mask(mask, spacing, seed=0, dilate_mm=0.0, shift_mm=(0.0, 0.0, 0.0),
                 drop_cranial_frac=0.0, drop_caudal_frac=0.0, boundary_noise_mm=0.0,
                 miss_slices=0):
    """Apply controlled errors to a binary mask.

    shift_mm is (dz, dy, dx). drop_*_frac removes that fraction of the
    structure's slices at the cranial (high z index) / caudal end.
    miss_slices removes N random slices in the middle (the "skipped slice" error).
    """
    rng = np.random.default_rng(seed)
    m = np.asarray(mask, bool).copy()
    if not m.any():
        return m
    if boundary_noise_mm > 0:
        sd = ndimage.distance_transform_edt(~m, sampling=spacing) - ndimage.distance_transform_edt(m, sampling=spacing)
        noise = ndimage.gaussian_filter(rng.normal(0, 1, m.shape), sigma=[6 / s for s in spacing])
        noise *= boundary_noise_mm / (noise.std() + 1e-9)
        m = (sd + noise) <= 0
    m = _grow(m, spacing, dilate_mm)
    if any(shift_mm):
        m = ndimage.shift(m.astype(np.uint8), [s / sp for s, sp in zip(shift_mm, spacing)], order=0) > 0
    zs = np.nonzero(m.any(axis=(1, 2)))[0]
    if len(zs):
        n = len(zs)
        if drop_cranial_frac > 0:
            k = int(round(n * drop_cranial_frac))
            if k:
                m[zs[-k:]] = False
        if drop_caudal_frac > 0:
            k = int(round(n * drop_caudal_frac))
            if k:
                m[zs[:k]] = False
        if miss_slices > 0 and n > 4:
            for k in rng.choice(zs[2:-2], size=min(miss_slices, n - 4), replace=False):
                m[k] = False
    return m


def simulate_autoseg(case: Case, errors=None, seed: int = 0) -> dict:
    """Return {name: mask} imitating an AI model with typical errors."""
    errors = DEFAULT_ERRORS if errors is None else errors
    out = {}
    for i, (name, params) in enumerate(errors.items()):
        if name in case.structures:
            out[name] = perturb_mask(case.structures[name], case.spacing, seed=seed + i, **params)
    body = case.structures.get("BODY")
    if body is not None:
        out = {k: v & body for k, v in out.items()}
    return out


# ------------------------------------------------------------------ TotalSegmentator
def has_gpu() -> bool:
    try:
        import torch

        return bool(torch.cuda.is_available())
    except Exception:
        return False


def case_to_nifti(case: Case):
    """Convert (z,y,x) LPS array to a nibabel image in RAS (x,y,z)."""
    import nibabel as nib

    sz, sy, sx = case.spacing
    x0, y0, z0 = case.origin
    affine = np.array([[-sx, 0, 0, -x0], [0, -sy, 0, -y0], [0, 0, sz, z0], [0, 0, 0, 1]], float)
    data = np.transpose(case.ct, (2, 1, 0)).astype(np.int16)
    return nib.Nifti1Image(data, affine)


def run_totalsegmentator(case: Case, fast: bool | None = None, device: str | None = None) -> dict:
    """Run TotalSegmentator on `case.ct`; returns course-named masks.

    Requires `pip install TotalSegmentator`. With fast=True the 3 mm model
    is used (runs on CPU in a few minutes, lower accuracy).
    """
    from totalsegmentator.python_api import totalsegmentator

    gpu = has_gpu()
    if fast is None:
        fast = not gpu
    if device is None:
        device = "gpu" if gpu else "cpu"
    rois = sorted({c for v in TOTALSEG_MAP.values() for c in v})
    img = case_to_nifti(case)
    seg = totalsegmentator(img, None, ml=True, fast=fast, roi_subset=rois, device=device, quiet=True)
    from totalsegmentator.map_to_binary import class_map

    labels = np.transpose(np.asanyarray(seg.dataobj), (2, 1, 0))
    name_to_id = {v: k for k, v in class_map["total"].items()}
    out = {}
    for course_name, ts_names in TOTALSEG_MAP.items():
        ids = [name_to_id[n] for n in ts_names if n in name_to_id]
        out[course_name] = np.isin(labels, ids)
    return out


def save_masks(masks: dict, path, spacing=None):
    """Packed boolean masks (+ optional voxel spacing) in one .npz file."""
    shape = next(iter(masks.values())).shape
    extra = {} if spacing is None else {"spacing": np.asarray(spacing, float)}
    np.savez_compressed(path, shape=np.array(shape), **extra, **{k: np.packbits(v.ravel()) for k, v in masks.items()})


def load_masks(path) -> dict:
    f = np.load(path)
    shape = tuple(f["shape"].tolist())
    n = int(np.prod(shape))
    return {k: np.unpackbits(f[k])[:n].reshape(shape).astype(bool) for k in f.files if k not in ("shape", "spacing")}


def get_autoseg(case: Case, pack_dir=None, allow_live=True, verbose=True) -> tuple:
    """Return (masks, how) where how in {'totalsegmentator', 'precomputed', 'simulated'}.

    allow_live=True tries to run TotalSegmentator (caller decides, e.g. only with GPU).
    """
    if case.source != "synthetic":
        if allow_live and os.environ.get("RTCOURSE_MODE", "auto") != "synthetic":
            try:
                masks = run_totalsegmentator(case)
                return masks, "totalsegmentator"
            except Exception as e:  # pragma: no cover - needs GPU
                if verbose:
                    print(f"[TRYB AWARYJNY] TotalSegmentator nie zadziałał ({e}); używam wyników przygotowanych wcześniej.")
        if pack_dir is not None:
            p = os.path.join(pack_dir, "totalseg", f"{case.case_id}.npz")
            if os.path.exists(p):
                return load_masks(p), "precomputed"
    if verbose and case.source != "synthetic":
        print("[TRYB AWARYJNY] Brak GPU i brak gotowych wyników — używam symulowanego modelu.")
    return simulate_autoseg(case), "simulated"
