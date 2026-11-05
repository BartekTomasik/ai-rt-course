"""Linear-quadratic (LQ) radiobiology for teaching: BED, EQD2, voxel-wise conversion.

    BED  = n d (1 + d / (alpha/beta))
    EQD2 = BED / (1 + 2 / (alpha/beta))

n = number of fractions, d = dose per fraction. Voxel-wise conversion assumes
that every voxel receives the same number of fractions as the plan with dose
per fraction D_voxel / n. Not modelled unless stated: incomplete repair,
dose-rate effects, validity of LQ at very high doses per fraction.

Adapted (simplified, numpy-only) from rt_toolkit.radiobiology
(https://github.com/BartekTomasik/rt-toolkit, MIT licence, same author).
Educational code — not for clinical decisions.
"""
from __future__ import annotations

import numpy as np

# Typical alpha/beta values (Gy) used in teaching. ALWAYS check against the
# literature for the specific endpoint; uncertainties are large.
ALPHA_BETA_TYPICAL = {
    "guz (typowo)": 10.0,
    "tkanki wcześnie reagujące": 10.0,
    "tkanki późno reagujące": 3.0,
    "rdzeń kręgowy": 2.0,
    "mózg": 2.0,
    "gruczoł krokowy (rak)": 1.5,
    "pierś (rak/tkanki)": 3.5,
    "odbytnica (późne)": 3.0,
}


def _check(n_fractions, alpha_beta):
    if np.any(np.asarray(n_fractions) <= 0):
        raise ValueError("Liczba frakcji musi być > 0")
    if np.any(np.asarray(alpha_beta) <= 0):
        raise ValueError("alpha/beta musi być > 0")


def _out(x):
    x = np.asarray(x, float)
    return x.item() if x.ndim == 0 else x


def bed(total_dose, n_fractions, alpha_beta):
    """Biologically effective dose (Gy) of `total_dose` delivered in `n_fractions`."""
    _check(n_fractions, alpha_beta)
    D = np.asarray(total_dose, float)
    return _out(D * (1.0 + (D / n_fractions) / alpha_beta))


def eqd2(total_dose, n_fractions, alpha_beta):
    """Equivalent dose in 2 Gy fractions (Gy)."""
    _check(n_fractions, alpha_beta)
    D = np.asarray(total_dose, float)
    return _out(D * (D / n_fractions + alpha_beta) / (2.0 + alpha_beta))


def eqd2_from_bed(bed_value, alpha_beta):
    return _out(np.asarray(bed_value, float) / (1.0 + 2.0 / np.asarray(alpha_beta, float)))


def total_dose_for_eqd2(target_eqd2, n_fractions, alpha_beta):
    """Physical total dose in `n_fractions` giving `target_eqd2` (inverse of eqd2).

    Solves D^2/n + ab*D - EQD2*(2+ab) = 0 for D > 0.
    """
    _check(n_fractions, alpha_beta)
    e = np.asarray(target_eqd2, float)
    a, b, c = 1.0 / n_fractions, alpha_beta, -e * (2.0 + alpha_beta)
    return _out((-b + np.sqrt(b * b - 4 * a * c)) / (2 * a))


def alpha_beta_map(structures: dict, shape, default: float = 3.0, overrides: dict | None = None) -> np.ndarray:
    """Voxel map of alpha/beta: `default` everywhere, `overrides` {structure: ab} applied in order."""
    m = np.full(shape, float(default))
    for name, ab in (overrides or {}).items():
        if name in structures:
            m[np.asarray(structures[name], bool)] = float(ab)
    return m


def dose_to_eqd2(dose, n_fractions, alpha_beta):
    """Voxel-wise EQD2 of a dose array; alpha_beta can be a scalar or a voxel map."""
    return np.asarray(eqd2(np.asarray(dose, float), n_fractions, alpha_beta), float)


def sum_eqd2(courses, alpha_beta, recovery_factors=None):
    """Voxel-wise cumulative EQD2 of several courses [(dose_array, n_fractions), ...].

    recovery_factors: fraction of each course's EQD2 that is RETAINED
    (1 = no recovery; e.g. [0.75, 1.0] = 25% recovery of the first course).
    Assumes all dose arrays are on the same, registered grid (no deformable
    registration). Research/teaching use only.
    """
    if not courses:
        raise ValueError("Brak kursów leczenia")
    rf = [1.0] * len(courses) if recovery_factors is None else list(recovery_factors)
    if len(rf) != len(courses):
        raise ValueError("recovery_factors: jedna wartość na kurs")
    total = np.zeros(np.shape(courses[0][0]), float)
    for (d, n), r in zip(courses, rf):
        if np.shape(d) != total.shape:
            raise ValueError("Dawki muszą być na wspólnej siatce (najpierw rejestracja i resampling)")
        total += r * dose_to_eqd2(d, n, alpha_beta)
    return total


def bed_with_time(total_dose, n_fractions, alpha_beta, overall_time_days, kickoff_days=28.0, k_gy_per_day=0.9):
    """BED with a simple repopulation correction: BED - K (T - Tk) for T > Tk.

    Default K = 0.9 Gy10/day and Tk = 28 days are textbook values for head-and-neck
    squamous cell carcinoma; they are uncertain and site-specific.
    """
    b = np.asarray(bed(total_dose, n_fractions, alpha_beta), float)
    loss = k_gy_per_day * max(0.0, float(overall_time_days) - kickoff_days)
    return _out(b - loss)
