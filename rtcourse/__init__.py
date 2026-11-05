"""rtcourse — small helper library for the course "AI w radioterapii".

Everything here is educational code: simple, readable and NOT intended for
clinical use. Modules:

- phantom   : synthetic thorax phantom + writer for DICOM CT / RTSTRUCT / RTDOSE / RTPLAN
- dicom_io  : reading DICOM-RT (CT series, contours -> masks, dose resampling)
- dose      : toy "beam" dose model (NOT a treatment planning system)
- metrics   : Dice, HD95, surface Dice, DVH, dose metrics, constraint checks
- autoseg   : TotalSegmentator wrapper + simulated "AI" errors for fallback mode
- data      : get a case: real course pack -> download -> synthetic fallback
- viz       : plotting helpers
"""

__version__ = "0.1.0"

from . import metrics, dose, phantom  # noqa: F401
