"""Plotting helpers (matplotlib)."""
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from skimage import measure

from .phantom import STRUCTURE_COLORS
from . import metrics

WINDOWS = {  # (center, width) in HU
    "mediastinum": (40, 400),
    "lung": (-600, 1500),
    "bone": (400, 1800),
    "soft": (50, 350),
}


def _color(name, i=0):
    if name in STRUCTURE_COLORS:
        return tuple(c / 255 for c in STRUCTURE_COLORS[name])
    return plt.cm.tab10(i % 10)


def _extent(case, view):
    sz, sy, sx = case.spacing
    nz, ny, nx = case.shape
    x0, y0, z0 = case.origin
    if view == "axial":
        return [x0 - sx / 2, x0 + (nx - .5) * sx, y0 + (ny - .5) * sy, y0 - sy / 2]
    if view == "coronal":
        return [x0 - sx / 2, x0 + (nx - .5) * sx, z0 - sz / 2, z0 + (nz - .5) * sz]
    return [y0 - sy / 2, y0 + (ny - .5) * sy, z0 - sz / 2, z0 + (nz - .5) * sz]


def _take(vol, view, idx):
    if view == "axial":
        return vol[idx]
    if view == "coronal":
        return vol[:, idx, :]
    return vol[:, :, idx]


def show_slice(case, index=None, view="axial", window="mediastinum", structures=None,
               dose=None, dose_min=None, extra=None, ax=None, title=None, legend=True):
    """Show one slice with contours (solid) and optional dose colour wash.

    extra: dict {name: mask} drawn dashed (e.g. AI contours to compare).
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(6, 6))
    nz, ny, nx = case.shape
    if index is None:
        ref = case.structures.get("PTV", case.structures.get("Heart"))
        if ref is not None and ref.any():
            c = np.array(np.nonzero(ref)).mean(axis=1).round().astype(int)
            index = {"axial": c[0], "coronal": c[1], "sagittal": c[2]}[view]
        else:
            index = {"axial": nz // 2, "coronal": ny // 2, "sagittal": nx // 2}[view]
    wc, ww = WINDOWS.get(window, window) if isinstance(window, str) else window
    img = _take(case.ct, view, index)
    ext = _extent(case, view)
    origin = "upper" if view == "axial" else "lower"
    ax.imshow(img, cmap="gray", vmin=wc - ww / 2, vmax=wc + ww / 2, extent=ext, origin=origin, aspect="equal")
    if dose is not None:
        d = _take(dose, view, index)
        dmin = dose_min if dose_min is not None else 0.1 * float(np.max(dose))
        ax.imshow(np.ma.masked_less(d, dmin), cmap="jet", alpha=0.35, vmin=dmin, vmax=float(np.max(dose)), extent=ext, origin=origin, aspect="equal")
    handles = []
    names = list(case.structures) if structures is None else structures

    def draw(masks, style, suffix):
        for i, name in enumerate(names):
            if name not in masks:
                continue
            m = _take(masks[name], view, index)
            if not m.any():
                continue
            col = _color(name, i)
            for cnt in measure.find_contours(m.astype(float), 0.5):
                # convert index -> mm
                r, cc = cnt[:, 0], cnt[:, 1]
                X = ext[0] + (cc + .5) * (ext[1] - ext[0]) / m.shape[1]
                if origin == "upper":
                    Y = ext[3] + (r + .5) * (ext[2] - ext[3]) / m.shape[0]
                else:
                    Y = ext[2] + (r + .5) * (ext[3] - ext[2]) / m.shape[0]
                ax.plot(X, Y, style, color=col, lw=1.3)
            handles.append(plt.Line2D([], [], color=col, ls=style, label=name + suffix))

    draw(case.structures, "-", "")
    if extra:
        draw(extra, "--", " (AI)")
    if legend and handles:
        ax.legend(handles=handles, fontsize=7, loc="lower right", framealpha=0.6)
    ax.set_title(title or f"{view}, przekrój {index}")
    ax.set_xlabel("mm")
    return ax


def show_three_views(case, dose=None, structures=None, window="mediastinum", extra=None):
    fig, axs = plt.subplots(1, 3, figsize=(15, 5))
    for ax, v in zip(axs, ["axial", "coronal", "sagittal"]):
        show_slice(case, view=v, dose=dose, structures=structures, window=window, ax=ax, extra=extra, legend=(v == "axial"))
    plt.tight_layout()
    return fig


def plot_dvh(dose, structures: dict, names=None, ax=None, style="-", label_suffix="", spacing=None):
    if ax is None:
        _, ax = plt.subplots(figsize=(8, 5))
    names = names or list(structures)
    for i, n in enumerate(names):
        if n not in structures:
            continue
        b, v = metrics.dvh(dose, structures[n], max_dose=float(np.max(dose)) * 1.05)
        ax.plot(b, v, style, color=_color(n, i), label=n + label_suffix)
    ax.set_xlabel("Dawka [Gy]")
    ax.set_ylabel("Objętość [%]")
    ax.set_ylim(0, 102)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    ax.set_title("Skumulowany histogram dawka–objętość (DVH)")
    return ax


def slice_browser(case, dose=None, structures=None, extra=None, window="mediastinum"):
    """Interactive slider (ipywidgets) — falls back to a static image without widgets.

    Set RTCOURSE_STATIC_PLOTS=1 (done by scripts/run_notebooks.py) to force the static image:
    in a headless kernel without a front end the widget can block.
    """
    import os

    try:
        import ipywidgets as w
    except ImportError:
        w = None
    if w is None or os.environ.get("RTCOURSE_STATIC_PLOTS") == "1":
        show_slice(case, dose=dose, structures=structures, extra=extra, window=window)
        plt.show()
        return

    def f(k=case.shape[0] // 2, okno=window):
        show_slice(case, index=k, dose=dose, structures=structures, extra=extra, window=okno)
        plt.show()

    w.interact(f, k=w.IntSlider(min=0, max=case.shape[0] - 1, value=case.shape[0] // 2, description="warstwa"),
               okno=w.Dropdown(options=list(WINDOWS), value=window))
