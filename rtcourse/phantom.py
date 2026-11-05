"""Synthetic thorax phantom and a minimal DICOM-RT writer.

`make_phantom()` builds a simple "patient": body, lungs, heart, spine,
spinal cord, oesophagus and a lung tumour (GTV) with PTV margin, plus a toy
dose distribution. `write_dicom_rt()` saves it as a DICOM CT series,
RTSTRUCT, RTDOSE and RTPLAN, so the same code paths as for real data can be
exercised without any patient data or network access.
"""
from __future__ import annotations

import datetime as _dt
import os

import numpy as np
from scipy import ndimage

from .case import Case
from .dose import DEFAULT_ANGLES, compute_dose

STRUCTURE_COLORS = {
    "BODY": (0, 255, 0),
    "Lung_L": (0, 128, 255),
    "Lung_R": (0, 200, 255),
    "Heart": (255, 0, 0),
    "Esophagus": (255, 160, 0),
    "SpinalCord": (255, 255, 0),
    "GTV": (255, 0, 255),
    "PTV": (180, 0, 255),
}

OAR_NAMES = ["Lung_L", "Lung_R", "Heart", "Esophagus", "SpinalCord"]


def _ellipsoid(X, Y, Z, c, r):
    return ((X - c[0]) / r[0]) ** 2 + ((Y - c[1]) / r[1]) ** 2 + ((Z - c[2]) / r[2]) ** 2 <= 1.0


def make_phantom(
    seed: int = 0,
    shape=(56, 192, 192),
    spacing=(2.5, 2.0, 2.0),
    tumor_radius_mm: float | None = None,
    tumor_center_mm=None,
    ptv_margin_mm: float = 8.0,
    with_dose: bool = True,
    prescription: float = 60.0,
    noise_hu: float = 15.0,
    variability: float = 1.0,
) -> Case:
    """Create a synthetic thorax phantom.

    seed controls random anatomical variation (0 = reference phantom when
    variability=0). Coordinates are DICOM LPS: +x = patient left,
    +y = posterior, +z = superior.
    """
    rng = np.random.default_rng(seed)
    v = variability

    def jit(scale):
        return float(rng.normal(0, scale * v))

    nz, ny, nx = shape
    sz, sy, sx = spacing
    origin = (-(nx - 1) / 2 * sx, -(ny - 1) / 2 * sy, -(nz - 1) / 2 * sz)
    Z = (origin[2] + np.arange(nz) * sz)[:, None, None]
    Y = (origin[1] + np.arange(ny) * sy)[None, :, None]
    X = (origin[0] + np.arange(nx) * sx)[None, None, :]

    body_a, body_b = 165 + jit(8), 115 + jit(6)
    body = ((X / body_a) ** 2 + (Y / body_b) ** 2 <= 1.0) & np.ones_like(Z, bool)
    inner = ((X / (body_a - 12)) ** 2 + (Y / (body_b - 10)) ** 2 <= 1.0) & body

    lung_r = _ellipsoid(X, Y, Z, (-72 + jit(4), 5 + jit(3), 5 + jit(5)), (50 + jit(3), 72 + jit(4), 80 + jit(5)))
    lung_l = _ellipsoid(X, Y, Z, (74 + jit(4), 5 + jit(3), 5 + jit(5)), (46 + jit(3), 70 + jit(4), 78 + jit(5)))
    heart = _ellipsoid(X, Y, Z, (22 + jit(5), -28 + jit(4), -25 + jit(5)), (50 + jit(4), 44 + jit(3), 45 + jit(4)))
    vert_body = ((X / 18) ** 2 + ((Y - 68) / 16) ** 2 <= 1.0) & np.ones_like(Z, bool)
    canal_bone = ((X / 13) ** 2 + ((Y - 94) / 13) ** 2 <= 1.0) & np.ones_like(Z, bool)
    canal = ((X / 8) ** 2 + ((Y - 94) / 8) ** 2 <= 1.0) & np.ones_like(Z, bool)
    cord = ((X / 5) ** 2 + ((Y - 94) / 5.5) ** 2 <= 1.0) & np.ones_like(Z, bool)
    eso_x = -6 + 4 * np.sin(Z / 40.0) + jit(2)
    eso = (((X - eso_x) / 8) ** 2 + ((Y - 42) / 7) ** 2 <= 1.0)
    sternum = ((X / 16) ** 2 + ((Y + body_b - 14) / 6) ** 2 <= 1.0) & np.ones_like(Z, bool)

    lung_r &= ~heart & inner
    lung_l &= ~heart & inner
    eso &= ~heart & ~vert_body

    # tumour in the right lung, slightly lobulated
    if tumor_radius_mm is None:
        tumor_radius_mm = float(np.clip(18 + jit(5), 8, 30))
    if tumor_center_mm is None:
        tumor_center_mm = (-40 + jit(10), -5 + jit(12), 0 + jit(15))
    cx, cy, cz = tumor_center_mm
    R = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2 + (Z - cz) ** 2)
    ang = np.arctan2(Y - cy, X - cx)
    lobul = 1 + 0.12 * np.sin(3 * ang + rng.uniform(0, 6.28))
    gtv = (R <= tumor_radius_mm * lobul) & body
    lung_r &= ~gtv
    lung_l &= ~gtv

    # HU map
    ct = np.full(shape, -1000.0, dtype=np.float32)
    ct[body] = -100.0  # subcutaneous fat
    ct[inner] = 40.0  # muscle / soft tissue
    ct[lung_r | lung_l] = -820.0
    ct[heart] = 45.0
    ct[eso] = 25.0
    ct[vert_body | canal_bone | sternum] = 650.0
    ct[canal] = 20.0
    ct[cord] = 30.0
    ct[gtv] = 35.0
    # lung texture (vessels) + noise
    tex = ndimage.gaussian_filter(rng.normal(0, 1, shape), 1.5)
    ct[lung_r | lung_l] += (60 * tex)[lung_r | lung_l]
    ct = ndimage.gaussian_filter(ct, 0.7)
    ct += rng.normal(0, noise_hu, shape).astype(np.float32)
    ct = np.clip(ct, -1024, 3000)

    # PTV = GTV + margin (anisotropic sampling handled by EDT)
    dist = ndimage.distance_transform_edt(~gtv, sampling=spacing)
    ptv = (dist <= ptv_margin_mm) & body

    structures = {
        "BODY": body,
        "Lung_L": lung_l,
        "Lung_R": lung_r,
        "Heart": heart & inner,
        "Esophagus": eso & inner,
        "SpinalCord": cord,
        "GTV": gtv,
        "PTV": ptv,
    }
    case = Case(
        ct=ct.astype(np.float32),
        spacing=tuple(float(s) for s in spacing),
        origin=tuple(float(o) for o in origin),
        structures=structures,
        case_id=f"PHANTOM{seed:03d}",
        source="synthetic",
        meta={"prescription_Gy": prescription, "fractions": 30, "seed": seed},
    )
    if with_dose:
        case.dose = compute_dose(ptv, spacing, body=body, prescription=prescription)
        case.meta["beam_angles"] = list(DEFAULT_ANGLES)
    return case


def make_cohort(n: int, start_seed: int = 1, **kwargs):
    """List of phantoms with random anatomical variation."""
    return [make_phantom(seed=start_seed + i, **kwargs) for i in range(n)]


# =================================================================== DICOM writer
def _uid():
    from pydicom.uid import generate_uid

    return generate_uid()


def _base_dataset(modality, sop_class, study, series_uid, case: Case):
    from pydicom.dataset import Dataset, FileMetaDataset
    from pydicom.uid import ExplicitVRLittleEndian, PYDICOM_IMPLEMENTATION_UID

    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = sop_class
    meta.MediaStorageSOPInstanceUID = _uid()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    meta.ImplementationClassUID = PYDICOM_IMPLEMENTATION_UID
    ds = Dataset()
    ds.file_meta = meta
    ds.SOPClassUID = sop_class
    ds.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    ds.Modality = modality
    ds.PatientName = "PHANTOM^SYNTHETIC"
    ds.PatientID = case.case_id
    ds.PatientBirthDate = ""
    ds.PatientSex = "O"
    ds.StudyInstanceUID = study["StudyInstanceUID"]
    ds.StudyDate = study["date"]
    ds.StudyTime = "120000"
    ds.StudyID = "1"
    ds.AccessionNumber = ""
    ds.ReferringPhysicianName = ""
    ds.SeriesInstanceUID = series_uid
    ds.SeriesNumber = study["series_counter"]
    study["series_counter"] += 1
    ds.FrameOfReferenceUID = study["FrameOfReferenceUID"]
    ds.Manufacturer = "rtcourse synthetic phantom (educational, not for clinical use)"
    ds.InstanceCreationDate = study["date"]
    return ds


def _save(ds, path):
    import pydicom

    if int(pydicom.__version__.split(".")[0]) >= 3:
        ds.save_as(path, enforce_file_format=True)
    else:  # pydicom 2.x
        ds.is_little_endian = True
        ds.is_implicit_VR = False
        ds.save_as(path, write_like_original=False)


def mask_to_contours(mask2d, origin_xy, spacing_xy):
    """Return list of (N, 2) arrays of (x, y) mm contour points for one slice."""
    from skimage import measure

    padded = np.pad(mask2d.astype(np.float32), 1)
    out = []
    for c in measure.find_contours(padded, 0.5):
        if len(c) < 4:
            continue
        rows, cols = c[:, 0] - 1, c[:, 1] - 1
        xs = origin_xy[0] + cols * spacing_xy[1]
        ys = origin_xy[1] + rows * spacing_xy[0]
        out.append(np.stack([xs, ys], axis=1)[:-1])  # drop duplicated closing point
    return out


def write_dicom_rt(case: Case, outdir: str, write_plan: bool = True) -> dict:
    """Write CT series + RTSTRUCT (+ RTDOSE, RTPLAN) for `case` into `outdir`.

    Returns a dict with file paths.
    """
    from pydicom.dataset import Dataset
    from pydicom.sequence import Sequence
    from pydicom.uid import CTImageStorage, RTStructureSetStorage, RTDoseStorage, RTPlanStorage

    os.makedirs(outdir, exist_ok=True)
    today = _dt.date.today().strftime("%Y%m%d")
    study = {
        "StudyInstanceUID": _uid(),
        "FrameOfReferenceUID": _uid(),
        "date": today,
        "series_counter": 1,
    }
    nz, ny, nx = case.ct.shape
    sz, sy, sx = case.spacing
    x0, y0, z0 = case.origin
    paths = {"CT": []}

    # ---------------- CT
    ct_series = _uid()
    ct_refs = []
    for k in range(nz):
        ds = _base_dataset("CT", CTImageStorage, study, ct_series, case)
        study["series_counter"] -= 1  # same series for all slices
        ds.SeriesDescription = "Synthetic thorax CT"
        ds.ImageType = ["ORIGINAL", "PRIMARY", "AXIAL"]
        ds.InstanceNumber = k + 1
        ds.ImagePositionPatient = [float(x0), float(y0), float(z0 + k * sz)]
        ds.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
        ds.PatientPosition = "HFS"
        ds.SliceThickness = float(sz)
        ds.PixelSpacing = [float(sy), float(sx)]
        ds.SliceLocation = float(z0 + k * sz)
        ds.Rows, ds.Columns = ny, nx
        ds.SamplesPerPixel = 1
        ds.PhotometricInterpretation = "MONOCHROME2"
        ds.BitsAllocated = 16
        ds.BitsStored = 16
        ds.HighBit = 15
        ds.PixelRepresentation = 1
        ds.RescaleIntercept = 0
        ds.RescaleSlope = 1
        ds.RescaleType = "HU"
        ds.KVP = 120
        ds.WindowCenter = 40
        ds.WindowWidth = 400
        ds.PixelData = np.round(case.ct[k]).astype(np.int16).tobytes()
        p = os.path.join(outdir, f"CT_{k + 1:04d}.dcm")
        _save(ds, p)
        paths["CT"].append(p)
        ct_refs.append((ds.SOPClassUID, ds.SOPInstanceUID))
    study["series_counter"] += 1

    # ---------------- RTSTRUCT
    ds = _base_dataset("RTSTRUCT", RTStructureSetStorage, study, _uid(), case)
    ds.SeriesDescription = "Synthetic structures"
    ds.StructureSetLabel = "RTCOURSE"
    ds.StructureSetName = "RTCOURSE"
    ds.StructureSetDate = today
    ds.StructureSetTime = "120000"
    ref_for = Dataset()
    ref_for.FrameOfReferenceUID = study["FrameOfReferenceUID"]
    rt_study = Dataset()
    rt_study.ReferencedSOPClassUID = "1.2.840.10008.3.1.2.3.1"
    rt_study.ReferencedSOPInstanceUID = study["StudyInstanceUID"]
    rt_series = Dataset()
    rt_series.SeriesInstanceUID = ct_series
    rt_series.ContourImageSequence = Sequence(
        [_img_ref(c, i) for c, i in ct_refs]
    )
    rt_study.RTReferencedSeriesSequence = Sequence([rt_series])
    ref_for.RTReferencedStudySequence = Sequence([rt_study])
    ds.ReferencedFrameOfReferenceSequence = Sequence([ref_for])
    roi_seq, contour_seq, obs_seq = [], [], []
    for n, (name, mask) in enumerate(case.structures.items(), start=1):
        roi = Dataset()
        roi.ROINumber = n
        roi.ReferencedFrameOfReferenceUID = study["FrameOfReferenceUID"]
        roi.ROIName = name
        roi.ROIGenerationAlgorithm = "MANUAL" if case.source != "autoseg" else "AUTOMATIC"
        roi_seq.append(roi)
        rc = Dataset()
        rc.ROIDisplayColor = list(STRUCTURE_COLORS.get(name, (200, 200, 200)))
        rc.ReferencedROINumber = n
        cs = []
        for k in range(nz):
            if not mask[k].any():
                continue
            for pts in mask_to_contours(mask[k], (x0, y0), (sy, sx)):
                c = Dataset()
                c.ContourGeometricType = "CLOSED_PLANAR"
                c.NumberOfContourPoints = len(pts)
                z = z0 + k * sz
                c.ContourData = [float(round(v, 3)) for p in pts for v in (p[0], p[1], z)]
                c.ContourImageSequence = Sequence([_img_ref(*ct_refs[k])])
                cs.append(c)
        rc.ContourSequence = Sequence(cs)
        contour_seq.append(rc)
        ob = Dataset()
        ob.ObservationNumber = n
        ob.ReferencedROINumber = n
        ob.RTROIInterpretedType = "PTV" if name.startswith("PTV") else ("GTV" if name.startswith("GTV") else ("EXTERNAL" if name == "BODY" else "ORGAN"))
        ob.ROIInterpreter = ""
        obs_seq.append(ob)
    ds.StructureSetROISequence = Sequence(roi_seq)
    ds.ROIContourSequence = Sequence(contour_seq)
    ds.RTROIObservationsSequence = Sequence(obs_seq)
    p = os.path.join(outdir, "RTSTRUCT.dcm")
    _save(ds, p)
    paths["RTSTRUCT"] = p
    struct_uid = (ds.SOPClassUID, ds.SOPInstanceUID)

    # ---------------- RTPLAN (minimal)
    plan_ref = None
    if write_plan and case.dose is not None:
        ds = _base_dataset("RTPLAN", RTPlanStorage, study, _uid(), case)
        ds.SeriesDescription = "Synthetic plan"
        ds.RTPlanLabel = "LUNG_60Gy"
        ds.RTPlanName = "Synthetic 3D-CRT"
        ds.RTPlanDate = today
        ds.RTPlanTime = "120000"
        ds.RTPlanGeometry = "PATIENT"
        ds.ApprovalStatus = "UNAPPROVED"
        rs = Dataset()
        rs.ReferencedSOPClassUID, rs.ReferencedSOPInstanceUID = struct_uid
        ds.ReferencedStructureSetSequence = Sequence([rs])
        rx = case.meta.get("prescription_Gy", 60.0)
        nfx = case.meta.get("fractions", 30)
        dr = Dataset()
        dr.DoseReferenceNumber = 1
        dr.DoseReferenceStructureType = "VOLUME"
        dr.DoseReferenceType = "TARGET"
        dr.DoseReferenceDescription = "PTV"
        dr.TargetPrescriptionDose = float(rx)
        ds.DoseReferenceSequence = Sequence([dr])
        ptv = case.structures.get("PTV")
        zi, yi, xi = np.nonzero(ptv)
        iso = [float(x0 + xi.mean() * sx), float(y0 + yi.mean() * sy), float(z0 + zi.mean() * sz)]
        angles = case.meta.get("beam_angles", list(DEFAULT_ANGLES))
        fg = Dataset()
        fg.FractionGroupNumber = 1
        fg.NumberOfFractionsPlanned = int(nfx)
        fg.NumberOfBeams = len(angles)
        fg.NumberOfBrachyApplicationSetups = 0
        rbs = []
        beams = []
        for b, ang in enumerate(angles, start=1):
            rb = Dataset()
            rb.ReferencedBeamNumber = b
            rb.BeamMeterset = 100.0
            rbs.append(rb)
            bm = Dataset()
            bm.BeamNumber = b
            bm.BeamName = f"G{int(ang):03d}"
            bm.BeamType = "STATIC"
            bm.RadiationType = "PHOTON"
            bm.TreatmentDeliveryType = "TREATMENT"
            bm.TreatmentMachineName = "VIRTUAL_LINAC"
            bm.PrimaryDosimeterUnit = "MU"
            bm.SourceAxisDistance = 1000.0
            bm.NumberOfWedges = 0
            bm.NumberOfCompensators = 0
            bm.NumberOfBoli = 0
            bm.NumberOfBlocks = 0
            bm.FinalCumulativeMetersetWeight = 1.0
            bm.NumberOfControlPoints = 2
            cps = []
            for ci, w in enumerate((0.0, 1.0)):
                cp = Dataset()
                cp.ControlPointIndex = ci
                cp.CumulativeMetersetWeight = w
                if ci == 0:
                    cp.NominalBeamEnergy = 6.0
                    cp.GantryAngle = float(ang)
                    cp.GantryRotationDirection = "NONE"
                    cp.BeamLimitingDeviceAngle = 0.0
                    cp.PatientSupportAngle = 0.0
                    cp.IsocenterPosition = iso
                cps.append(cp)
            bm.ControlPointSequence = Sequence(cps)
            beams.append(bm)
        fg.ReferencedBeamSequence = Sequence(rbs)
        ds.FractionGroupSequence = Sequence([fg])
        ds.BeamSequence = Sequence(beams)
        p = os.path.join(outdir, "RTPLAN.dcm")
        _save(ds, p)
        paths["RTPLAN"] = p
        plan_ref = (ds.SOPClassUID, ds.SOPInstanceUID)

    # ---------------- RTDOSE (coarser grid, cropped to body: shows resampling)
    if case.dose is not None:
        ds = _base_dataset("RTDOSE", RTDoseStorage, study, _uid(), case)
        ds.SeriesDescription = "Synthetic dose"
        step = 2
        body = case.structures.get("BODY", np.ones(case.ct.shape, bool))
        _, yy, xx = np.nonzero(body)
        y_lo, y_hi = max(yy.min() - step, 0), min(yy.max() + 2 * step, case.ct.shape[1])
        x_lo, x_hi = max(xx.min() - step, 0), min(xx.max() + 2 * step, case.ct.shape[2])
        d = case.dose[:, y_lo:y_hi:step, x_lo:x_hi:step]
        scaling = float(d.max()) / 60000.0 if d.max() > 0 else 1.0
        ds.DoseUnits = "GY"
        ds.DoseType = "PHYSICAL"
        ds.DoseSummationType = "PLAN"
        ds.DoseGridScaling = scaling
        ds.ImagePositionPatient = [float(x0 + x_lo * sx), float(y0 + y_lo * sy), float(z0)]
        ds.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
        ds.PixelSpacing = [float(sy * step), float(sx * step)]
        ds.SliceThickness = float(sz)
        ds.GridFrameOffsetVector = [float(k * sz) for k in range(nz)]
        ds.NumberOfFrames = nz
        ds.FrameIncrementPointer = (0x3004, 0x000C)
        ds.Rows, ds.Columns = d.shape[1], d.shape[2]
        ds.SamplesPerPixel = 1
        ds.PhotometricInterpretation = "MONOCHROME2"
        ds.BitsAllocated = 32
        ds.BitsStored = 32
        ds.HighBit = 31
        ds.PixelRepresentation = 0
        ds.PixelData = np.round(d / scaling).astype(np.uint32).tobytes()
        if plan_ref is not None:
            rp = Dataset()
            rp.ReferencedSOPClassUID, rp.ReferencedSOPInstanceUID = plan_ref
            ds.ReferencedRTPlanSequence = Sequence([rp])
        p = os.path.join(outdir, "RTDOSE.dcm")
        _save(ds, p)
        paths["RTDOSE"] = p
    return paths


def _img_ref(sop_class, sop_uid):
    from pydicom.dataset import Dataset

    r = Dataset()
    r.ReferencedSOPClassUID = sop_class
    r.ReferencedSOPInstanceUID = sop_uid
    return r
