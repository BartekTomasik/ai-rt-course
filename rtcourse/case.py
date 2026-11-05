"""Container for one RT case (image + structures + optional dose)."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class Case:
    """One patient/phantom on a regular grid.

    Arrays are indexed (z, y, x) = (slice, row, column).
    spacing = (sz, sy, sx) in mm; origin = (x0, y0, z0) in mm (DICOM patient
    coordinates, LPS) of voxel [0, 0, 0].
    """

    ct: np.ndarray
    spacing: tuple
    origin: tuple
    structures: dict = field(default_factory=dict)
    dose: np.ndarray | None = None
    case_id: str = "case"
    source: str = "synthetic"
    meta: dict = field(default_factory=dict)

    @property
    def shape(self):
        return self.ct.shape

    def summary(self) -> str:
        sz, sy, sx = self.spacing
        lines = [
            f"Przypadek: {self.case_id}  (źródło: {self.source})",
            f"  CT: {self.ct.shape[0]} warstw x {self.ct.shape[1]} x {self.ct.shape[2]} pikseli, "
            f"voxel {sx:.2f} x {sy:.2f} x {sz:.2f} mm",
            f"  Struktury: {', '.join(self.structures) or '(brak)'}",
            f"  Dawka: {'tak, max %.1f Gy' % float(self.dose.max()) if self.dose is not None else 'brak'}",
        ]
        return "\n".join(lines)

    def save_npz(self, path):
        """Compact storage used in the course pack."""
        arrays = {f"mask__{k}": np.packbits(v.astype(bool).ravel()) for k, v in self.structures.items()}
        if self.dose is not None:
            arrays["dose"] = self.dose.astype(np.float32)
        np.savez_compressed(
            path,
            ct=self.ct.astype(np.int16),
            spacing=np.asarray(self.spacing, float),
            origin=np.asarray(self.origin, float),
            case_id=np.array(self.case_id),
            source=np.array(self.source),
            **arrays,
        )

    @classmethod
    def load_npz(cls, path) -> "Case":
        f = np.load(path, allow_pickle=False)
        ct = f["ct"].astype(np.float32)
        n = ct.size
        structures = {
            k[len("mask__"):]: np.unpackbits(f[k])[:n].reshape(ct.shape).astype(bool)
            for k in f.files
            if k.startswith("mask__")
        }
        dose = f["dose"] if "dose" in f.files else None
        return cls(
            ct=ct,
            spacing=tuple(f["spacing"].tolist()),
            origin=tuple(f["origin"].tolist()),
            structures=structures,
            dose=dose,
            case_id=str(f["case_id"]),
            source=str(f["source"]),
        )
