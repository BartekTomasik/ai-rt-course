"""Toy dose model for teaching.

The model sums a few coplanar "beams". Each beam:
- has an aperture shaped to the target projection (beam's-eye view, per slice),
- is attenuated exponentially with depth,
- is blurred with a Gaussian penumbra.

It reproduces qualitative features of a real plan (conformal high dose, low-dose
"bath" along beam paths, steep gradients) but it is NOT a dose calculation
algorithm. Heterogeneity, scatter and MLC physics are ignored.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage

DEFAULT_ANGLES = (20, 160, 210, 270, 330)  # degrees, IEC-like gantry angles


def _coords_mm(shape, spacing):
    """Return z, y, x coordinate grids (mm) for array index grid (z, y, x)."""
    nz, ny, nx = shape
    sz, sy, sx = spacing
    z = (np.arange(nz) * sz)[:, None, None]
    y = (np.arange(ny) * sy)[None, :, None]
    x = (np.arange(nx) * sx)[None, None, :]
    return z, y, x


def compute_dose(
    ptv: np.ndarray,
    spacing,
    body: np.ndarray | None = None,
    prescription: float = 60.0,
    angles=DEFAULT_ANGLES,
    weights=None,
    margin_mm: float = 5.0,
    penumbra_mm: float = 4.0,
    mu_per_mm: float = 0.005,
    normalize: str = "D95",
    scatter_fraction: float = 0.08,
    scatter_mm: float = 25.0,
) -> np.ndarray:
    """Compute a toy dose distribution (Gy) on the same grid as `ptv`.

    Parameters
    ----------
    ptv : bool array (z, y, x) — target mask.
    spacing : (sz, sy, sx) in mm.
    body : optional bool mask; dose outside the body is set to 0.
    prescription : dose (Gy) to which the target is normalised.
    angles : gantry angles in degrees (0 = beam from anterior).
    weights : relative beam weights (default: equal).
    margin_mm : extra aperture margin around the target projection.
    penumbra_mm : Gaussian sigma of the penumbra.
    mu_per_mm : effective attenuation coefficient.
    normalize : "D95" (95% of PTV gets the prescription) or "mean".
    scatter_fraction, scatter_mm : amplitude and width of the crude scatter term.
    """
    ptv = np.asarray(ptv, bool)
    if not ptv.any():
        raise ValueError("PTV mask is empty")
    spacing = tuple(float(s) for s in spacing)
    weights = np.ones(len(angles)) if weights is None else np.asarray(weights, float)

    z, y, x = _coords_mm(ptv.shape, spacing)
    zi, yi, xi = np.nonzero(ptv)
    iso_y = yi.mean() * spacing[1]
    iso_x = xi.mean() * spacing[2]
    ry = y - iso_y
    rx = x - iso_x

    dose = np.zeros(ptv.shape, dtype=np.float32)
    for ang, w in zip(angles, weights):
        th = np.deg2rad(ang)
        # LPS: +x = patient left, +y = posterior. Gantry 0 -> beam travels +y.
        dx, dy = -np.sin(th), np.cos(th)  # beam direction
        ux, uy = np.cos(th), np.sin(th)  # lateral (beam's-eye-view) axis
        u = rx * ux + ry * uy  # (1, ny, nx)
        s = rx * dx + ry * dy  # depth relative to isocentre
        u_ptv = (xi * spacing[2] - iso_x) * ux + (yi * spacing[1] - iso_y) * uy
        fluence = np.zeros(ptv.shape, dtype=np.float32)
        for k in np.unique(zi):
            sel = zi == k
            lo = u_ptv[sel].min() - margin_mm
            hi = u_ptv[sel].max() + margin_mm
            fluence[k] = ((u[0] >= lo) & (u[0] <= hi)).astype(np.float32)
        # cranio-caudal margin: dilate along z by margin
        nz_m = int(round(margin_mm / spacing[0]))
        if nz_m > 0:
            fluence = ndimage.maximum_filter1d(fluence, size=2 * nz_m + 1, axis=0)
        atten = np.exp(-mu_per_mm * s).astype(np.float32)
        dose += w * fluence * atten

    sigma = [penumbra_mm / s for s in spacing]
    primary = ndimage.gaussian_filter(dose, sigma=sigma)
    # crude scatter: wide, low-amplitude blur (gives realistic low-dose DVH tails)
    scatter = ndimage.gaussian_filter(dose, sigma=[scatter_mm / s for s in spacing])
    dose = primary + scatter_fraction * scatter
    if body is not None:
        dose *= np.asarray(body, bool)

    vals = dose[ptv]
    ref = np.percentile(vals, 5) if normalize == "D95" else vals.mean()
    dose *= prescription / max(ref, 1e-6)
    return dose.astype(np.float32)
