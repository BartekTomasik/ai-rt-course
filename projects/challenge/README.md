# Wyzwanie: „Pobij bazowy Dice” (opcjonalne, ranking)

Dla osób, które chcą programować. Zadanie: dla **odłożonych przypadków** z pakietu kursu (`course_pack/challenge/images/`,
CT bez konturów) przygotujcie maski płuc (L/P), serca, przełyku i rdzenia kręgowego — **lepsze niż wynik bazowy**.

- **Wynik bazowy:** TotalSegmentator „z pudełka” (jeśli w pakiecie są maski `challenge/totalseg/`),
  w przeciwnym razie proste progowanie HU (tylko płuca). Generuje go `baseline.py`.
- **Miara rankingu:** średni Dice ze wszystkich struktur i przypadków (brak struktury = 0). Pomocniczo: średni HD95.
- **Dozwolone:** postprocessing masek bazowych, łączenie metod, własne modele, inne otwarte narzędzia (opiszcie je).
  **Niedozwolone:** ręczne konturowanie przypadków testowych, pobieranie etykiet tych przypadków z TCIA (to też LCTSC!).
  Fair play — pomysł i kod są ważniejsze niż wynik.

## Format zgłoszenia
Folder z plikami `<case_id>.npz` — po jednym na przypadek, z maskami bool o kształcie CT `(z, y, x)`
nazwanymi `Lung_L, Lung_R, Heart, Esophagus, SpinalCord`:

```python
import numpy as np
from rtcourse.case import Case
from rtcourse import autoseg
case = Case.load_npz("course_pack/challenge/images/LCTSC-....npz")
masks = {"Lung_L": ..., "Lung_R": ..., "Heart": ..., "Esophagus": ..., "SpinalCord": ...}  # bool, case.ct.shape
autoseg.save_masks(masks, f"moj_zespol/{case.case_id}.npz")       # albo np.savez_compressed(..., **masks)
```

Sprawdzenie formatu (bez etykiet — możecie to zrobić sami):
```bash
python projects/challenge/baseline.py --pack course_pack --out submissions/baseline
python projects/challenge/evaluate.py --submission moj_zespol --images course_pack/challenge/images --check-only
```

Zgłoszenie: spakowany folder + krótki opis metody (½ strony) + kod. Prowadzący liczy wynik:
```bash
python projects/challenge/evaluate.py --submission moj_zespol --ground-truth instructor_private/challenge_gt \
    --images course_pack/challenge/images --team "Zespół A" --leaderboard leaderboard.csv
```
Punkty bonusowe: pobicie bazy (+3), miejsce 1–3 (+5/+4/+3), najlepszy opis metody (+3). Max bonus w kursie: 10 pkt.

## Pomysły na start
Największa spójna składowa i wypełnianie dziur; korekta konwencji (np. rdzeń vs kanał kręgowy — dylatacja/erozja);
wygładzanie między przekrojami; ograniczenie przełyku do okolicy przed kręgosłupem; uczenie progów na przypadkach z `cases/`.
