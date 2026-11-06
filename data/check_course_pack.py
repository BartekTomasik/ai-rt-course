#!/usr/bin/env python
"""Check the course pack BEFORE sharing it (Zenodo / Google Drive / pendrive).

Usage:
    python data/check_course_pack.py course_pack            # folder
    python data/check_course_pack.py course_pack.zip        # or the zip that will be shared

Fails (exit code 1) when the pack would leak the challenge ground truth or lacks licence information.
Checks:
  1. MANIFEST.json and LICENSE_AND_CITATION.md exist; the licence and data citation are filled in.
  2. No instructor files: nothing named challenge_gt / instructor_private / solutions / quiz key.
  3. Challenge images carry no labels: challenge/images/*.npz contain only the BODY structure.
  4. Challenge cases do not appear among the training cases (cases/, dicom/, totalseg/).
  5. Files listed in MANIFEST.json exist.
Prints the size and, for a zip, the SHA-256 to put next to the download link.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import sys
import tempfile
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FORBIDDEN = ("challenge_gt", "instructor_private", "instructor/", "solutions", "quiz_key", "answer_key")


def check(pack: pathlib.Path) -> list[str]:
    from rtcourse.case import Case

    errors = []
    files = [p for p in pack.rglob("*") if p.is_file()]
    rel = [p.relative_to(pack).as_posix() for p in files]
    for r in rel:
        if any(f in r.lower() for f in FORBIDDEN):
            errors.append(f"instructor file in the pack: {r}")
    man_p, lic_p = pack / "MANIFEST.json", pack / "LICENSE_AND_CITATION.md"
    if not man_p.exists():
        errors.append("MANIFEST.json is missing")
        return errors
    if not lic_p.exists():
        errors.append("LICENSE_AND_CITATION.md is missing")
    man = json.loads(man_p.read_text(encoding="utf-8"))
    src = man.get("source", {})
    if not src.get("license"):
        errors.append("MANIFEST.json: source.license is empty")
    if src.get("collection") != "synthetic" and src.get("data_citation", "-") in ("", "-"):
        errors.append("MANIFEST.json: data citation missing for a public data set")
    train, held = set(man.get("cases", [])), set(man.get("challenge_cases", []))
    if train & held:
        errors.append(f"cases both in training and challenge: {sorted(train & held)}")
    for c in train:
        if not (pack / "cases" / f"{c}.npz").exists():
            errors.append(f"listed case missing: cases/{c}.npz")
    for c in held:
        img = pack / "challenge" / "images" / f"{c}.npz"
        if not img.exists():
            errors.append(f"listed challenge case missing: {img.relative_to(pack).as_posix()}")
            continue
        extra = set(Case.load_npz(img).structures) - {"BODY"}
        if extra:
            errors.append(f"challenge image {c} contains labels: {sorted(extra)}")
        for d in ("cases", "totalseg", "dicom"):
            if (pack / d / f"{c}.npz").exists() or (pack / d / c).exists():
                errors.append(f"challenge case {c} also present in {d}/")
    return errors


def main(argv):
    if len(argv) != 1:
        sys.exit(__doc__)
    target = pathlib.Path(argv[0])
    tmp = None
    try:
        if target.suffix == ".zip":
            tmp = pathlib.Path(tempfile.mkdtemp())
            with zipfile.ZipFile(target) as z:
                z.extractall(tmp)
            subdirs = [p for p in tmp.iterdir() if p.is_dir()]
            pack = subdirs[0] if len(subdirs) == 1 and not (tmp / "MANIFEST.json").exists() else tmp
        else:
            pack = target
        errors = check(pack)
        size = sum(p.stat().st_size for p in pack.rglob("*") if p.is_file()) / 1e6
        print(f"Pakiet: {target} ({size:.1f} MB po rozpakowaniu)")
        if target.suffix == ".zip":
            h = hashlib.sha256(target.read_bytes()).hexdigest()
            print(f"SHA-256: {h}  (wpisz obok linku do pobrania)")
        if errors:
            print("BŁĘDY - NIE udostępniaj pakietu:")
            for e in errors:
                print("  -", e)
            sys.exit(1)
        print("OK - pakiet można udostępnić (sprawdź jeszcze licencję na stronie kolekcji TCIA).")
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv[1:])
