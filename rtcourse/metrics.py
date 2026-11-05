"""Segmentation and dose metrics (educational, voxel-based implementations)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import ndimage


# ---------------------------------------------------------------- geometry
def volume_cc(mask, spacing) -> float:
    """Volume of a mask in cm^3 (spacing in mm)."""
    return float(np.count_nonzero(mask) * np.prod(spacing) / 1000.0)


def dice(a, b) -> float:
    """Dice similarity coefficient: 2|A∩B| / (|A|+|B|). Both empty -> 1.0."""
    a = np.asarray(a, bool)
    b = np.asarray(b, bool)
    s = a.sum() + b.sum()
    if s == 0:
        return 1.0
    return float(2.0 * np.logical_and(a, b).sum() / s)


def _surface(mask):
    mask = np.asarray(mask, bool)
    if not mask.any():
        return mask
    eroded = ndimage.binary_erosion(mask, structure=ndimage.generate_binary_structure(3, 1), border_value=0)
    return mask & ~eroded


def surface_distances(a, b, spacing):
    """Distances (mm) from surface voxels of A to surface of B and vice versa."""
    sa, sb = _surface(a), _surface(b)
    if not sa.any() or not sb.any():
        return None, None
    dt_b = ndimage.distance_transform_edt(~sb, sampling=spacing)
    dt_a = ndimage.distance_transform_edt(~sa, sampling=spacing)
    return dt_b[sa], dt_a[sb]


def hd95(a, b, spacing) -> float:
    """95th percentile Hausdorff distance (mm). Returns inf if a mask is empty."""
    d_ab, d_ba = surface_distances(a, b, spacing)
    if d_ab is None:
        return float("inf")
    return float(max(np.percentile(d_ab, 95), np.percentile(d_ba, 95)))


def mean_surface_distance(a, b, spacing) -> float:
    d_ab, d_ba = surface_distances(a, b, spacing)
    if d_ab is None:
        return float("inf")
    return float((d_ab.sum() + d_ba.sum()) / (len(d_ab) + len(d_ba)))


def surface_dice(a, b, spacing, tolerance_mm: float = 2.0) -> float:
    """Surface Dice at a given tolerance (voxel approximation of Nikolov et al. 2021)."""
    d_ab, d_ba = surface_distances(a, b, spacing)
    if d_ab is None:
        return 0.0
    ok = (d_ab <= tolerance_mm).sum() + (d_ba <= tolerance_mm).sum()
    return float(ok / (len(d_ab) + len(d_ba)))


def compare_masks(reference: dict, test: dict, spacing, tolerance_mm: float = 2.0) -> pd.DataFrame:
    """Table of metrics for every structure present in both dicts."""
    rows = []
    for name in reference:
        if name not in test:
            continue
        r, t = reference[name], test[name]
        rows.append(
            {
                "structure": name,
                "V_ref_cc": round(volume_cc(r, spacing), 1),
                "V_test_cc": round(volume_cc(t, spacing), 1),
                "dV_%": round(100 * (volume_cc(t, spacing) - volume_cc(r, spacing)) / max(volume_cc(r, spacing), 1e-6), 1),
                "Dice": round(dice(r, t), 3),
                "HD95_mm": round(hd95(r, t, spacing), 1),
                "MSD_mm": round(mean_surface_distance(r, t, spacing), 2),
                f"sDice_{tolerance_mm:g}mm": round(surface_dice(r, t, spacing, tolerance_mm), 3),
            }
        )
    return pd.DataFrame(rows).set_index("structure")


# ---------------------------------------------------------------- dose
def dvh(dose, mask, bin_width: float = 0.1, max_dose: float | None = None):
    """Cumulative DVH. Returns (dose_bins_Gy, volume_percent)."""
    d = np.asarray(dose)[np.asarray(mask, bool)]
    if max_dose is None:
        max_dose = float(np.max(dose)) * 1.05 + bin_width
    bins = np.arange(0, max_dose + bin_width, bin_width)
    if d.size == 0:
        return bins, np.zeros_like(bins)
    hist, _ = np.histogram(d, bins=np.append(bins, np.inf))
    cum = hist[::-1].cumsum()[::-1]
    return bins, 100.0 * cum / d.size


def dose_at_volume(dose, mask, volume_percent: float) -> float:
    """D_x%: minimum dose received by the hottest x% of the volume."""
    d = np.asarray(dose)[np.asarray(mask, bool)]
    if d.size == 0:
        return float("nan")
    return float(np.percentile(d, 100 - volume_percent))


def dose_at_abs_volume(dose, mask, spacing, volume_cc_: float = 0.03) -> float:
    """D_{x cc}: e.g. D0.03cc ("near-max dose")."""
    d = np.sort(np.asarray(dose)[np.asarray(mask, bool)])[::-1]
    if d.size == 0:
        return float("nan")
    n = max(1, int(round(volume_cc_ * 1000.0 / np.prod(spacing))))
    return float(d[min(n, d.size) - 1])


def volume_at_dose(dose, mask, dose_gy: float) -> float:
    """V_x Gy: percentage of the volume receiving >= x Gy."""
    d = np.asarray(dose)[np.asarray(mask, bool)]
    if d.size == 0:
        return float("nan")
    return float(100.0 * np.count_nonzero(d >= dose_gy) / d.size)


def mean_dose(dose, mask) -> float:
    d = np.asarray(dose)[np.asarray(mask, bool)]
    return float(d.mean()) if d.size else float("nan")


# Example constraints for conventional lung RT 60 Gy / 30 fx (educational;
# based loosely on QUANTEC / RTOG 0617 style limits — local protocols apply!)
LUNG_CONSTRAINTS = [
    # structure, metric, operator, limit, unit
    ("Lungs-GTV", "V20Gy", "<", 35.0, "%"),
    ("Lungs-GTV", "Dmean", "<", 20.0, "Gy"),
    ("Heart", "V50Gy", "<", 25.0, "%"),
    ("Heart", "Dmean", "<", 20.0, "Gy"),
    ("Esophagus", "Dmean", "<", 34.0, "Gy"),
    ("SpinalCord", "D0.03cc", "<", 50.0, "Gy"),
    ("PTV", "D95%", ">", 57.0, "Gy"),
]


def evaluate_metric(dose, mask, spacing, metric: str) -> float:
    """Evaluate a metric string: 'Dmean', 'V20Gy', 'D95%', 'D0.03cc', 'Dmax'."""
    if metric == "Dmean":
        return mean_dose(dose, mask)
    if metric == "Dmax":
        d = np.asarray(dose)[np.asarray(mask, bool)]
        return float(d.max()) if d.size else float("nan")
    if metric.startswith("V") and metric.endswith("Gy"):
        return volume_at_dose(dose, mask, float(metric[1:-2]))
    if metric.startswith("D") and metric.endswith("cc"):
        return dose_at_abs_volume(dose, mask, spacing, float(metric[1:-2]))
    if metric.startswith("D") and metric.endswith("%"):
        return dose_at_volume(dose, mask, float(metric[1:-1]))
    raise ValueError(f"Unknown metric: {metric}")


def check_constraints(dose, structures: dict, spacing, constraints=LUNG_CONSTRAINTS) -> pd.DataFrame:
    """Evaluate a list of constraints; returns a table with PASS/FAIL."""
    rows = []
    for name, metric, op, limit, unit in constraints:
        if name not in structures:
            continue
        val = evaluate_metric(dose, structures[name], spacing, metric)
        ok = val < limit if op == "<" else val > limit
        rows.append({"structure": name, "metric": metric, "value": round(val, 2), "limit": f"{op} {limit:g} {unit}", "status": "OK" if ok else "PRZEKROCZONY"})
    return pd.DataFrame(rows)
