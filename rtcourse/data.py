"""Getting data for the notebooks, with a fallback chain.

MODE (env RTCOURSE_MODE or argument):
- "auto"      : course pack on disk -> download course pack -> synthetic phantom
- "real"      : course pack required (error if missing)
- "synthetic" : always the synthetic phantom (used in CI and as emergency mode)

Course pack location (first that exists): env RTCOURSE_DATA, ./course_pack,
../course_pack, /content/course_pack, /content/drive/MyDrive/ai-rt-course/course_pack,
/kaggle/input/ai-rt-course-pack/course_pack.

Download URL: env RTCOURSE_PACK_URL or COURSE_PACK_URL below (set it after
uploading the pack produced by data/prepare_course_pack.py, e.g. to Zenodo).
"""
from __future__ import annotations

import glob
import json
import os
import zipfile

import numpy as np

from .case import Case
from .phantom import make_phantom, write_dicom_rt

# TODO(prowadzący): po wgraniu pakietu na Zenodo / dysk wpisz tu bezpośredni link do pliku .zip
COURSE_PACK_URL = ""

CANDIDATE_DIRS = [
    "course_pack",
    os.path.join("..", "course_pack"),
    "/content/course_pack",
    "/content/drive/MyDrive/ai-rt-course/course_pack",
    "/kaggle/input/ai-rt-course-pack/course_pack",
    "/kaggle/input/ai-rt-course-pack",
]


def get_mode(mode: str | None = None) -> str:
    mode = (mode or os.environ.get("RTCOURSE_MODE", "auto")).lower()
    if mode not in {"auto", "real", "synthetic"}:
        raise ValueError("MODE musi być 'auto', 'real' albo 'synthetic'")
    return mode


def find_course_pack() -> str | None:
    cands = ([os.environ["RTCOURSE_DATA"]] if os.environ.get("RTCOURSE_DATA") else []) + CANDIDATE_DIRS
    for d in cands:
        if os.path.isfile(os.path.join(d, "MANIFEST.json")):
            return os.path.abspath(d)
    return None


def download_course_pack(url: str | None = None, dest: str = "course_pack", timeout: int = 60) -> str | None:
    """Download and unzip the course pack. Returns its folder or None on failure."""
    import urllib.request

    url = url or os.environ.get("RTCOURSE_PACK_URL") or COURSE_PACK_URL
    if not url:
        return None
    zpath = dest.rstrip("/") + ".zip"
    try:
        print(f"Pobieram pakiet danych: {url}")
        with urllib.request.urlopen(url, timeout=timeout) as r, open(zpath, "wb") as f:
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
        with zipfile.ZipFile(zpath) as z:
            z.extractall(os.path.dirname(os.path.abspath(dest)) or ".")
        os.remove(zpath)
    except Exception as e:
        print(f"[TRYB AWARYJNY] Nie udało się pobrać pakietu ({type(e).__name__}: {e}).")
        return None
    return find_course_pack()


def get_course_pack(mode: str | None = None) -> str | None:
    mode = get_mode(mode)
    if mode == "synthetic":
        return None
    d = find_course_pack() or download_course_pack()
    if d is None and mode == "real":
        raise FileNotFoundError("Nie znaleziono pakietu danych (course_pack). Ustaw RTCOURSE_DATA albo MODE='auto'.")
    return d


def manifest(pack_dir: str) -> dict:
    with open(os.path.join(pack_dir, "MANIFEST.json"), encoding="utf-8") as f:
        return json.load(f)


def list_cases(mode: str | None = None) -> list:
    d = get_course_pack(mode)
    if d is None:
        return [f"PHANTOM{i:03d}" for i in range(5)]
    return sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(d, "cases", "*.npz")))


def load_case(index: int = 0, mode: str | None = None, verbose: bool = True) -> Case:
    """Load case number `index` from the course pack, or a synthetic phantom."""
    d = get_course_pack(mode)
    if d is not None:
        files = sorted(glob.glob(os.path.join(d, "cases", "*.npz")))
        if files:
            c = Case.load_npz(files[index % len(files)])
            if verbose:
                print(f"Dane rzeczywiste z pakietu kursu: {c.case_id} ({c.source})")
            return c
    if verbose:
        msg = "tryb syntetyczny" if get_mode(mode) == "synthetic" else "TRYB AWARYJNY: brak pakietu danych"
        print(f"[{msg}] Używam syntetycznego fantomu klatki piersiowej (seed={index}).")
    return make_phantom(seed=index, variability=0.0 if index == 0 else 1.0)


def get_dicom_folder(mode: str | None = None, workdir: str = "rt_dicom_example") -> tuple:
    """Folder with one complete DICOM-RT case. Returns (folder, source_description)."""
    d = get_course_pack(mode)
    if d is not None:
        subs = sorted(glob.glob(os.path.join(d, "dicom", "*")))
        if subs:
            return subs[0], f"TCIA (pakiet kursu): {os.path.basename(subs[0])}"
    if not os.path.isfile(os.path.join(workdir, "RTSTRUCT.dcm")):
        print("Generuję syntetyczny fantom DICOM (CT + RTSTRUCT + RTPLAN + RTDOSE)...")
        write_dicom_rt(make_phantom(seed=0, variability=0.0), workdir)
    return workdir, "syntetyczny fantom (rtcourse.phantom)"


def add_derived_structures(case: Case) -> Case:
    """Add 'Lungs' and 'Lungs-GTV' if lungs are present."""
    s = case.structures
    if "Lung_L" in s and "Lung_R" in s:
        s["Lungs"] = s["Lung_L"] | s["Lung_R"]
        if "GTV" in s:
            s["Lungs-GTV"] = s["Lungs"] & ~s["GTV"]
        else:
            s["Lungs-GTV"] = s["Lungs"]
    return case


def place_virtual_tumor(case: Case, radius_mm: float = 15.0, margin_mm: float = 8.0, side: str = "Lung_R") -> Case:
    """Add a spherical virtual GTV deep inside a lung and a PTV (for public data without targets)."""
    from scipy import ndimage

    lung = case.structures[side]
    dist = ndimage.distance_transform_edt(lung, sampling=case.spacing)
    c = np.unravel_index(np.argmax(dist), dist.shape)
    zz, yy, xx = np.indices(lung.shape, sparse=True)
    sz, sy, sx = case.spacing
    r = np.sqrt(((zz - c[0]) * sz) ** 2 + ((yy - c[1]) * sy) ** 2 + ((xx - c[2]) * sx) ** 2)
    gtv = r <= radius_mm
    body = case.structures.get("BODY", np.ones_like(gtv))
    ptv = (ndimage.distance_transform_edt(~gtv, sampling=case.spacing) <= margin_mm) & body
    case.structures["GTV"] = gtv
    case.structures["PTV"] = ptv
    case.meta["virtual_tumor"] = True
    return case
