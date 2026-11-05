"""Synthetic image-quality problems for 2D CT slices (block 2)."""
from __future__ import annotations

import numpy as np
from scipy import ndimage

from .phantom import make_phantom


def add_noise(img, sd_hu, rng):
    return img + rng.normal(0, sd_hu, img.shape)


def add_metal_streaks(img, strength, rng, n_streaks=None):
    """Bright/dark streaks radiating from a small dense object (e.g. a clip or prosthesis)."""
    ny, nx = img.shape
    cy, cx = rng.uniform(0.35, 0.65) * ny, rng.uniform(0.3, 0.7) * nx
    yy, xx = np.mgrid[0:ny, 0:nx]
    ang = np.arctan2(yy - cy, xx - cx)
    n = n_streaks or int(rng.integers(3, 7))
    phases = rng.uniform(0, np.pi, n)
    streak = np.zeros_like(img, dtype=float)
    for ph in phases:
        streak += np.cos(2 * (ang - ph)) ** 40 * rng.choice([-1, 1])
    r = np.hypot(yy - cy, xx - cx)
    out = img + strength * streak * np.exp(-r / (0.6 * nx))
    out[r < 1.5] = 2500
    return out


def add_motion(img, strength, rng):
    """Breathing/motion: ghost copy shifted in y."""
    shift = strength * rng.uniform(0.7, 1.3)
    ghost = ndimage.shift(img, (shift, 0), order=1, mode="nearest")
    return 0.65 * img + 0.35 * ghost


def add_ring(img, strength, rng):
    ny, nx = img.shape
    yy, xx = np.mgrid[0:ny, 0:nx]
    r = np.hypot(yy - ny / 2, xx - nx / 2)
    r0 = rng.uniform(0.15, 0.4) * nx
    return img + strength * np.exp(-((r - r0) ** 2) / 1.5)


def make_slice_dataset(n_patients=40, slices_per_patient=8, size=48, artifact="metal",
                       strength=150.0, positive_fraction=0.5, label_level="slice", seed=0,
                       base_noise_hu=20.0, low_dose_extra_noise=0.0):
    """Build a 2D slice dataset with patient IDs.

    label_level="slice": each slice independently has the artifact with prob. positive_fraction.
    label_level="patient": all slices of a patient share the label (e.g. "patient with prosthesis").
    low_dose_extra_noise > 0 adds extra noise to positive patients (a second, subtle signal).

    Returns X (n, size, size) float32 in HU, y (n,), groups (n,) patient index.
    """
    rng = np.random.default_rng(seed)
    X, y, g = [], [], []
    fn = {"metal": add_metal_streaks, "motion": add_motion, "ring": add_ring}[artifact]
    for p in range(n_patients):
        ph = make_phantom(seed=1000 + p + 97 * seed, shape=(slices_per_patient + 4, 2 * size, 2 * size),
                          spacing=(10.0, 4.0, 4.0), with_dose=False, noise_hu=0.0)
        patient_label = rng.random() < positive_fraction
        for k in range(2, 2 + slices_per_patient):
            img = ph.ct[k].reshape(size, 2, size, 2).mean(axis=(1, 3))
            lab = patient_label if label_level == "patient" else (rng.random() < positive_fraction)
            if lab:
                img = fn(img, strength, rng)
                img = add_noise(img, low_dose_extra_noise, rng) if low_dose_extra_noise else img
            img = add_noise(img, base_noise_hu, rng)
            X.append(np.clip(img, -1024, 3000).astype(np.float32))
            y.append(int(lab))
            g.append(p)
    return np.array(X), np.array(y), np.array(g)


def add_corner_marker(X, y, rng, p_match=0.95, value=1500.0):
    """Shortcut: a bright corner 'label' that co-occurs with class 1 with prob p_match."""
    X = X.copy()
    for i in range(len(X)):
        put = (rng.random() < p_match) == bool(y[i])
        if put:
            X[i, 1:5, 1:5] = value
    return X
