#!/usr/bin/env python
"""Prepare the small classroom data pack ("course_pack") — run ONCE by the instructor.

Classroom Wi-Fi cannot handle whole TCIA collections, so we download a few
cases once, preprocess them and share one .zip (Google Drive / Zenodo).

Usage (recommended in Google Colab with GPU, ~20–40 min):
    !git clone https://github.com/bartektomasik/ai-rt-course && cd ai-rt-course
    !pip install -q pydicom TotalSegmentator
    !python data/prepare_course_pack.py --source lctsc --n-cases 10 --n-challenge 4 --totalseg

Offline test (no network; used in CI):
    python data/prepare_course_pack.py --source synthetic --n-cases 3 --n-challenge 2

Output:
    course_pack/                       -> share with students (zip: course_pack.zip)
        MANIFEST.json, LICENSE_AND_CITATION.md
        rtcourse/                      (copy of the helper code — works even while the repo is private)
        dicom/<case>/                  (original DICOM CT + RTSTRUCT, first --n-dicom cases)
        cases/<case>.npz               (2x downsampled CT + structures + virtual tumour + model dose)
        totalseg/<case>.npz            (TotalSegmentator masks, if --totalseg)
        challenge/images/<case>.npz    (held-out CT without labels)
        challenge/totalseg/<case>.npz  (baseline TotalSegmentator masks, if --totalseg)
    instructor_private/challenge_gt/   -> DO NOT SHARE (ground truth for the leaderboard)

NOTE: the TCIA download part could not be tested in the development
environment (network blocked) — test it in Colab before the course.
"""
from __future__ import annotations

import argparse
import datetime
import io
import json
import os
import pathlib
import shutil
import sys
import urllib.parse
import urllib.request
import zipfile

import numpy as np
from scipy import ndimage

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from rtcourse import autoseg, dicom_io  # noqa: E402
from rtcourse.case import Case  # noqa: E402
from rtcourse.data import place_virtual_tumor  # noqa: E402
from rtcourse.dose import compute_dose  # noqa: E402
from rtcourse.phantom import make_phantom  # noqa: E402

NBIA = "https://services.cancerimagingarchive.net/nbia-api/services/v1"

LCTSC_INFO = {
    "collection": "LCTSC",
    "title": "Lung CT Segmentation Challenge 2017 (LCTSC)",
    "license": "Creative Commons Attribution 3.0 Unported (CC BY 3.0) — SPRAWDŹ aktualną licencję na stronie kolekcji TCIA",
    "data_citation": "Yang J, Sharp G, Veeraraghavan H, van Elmpt W, Dekker A, Lustberg T, Gooding M. "
                     "Data from Lung CT Segmentation Challenge (LCTSC) (Version 3) [Data set]. "
                     "The Cancer Imaging Archive; 2017. https://doi.org/10.7937/K9/TCIA.2017.3R3FVZ08",
    "publication_citation": "Yang J, Veeraraghavan H, Armato SG 3rd, et al. Autosegmentation for thoracic radiation "
                            "treatment planning: A grand challenge at AAPM 2017. Med Phys. 2018;45(10):4568-4581. "
                            "https://doi.org/10.1002/mp.13141",
    "tcia_citation": "Clark K, Vendt B, Smith K, et al. The Cancer Imaging Archive (TCIA): Maintaining and Operating "
                     "a Public Information Repository. J Digit Imaging. 2013;26(6):1045-1057. https://doi.org/10.1007/s10278-013-9622-7",
}

NAME_ALIASES = {
    "lung_l": "Lung_L", "left lung": "Lung_L", "lung left": "Lung_L", "lungl": "Lung_L",
    "lung_r": "Lung_R", "right lung": "Lung_R", "lung right": "Lung_R", "lungr": "Lung_R",
    "heart": "Heart", "esophagus": "Esophagus", "oesophagus": "Esophagus",
    "spinalcord": "SpinalCord", "spinal_cord": "SpinalCord", "spinal cord": "SpinalCord", "cord": "SpinalCord",
}
OARS = ["Lung_L", "Lung_R", "Heart", "Esophagus", "SpinalCord"]


# ------------------------------------------------------------------ TCIA download
def _get_json(url):
    with urllib.request.urlopen(url, timeout=120) as r:
        return json.loads(r.read().decode())


def list_lctsc_series():
    url = f"{NBIA}/getSeries?" + urllib.parse.urlencode({"Collection": "LCTSC", "format": "json"})
    return _get_json(url)


def download_series(uid: str, dest: pathlib.Path):
    dest.mkdir(parents=True, exist_ok=True)
    url = f"{NBIA}/getImage?" + urllib.parse.urlencode({"SeriesInstanceUID": uid})
    with urllib.request.urlopen(url, timeout=600) as r:
        zipfile.ZipFile(io.BytesIO(r.read())).extractall(dest)


def fetch_lctsc(raw_dir: pathlib.Path, n: int) -> list:
    """Download CT + RTSTRUCT for the first n LCTSC patients. Returns patient folders."""
    try:
        series = list_lctsc_series()
    except Exception as e:
        sys.exit(f"Nie udało się połączyć z TCIA ({e}). Uruchom skrypt w Colab albo użyj tcia_utils.")
    by_patient = {}
    for s in series:
        by_patient.setdefault(s["PatientID"], []).append(s)
    patients = sorted(by_patient)[:n]
    out = []
    for pid in patients:
        pdir = raw_dir / pid
        if not (pdir / ".done").exists():
            for s in by_patient[pid]:
                if s.get("Modality") in ("CT", "RTSTRUCT"):
                    print(f"  pobieram {pid} {s['Modality']} ...", flush=True)
                    download_series(s["SeriesInstanceUID"], pdir / s["Modality"])
            (pdir / ".done").write_text("ok")
        out.append(pdir)
    return out


# ------------------------------------------------------------------ preprocessing
def normalise_names(structures: dict) -> dict:
    out = {}
    for k, v in structures.items():
        key = NAME_ALIASES.get(k.strip().lower().replace("-", "_"), None) or NAME_ALIASES.get(k.strip().lower())
        if key:
            out[key] = out.get(key, np.zeros_like(v)) | v
    return out


def body_mask(ct):
    m = ct > -400
    m = np.stack([ndimage.binary_fill_holes(s) for s in m])
    lab, n = ndimage.label(m)
    if n > 1:
        sizes = ndimage.sum(m, lab, range(1, n + 1))
        m = lab == (1 + int(np.argmax(sizes)))
    return m


def downsample_case(folder: pathlib.Path, case_id: str, factor: int = 2) -> Case:
    g = dicom_io.scan_folder(str(folder))
    ct, spacing, origin, _ = dicom_io.load_ct(g["CT"])
    nz, ny, nx = ct.shape
    ny2, nx2 = ny // factor, nx // factor
    ct2 = ct[:, : ny2 * factor, : nx2 * factor].reshape(nz, ny2, factor, nx2, factor).mean(axis=(2, 4))
    sz, sy, sx = spacing
    sp2 = (sz, sy * factor, sx * factor)
    or2 = (origin[0] + (factor - 1) * sx / 2, origin[1] + (factor - 1) * sy / 2, origin[2])
    raw = dicom_io.load_rtstruct(g["RTSTRUCT"][0], ct2.shape, sp2, or2)
    s = normalise_names(raw)
    missing = [o for o in OARS if o not in s]
    if missing:
        print(f"  UWAGA {case_id}: brak struktur {missing} (nazwy w pliku: {list(raw)})")
    s["BODY"] = body_mask(ct2)
    return Case(ct=ct2.astype(np.float32), spacing=sp2, origin=or2, structures=s, case_id=case_id, source="TCIA LCTSC")


def finish_case(case: Case) -> Case:
    """Add virtual tumour + PTV + model dose."""
    if "GTV" not in case.structures:
        place_virtual_tumor(case, radius_mm=15.0, margin_mm=8.0, side="Lung_R" if "Lung_R" in case.structures else "Lung_L")
    case.dose = compute_dose(case.structures["PTV"], case.spacing, body=case.structures.get("BODY"))
    return case


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", choices=["lctsc", "synthetic"], default="lctsc")
    ap.add_argument("--n-cases", type=int, default=10, help="przypadki zajęciowe")
    ap.add_argument("--n-challenge", type=int, default=4, help="przypadki odłożone do wyzwania (bez etykiet)")
    ap.add_argument("--n-dicom", type=int, default=2, help="ile przypadków dołączyć jako oryginalne DICOM")
    ap.add_argument("--totalseg", action="store_true", help="policz maski TotalSegmentator (zalecane GPU)")
    ap.add_argument("--out", default="course_pack")
    ap.add_argument("--private-out", default="instructor_private")
    ap.add_argument("--raw", default="raw_tcia", help="katalog na pobrane surowe dane")
    ap.add_argument("--no-zip", action="store_true")
    args = ap.parse_args()

    out = pathlib.Path(args.out)
    priv = pathlib.Path(args.private_out)
    if out.exists():
        shutil.rmtree(out)
    for d in ["cases", "totalseg", "dicom", "challenge/images", "challenge/totalseg"]:
        (out / d).mkdir(parents=True, exist_ok=True)
    (priv / "challenge_gt").mkdir(parents=True, exist_ok=True)

    total = args.n_cases + args.n_challenge
    cases = []
    if args.source == "lctsc":
        folders = fetch_lctsc(pathlib.Path(args.raw), total)
        for i, f in enumerate(folders):
            print(f"[{i + 1}/{len(folders)}] przetwarzam {f.name}", flush=True)
            cases.append((f, downsample_case(f, f.name)))
        info = LCTSC_INFO
    else:
        from rtcourse.phantom import write_dicom_rt

        for i in range(total):
            c = make_phantom(seed=100 + i, with_dose=False)
            c.case_id = f"SYNTH{i:03d}"
            f = pathlib.Path(args.raw) / c.case_id
            if i < args.n_dicom:
                write_dicom_rt(c, str(f), write_plan=False)
            # drop the phantom's own tumour to mimic public data without targets
            for k in ("GTV", "PTV"):
                c.structures.pop(k)
            cases.append((f, c))
        info = {"collection": "synthetic", "title": "Syntetyczne fantomy rtcourse", "license": "CC0 (dane wygenerowane)",
                "data_citation": "-", "publication_citation": "-", "tcia_citation": "-"}

    train, held = cases[: args.n_cases], cases[args.n_cases:]
    for i, (folder, c) in enumerate(train):
        finish_case(c)
        c.save_npz(out / "cases" / f"{c.case_id}.npz")
        if i < args.n_dicom and folder.exists():
            shutil.copytree(folder, out / "dicom" / c.case_id, ignore=shutil.ignore_patterns(".done"))
        if args.totalseg:
            print(f"  TotalSegmentator: {c.case_id}", flush=True)
            autoseg.save_masks(autoseg.run_totalsegmentator(c), out / "totalseg" / f"{c.case_id}.npz")
    for folder, c in held:
        gt = {k: v for k, v in c.structures.items() if k in OARS}
        autoseg.save_masks(gt, priv / "challenge_gt" / f"{c.case_id}.npz", spacing=c.spacing)
        img = Case(ct=c.ct, spacing=c.spacing, origin=c.origin, structures={"BODY": c.structures["BODY"]},
                   case_id=c.case_id, source=c.source)
        img.save_npz(out / "challenge" / "images" / f"{c.case_id}.npz")
        if args.totalseg:
            autoseg.save_masks(autoseg.run_totalsegmentator(c), out / "challenge" / "totalseg" / f"{c.case_id}.npz")

    shutil.copytree(ROOT / "rtcourse", out / "rtcourse", ignore=shutil.ignore_patterns("__pycache__"))
    manifest = {
        "created": datetime.date.today().isoformat(),
        "source": info,
        "cases": [c.case_id for _, c in train],
        "challenge_cases": [c.case_id for _, c in held],
        "dicom_cases": sorted(p.name for p in (out / "dicom").iterdir()),
        "totalseg": bool(args.totalseg),
        "notes": "CT przeskalowane 2x w płaszczyźnie poprzecznej. GTV/PTV są WIRTUALNE (sfera w płucu), "
                 "dawka policzona modelem edukacyjnym rtcourse.dose — nie są to dane kliniczne.",
    }
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "LICENSE_AND_CITATION.md").write_text(
        f"# Licencja i cytowanie\n\nZbiór: **{info['title']}**\n\nLicencja: {info['license']}\n\n"
        f"Wymagane cytowanie danych:\n> {info['data_citation']}\n\nPublikacja:\n> {info['publication_citation']}\n\n"
        f"TCIA:\n> {info['tcia_citation']}\n\nModyfikacje: przeskalowanie, wirtualny guz, dawka modelowa (rtcourse).\n",
        encoding="utf-8")
    if not args.no_zip:
        shutil.make_archive(str(out), "zip", root_dir=str(out.parent.resolve()), base_dir=out.name)
        print(f"Spakowano: {out}.zip ({os.path.getsize(str(out) + '.zip') / 1e6:.1f} MB)")
    print(f"Gotowe. Pakiet: {out}/  |  PRYWATNE etykiety wyzwania: {priv}/challenge_gt/ (nie udostępniaj!)")


if __name__ == "__main__":
    main()
