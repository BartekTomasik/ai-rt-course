"""Reading DICOM-RT objects into numpy arrays.

Supports the common case: axial CT, ImageOrientationPatient = [1,0,0,0,1,0]
(head-first supine and similar). Oblique acquisitions are rejected with a
clear message rather than handled silently.
"""
from __future__ import annotations

import os
from collections import defaultdict

import numpy as np

from .case import Case


def scan_folder(folder: str) -> dict:
    """Group DICOM files in `folder` (recursively) by Modality.

    Returns {modality: [paths]}; CT paths are sorted along z.
    """
    import pydicom

    groups = defaultdict(list)
    for root, _, files in os.walk(folder):
        for f in files:
            p = os.path.join(root, f)
            try:
                ds = pydicom.dcmread(p, stop_before_pixels=True)
            except Exception:
                continue
            groups[str(getattr(ds, "Modality", "UNKNOWN"))].append(p)
    if "CT" in groups:
        groups["CT"] = sorted(groups["CT"], key=lambda p: float(pydicom.dcmread(p, stop_before_pixels=True).ImagePositionPatient[2]))
    return dict(groups)


def describe(path: str, max_items: int = 40) -> str:
    """Short, human-readable list of the most relevant tags of a DICOM file."""
    import pydicom

    ds = pydicom.dcmread(path, stop_before_pixels=True)
    keys = [
        "Modality", "SOPClassUID", "PatientID", "StudyInstanceUID", "SeriesInstanceUID",
        "FrameOfReferenceUID", "SeriesDescription", "ImagePositionPatient",
        "ImageOrientationPatient", "PixelSpacing", "SliceThickness", "Rows", "Columns",
        "RescaleSlope", "RescaleIntercept", "DoseUnits", "DoseType", "DoseSummationType",
        "DoseGridScaling", "NumberOfFrames", "RTPlanLabel", "StructureSetLabel",
    ]
    lines = []
    for k in keys:
        if k in ds:
            val = ds.data_element(k).value
            s = str(val)
            lines.append(f"{k:28s} {s[:80]}")
    return "\n".join(lines[:max_items])


def load_ct(paths) -> tuple:
    """Load a CT series. Returns (volume_HU (z,y,x) float32, spacing (sz,sy,sx), origin (x,y,z), datasets)."""
    import pydicom

    dss = [pydicom.dcmread(p) for p in paths]
    dss.sort(key=lambda d: float(d.ImagePositionPatient[2]))
    iop = np.array(dss[0].ImageOrientationPatient, float)
    if not np.allclose(iop, [1, 0, 0, 0, 1, 0], atol=1e-3):
        raise NotImplementedError(f"Only axial, non-rotated CT supported (IOP={iop.tolist()})")
    vol = np.stack([d.pixel_array.astype(np.float32) * float(getattr(d, "RescaleSlope", 1)) + float(getattr(d, "RescaleIntercept", 0)) for d in dss])
    zs = np.array([float(d.ImagePositionPatient[2]) for d in dss])
    sz = float(np.median(np.diff(zs))) if len(zs) > 1 else float(dss[0].SliceThickness)
    sy, sx = (float(v) for v in dss[0].PixelSpacing)
    x0, y0, z0 = (float(v) for v in dss[0].ImagePositionPatient)
    return vol, (sz, sy, sx), (x0, y0, z0), dss


def list_rois(rtstruct_path: str) -> list:
    import pydicom

    ds = pydicom.dcmread(rtstruct_path)
    return [r.ROIName for r in ds.StructureSetROISequence]


def load_rtstruct(rtstruct_path: str, shape, spacing, origin, names=None) -> dict:
    """Rasterise RTSTRUCT contours onto the CT grid. Returns {name: bool mask}.

    Points are tested at voxel centres; several contours on one slice are
    combined with XOR, so holes (e.g. a ring) are handled.
    """
    import pydicom
    from matplotlib.path import Path

    ds = pydicom.dcmread(rtstruct_path)
    nz, ny, nx = shape
    sz, sy, sx = spacing
    x0, y0, z0 = origin
    num_to_name = {r.ROINumber: r.ROIName for r in ds.StructureSetROISequence}
    yy, xx = np.mgrid[0:ny, 0:nx]
    pts_xy = np.stack([x0 + xx.ravel() * sx, y0 + yy.ravel() * sy], axis=1)
    out = {}
    for rc in ds.ROIContourSequence:
        name = num_to_name.get(rc.ReferencedROINumber, f"ROI_{rc.ReferencedROINumber}")
        if names is not None and name not in names:
            continue
        mask = np.zeros(shape, bool)
        for c in getattr(rc, "ContourSequence", []):
            data = np.asarray(c.ContourData, float).reshape(-1, 3)
            k = int(round((data[0, 2] - z0) / sz))
            if not 0 <= k < nz or len(data) < 3:
                continue
            # bounding box speeds things up for small structures
            xmin, ymin = data[:, 0].min(), data[:, 1].min()
            xmax, ymax = data[:, 0].max(), data[:, 1].max()
            sel = (pts_xy[:, 0] >= xmin - sx) & (pts_xy[:, 0] <= xmax + sx) & (pts_xy[:, 1] >= ymin - sy) & (pts_xy[:, 1] <= ymax + sy)
            inside = np.zeros(ny * nx, bool)
            inside[sel] = Path(data[:, :2]).contains_points(pts_xy[sel])
            mask[k] ^= inside.reshape(ny, nx)
        out[name] = mask
    return out


def load_rtdose(rtdose_path: str, shape=None, spacing=None, origin=None):
    """Load RTDOSE. If CT geometry is given, resample (trilinear) onto CT grid.

    Returns dose (Gy) array; without CT geometry also returns its own geometry.
    """
    import pydicom
    from scipy.interpolate import RegularGridInterpolator

    ds = pydicom.dcmread(rtdose_path)
    dose = ds.pixel_array.astype(np.float32) * float(ds.DoseGridScaling)
    if dose.ndim == 2:
        dose = dose[None]
    x0, y0, z0 = (float(v) for v in ds.ImagePositionPatient)
    sy, sx = (float(v) for v in ds.PixelSpacing)
    offs = np.asarray(ds.GridFrameOffsetVector, float)
    zs = z0 + offs
    ys = y0 + np.arange(dose.shape[1]) * sy
    xs = x0 + np.arange(dose.shape[2]) * sx
    if shape is None:
        return dose, {"z": zs, "y": ys, "x": xs}
    interp = RegularGridInterpolator((zs, ys, xs), dose, bounds_error=False, fill_value=0.0)
    nz, ny, nx = shape
    cz = origin[2] + np.arange(nz) * spacing[0]
    cy = origin[1] + np.arange(ny) * spacing[1]
    cx = origin[0] + np.arange(nx) * spacing[2]
    out = np.empty(shape, np.float32)
    Y, X = np.meshgrid(cy, cx, indexing="ij")
    for k in range(nz):
        pts = np.stack([np.full(Y.size, cz[k]), Y.ravel(), X.ravel()], axis=1)
        out[k] = interp(pts).reshape(ny, nx)
    return out


def plan_summary(rtplan_path: str) -> dict:
    """Key information from an RTPLAN: prescription, fractions, beams."""
    import pydicom

    ds = pydicom.dcmread(rtplan_path)
    info = {"label": getattr(ds, "RTPlanLabel", ""), "geometry": getattr(ds, "RTPlanGeometry", "")}
    if "DoseReferenceSequence" in ds:
        info["prescription_Gy"] = [float(getattr(d, "TargetPrescriptionDose", np.nan)) for d in ds.DoseReferenceSequence]
    if "FractionGroupSequence" in ds:
        info["fractions"] = int(ds.FractionGroupSequence[0].NumberOfFractionsPlanned)
    beams = []
    for b in getattr(ds, "BeamSequence", []):
        cp0 = b.ControlPointSequence[0]
        beams.append({
            "name": str(getattr(b, "BeamName", "")),
            "type": str(getattr(b, "BeamType", "")),
            "radiation": str(getattr(b, "RadiationType", "")),
            "energy_MV": float(getattr(cp0, "NominalBeamEnergy", np.nan)),
            "gantry_deg": float(getattr(cp0, "GantryAngle", np.nan)),
            "control_points": int(getattr(b, "NumberOfControlPoints", 0)),
        })
    info["beams"] = beams
    return info


def load_case_from_folder(folder: str, case_id: str | None = None, structure_names=None) -> Case:
    """Read a whole RT case (CT + RTSTRUCT [+ RTDOSE]) from a folder."""
    g = scan_folder(folder)
    if "CT" not in g:
        raise FileNotFoundError(f"No CT images found in {folder}")
    ct, spacing, origin, dss = load_ct(g["CT"])
    structures = {}
    if "RTSTRUCT" in g:
        structures = load_rtstruct(g["RTSTRUCT"][0], ct.shape, spacing, origin, names=structure_names)
    dose = None
    if "RTDOSE" in g:
        dose = load_rtdose(g["RTDOSE"][0], ct.shape, spacing, origin)
    meta = {"files": g}
    if "RTPLAN" in g:
        meta["plan"] = plan_summary(g["RTPLAN"][0])
    return Case(ct=ct, spacing=spacing, origin=origin, structures=structures, dose=dose,
                case_id=case_id or str(dss[0].PatientID), source="dicom", meta=meta)
