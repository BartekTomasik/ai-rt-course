"""Simulated post-deployment monitoring of an autosegmentation model (block 7).

The "AI" contours are reference contours with errors drawn from a *regime*
(baseline, after a CT protocol change, after a model update...). Each week a
few patients are treated; for each we compute Dice/HD95 between the AI
contour and the clinician-approved contour. Control charts then look for drift.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import metrics
from .autoseg import perturb_mask
from .phantom import make_phantom

# Error regimes: per organ, distributions of perturbation parameters.
# Each value is (mean, sd) for normal draws or (low, high) for "U" (uniform) draws.
REGIMES = {
    "model v1 (wdrożenie)": {
        "Heart": {"dilate_mm": ("N", 2.5, 1.5), "boundary_noise_mm": ("U", 1.5, 4.0)},
        "Esophagus": {"shift_y_mm": ("N", 0.0, 1.5), "drop_caudal_frac": ("U", 0.0, 0.08)},
    },
    "nowy protokół CT (kontrast, cieńsze warstwy)": {
        "Heart": {"dilate_mm": ("N", 5.0, 1.5), "boundary_noise_mm": ("U", 2.0, 4.5)},
        "Esophagus": {"shift_y_mm": ("N", 0.0, 1.5), "drop_caudal_frac": ("U", 0.1, 0.3)},
    },
    "model v2 (aktualizacja producenta)": {
        "Heart": {"dilate_mm": ("N", 1.0, 1.0), "boundary_noise_mm": ("U", 1.0, 2.5)},
        "Esophagus": {"shift_y_mm": ("N", 3.0, 1.0), "drop_caudal_frac": ("U", 0.0, 0.05)},
    },
}


def _draw(spec, rng):
    kind, a, b = spec
    return float(rng.normal(a, b)) if kind == "N" else float(rng.uniform(a, b))


def make_pool(n=10, seed=0):
    """Small, fast phantoms used as 'patients'."""
    return [make_phantom(seed=500 + seed * 100 + i, shape=(24, 96, 96), spacing=(5.0, 4.0, 4.0), with_dose=False)
            for i in range(n)]


def simulate_case(case, regime: dict, rng, organs=("Heart", "Esophagus")):
    rows = []
    for organ in organs:
        if organ not in case.structures or organ not in regime:
            continue
        p = {k: _draw(v, rng) for k, v in regime[organ].items()}
        shift = (0.0, p.pop("shift_y_mm", 0.0), 0.0)
        ref = case.structures[organ]
        ai = perturb_mask(ref, case.spacing, seed=int(rng.integers(1 << 30)), shift_mm=shift, **p)
        rows.append({"organ": organ, "Dice": metrics.dice(ref, ai), "HD95_mm": min(metrics.hd95(ref, ai, case.spacing), 100.0)})
    return rows


def simulate_weeks(n_weeks=26, patients_per_week=5, events=None, pool=None, seed=0, organs=("Heart", "Esophagus")):
    """Simulate weekly QA data. events: {week: regime_name} (week numbering from 1)."""
    rng = np.random.default_rng(seed)
    pool = pool or make_pool(10, seed)
    events = events or {}
    regime_name = "model v1 (wdrożenie)"
    rows = []
    for week in range(1, n_weeks + 1):
        regime_name = events.get(week, regime_name)
        for p in range(patients_per_week):
            case = pool[int(rng.integers(len(pool)))]
            for r in simulate_case(case, REGIMES[regime_name], rng, organs):
                rows.append({"week": week, "patient": f"W{week:02d}P{p + 1}", "regime": regime_name, **r})
    return pd.DataFrame(rows)


def shewhart_limits(baseline_values, k=3.0):
    """Mean and +-k SD limits from the baseline period."""
    m, s = float(np.mean(baseline_values)), float(np.std(baseline_values, ddof=1))
    return m, m - k * s, m + k * s, s


def cusum_lower(values, target, sd, k=0.5, h=4.0):
    """One-sided lower CUSUM (detects a DECREASE). Returns (S array, first alarm index or None)."""
    s, out, alarm = 0.0, [], None
    for i, x in enumerate(values):
        s = max(0.0, s + (target - k * sd) - x)
        out.append(s)
        if alarm is None and s > h * sd:
            alarm = i
    return np.array(out), alarm


def evaluate_acceptance(df: pd.DataFrame, criteria: dict) -> pd.DataFrame:
    """Check commissioning criteria per organ.

    criteria = {organ: {"Dice_median_min": .., "HD95_p90_max": .., "Dice_min_case": ..}}
    """
    rows = []
    for organ, crit in criteria.items():
        d = df[df.organ == organ]
        if d.empty:
            continue
        checks = []
        if "Dice_median_min" in crit:
            checks.append(("mediana Dice", d.Dice.median(), ">=", crit["Dice_median_min"]))
        if "HD95_p90_max" in crit:
            checks.append(("90. percentyl HD95 [mm]", d.HD95_mm.quantile(0.9), "<=", crit["HD95_p90_max"]))
        if "Dice_min_case" in crit:
            checks.append(("najgorszy przypadek Dice", d.Dice.min(), ">=", crit["Dice_min_case"]))
        for name, val, op, lim in checks:
            ok = val >= lim if op == ">=" else val <= lim
            rows.append({"narząd": organ, "kryterium": name, "wartość": round(float(val), 3),
                         "wymaganie": f"{op} {lim}", "wynik": "SPEŁNIONE" if ok else "NIESPEŁNIONE"})
    return pd.DataFrame(rows)
