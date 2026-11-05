# AI w radioterapii — materiały do kursu

Kurs praktyczny (30 h, 10 bloków po 3 h) dla studentów studiów II stopnia z elektroradiologii.
Robimy na zajęciach rzeczy, które spotkacie w zakładzie radioterapii: otwieramy plan leczenia (DICOM-RT),
oceniamy autosegmentację, sprawdzamy, jak błąd konturu zmienia dawkę, i uczymy się odbierać i kontrolować
narzędzia AI. **Nie trzeba umieć programować.** Notatniki uruchamiacie w przeglądarce (Google Colab),
a zadania polegają na zmianie parametrów i interpretacji wyników. Dla chętnych są trudniejsze zadania
programistyczne.

> ⚠️ Materiały są wyłącznie edukacyjne. Kod, modele i dawki z tego repozytorium **nie służą do użytku klinicznego**.
> Używamy tylko danych publicznych (TCIA) i syntetycznych. Nie ma tu żadnych danych pacjentów.

## Mapa kursu

| Blok | Temat | Forma | Materiały |
|---|---|---|---|
| 0 | Jak korzystać z Google Colab (15 min, na start) | notatnik | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/bartektomasik/ai-rt-course/blob/main/notebooks/00_jak_korzystac_z_colaba.ipynb) [`00_jak_korzystac_z_colaba.ipynb`](notebooks/00_jak_korzystac_z_colaba.ipynb) |
| 1 | DICOM w radioterapii: CT, RTSTRUCT, RTPLAN, RTDOSE | notatnik | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/bartektomasik/ai-rt-course/blob/main/notebooks/01_dicom_rt.ipynb) [`01_dicom_rt.ipynb`](notebooks/01_dicom_rt.ipynb) |
| 2 | Jak „widzi” model: klasyfikator, przeuczenie, wyciek danych | notatnik | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/bartektomasik/ai-rt-course/blob/main/notebooks/02_jak_widzi_model.ipynb) [`02_jak_widzi_model.ipynb`](notebooks/02_jak_widzi_model.ipynb) |
| 3 | Autosegmentacja: TotalSegmentator vs kontur ręczny (Dice, HD95, surface Dice) | notatnik | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/bartektomasik/ai-rt-course/blob/main/notebooks/03_autosegmentacja.ipynb) [`03_autosegmentacja.ipynb`](notebooks/03_autosegmentacja.ipynb) |
| 4 | Kontur a dawka: DVH i limity dawek | notatnik | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/bartektomasik/ai-rt-course/blob/main/notebooks/04_kontur_a_dawka.ipynb) [`04_kontur_a_dawka.ipynb`](notebooks/04_kontur_a_dawka.ipynb) |
| 4b | Frakcjonowanie: BED i EQD2 (hipofrakcjonacja, przeliczanie limitów, przerwy, reirradiacja) | notatnik | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/bartektomasik/ai-rt-course/blob/main/notebooks/04b_eqd2_bed.ipynb) [`04b_eqd2_bed.ipynb`](notebooks/04b_eqd2_bed.ipynb) |
| 5 | Synthetic CT, CBCT i radioterapia adaptacyjna | warsztat | [karta ćwiczeń](worksheets/05_sct_cbct_art.md) |
| 6 | Automatyczne planowanie i predykcja dawki (KBP, OVH) | notatnik | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/bartektomasik/ai-rt-course/blob/main/notebooks/06_kbp_predykcja_dawki.ipynb) [`06_kbp_predykcja_dawki.ipynb`](notebooks/06_kbp_predykcja_dawki.ipynb) |
| 7 | Wdrożenie i QA modeli AI: odbiór, kryteria akceptacji, monitorowanie dryfu | notatnik + praca w grupach | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/bartektomasik/ai-rt-course/blob/main/notebooks/07_monitorowanie_qa.ipynb) [`07_monitorowanie_qa.ipynb`](notebooks/07_monitorowanie_qa.ipynb) |
| 8 | LLM w codziennej pracy: halucynacje, RODO, ocena błędów | warsztat | [karta ćwiczeń](worksheets/08_llm.md) |
| 9 | Regulacje (MDR, AI Act) i krytyczna ocena publikacji (TRIPOD+AI, CLAIM) | warsztat | [karta ćwiczeń](worksheets/09_regulacje_publikacje.md) |
| 10 | Prezentacje projektów | prezentacje | [zasady](worksheets/10_prezentacje.md) |

Bloki są niezależne — kolejność można zmieniać. Blok 0 warto zrobić na początku pierwszych zajęć; blok 4b można połączyć z blokiem 4 albo poprowadzić jako osobne 3 h. Projekt zaliczeniowy: [`projects/`](projects/README.md)
(4 karty projektów z rubryką oceny + opcjonalne [wyzwanie z rankingiem](projects/challenge/README.md)).

## Jak zacząć (student)

1. Potrzebujesz **laptopa z przeglądarką** i **konta Google**.
2. Kliknij przycisk **Open in Colab** przy wybranym bloku. Zacznij od **bloku 0** (15 min) — pokazuje, jak pracować w Colab.
3. W Colab: *Plik → Zapisz kopię na Dysku* (żeby zachować swoje zmiany).
4. Uruchamiaj komórki po kolei: **Shift+Enter**. Pierwsza komórka sama instaluje to, co potrzebne.
5. Jeśli coś nie działa (brak internetu, brak danych, brak GPU) — wpisz w pierwszej komórce `MODE = "synthetic"`.
   To **tryb awaryjny**: notatnik działa na syntetycznym fantomie generowanym w kodzie, bez pobierania czegokolwiek.

**GPU** przydaje się tylko w bloku 3 (TotalSegmentator na żywo): *Środowisko wykonawcze → Zmień typ środowiska → T4 GPU*.
Bez GPU notatnik użyje wyników przygotowanych wcześniej.

### Alternatywa: Kaggle Notebooks
1. Załóż konto na kaggle.com i zweryfikuj numer telefonu (potrzebne do włączenia internetu w notatniku).
2. *Create → New Notebook → File → Import Notebook* → wklej link do pliku `.ipynb` z GitHuba.
3. W panelu po prawej: *Settings → Internet: On* (opcjonalnie *Accelerator: GPU T4*).
4. Pakiet danych kursu można dodać jako „Dataset” (*Add Input*); notatniki szukają go w `/kaggle/input/ai-rt-course-pack/`.

### Lokalnie (dla chętnych)
```bash
git clone https://github.com/bartektomasik/ai-rt-course && cd ai-rt-course
pip install -r requirements.txt jupyterlab
jupyter lab notebooks/
```

## Dane

- **Zajęcia:** mały pakiet danych (`course_pack.zip`, kilka–kilkanaście przypadków) przygotowany z kolekcji
  **TCIA LCTSC** (Lung CT Segmentation Challenge 2017; CT klatki piersiowej + kontury płuc, serca, przełyku i rdzenia).
  Szczegóły, licencja i wymagane cytowania: [`data/README.md`](data/README.md).
- **Tryb awaryjny i testy:** syntetyczny fantom DICOM (CT + RTSTRUCT + RTPLAN + RTDOSE) generowany w kodzie
  ([`rtcourse/phantom.py`](rtcourse/phantom.py)).
- **Dawka** w notatnikach jest liczona prostym modelem edukacyjnym ([`rtcourse/dose.py`](rtcourse/dose.py)), a guz w danych LCTSC jest **wirtualny**.

## Struktura repozytorium

```
notebooks/          notatniki .ipynb (generowane z notebooks/src/*.py — edytuj źródła .py)
worksheets/         karty ćwiczeń warsztatowych (bloki 5, 8, 9, 10)
projects/           karty projektów zaliczeniowych, rubryka, wyzwanie z rankingiem
rtcourse/           mała biblioteka pomocnicza (DICOM-RT, metryki, fantom, model dawki)
data/               opis zbiorów danych + skrypt przygotowujący pakiet zajęciowy
docs/               sylabus, konspekt kursu, formularz „Chcesz robić badania z nami?”
scripts/            budowanie/uruchamianie notatników, wersja dla studentów
tests/              testy (uruchamiane w CI)
```

## Dla rozwijających materiały

```bash
pip install -r requirements-dev.txt
python scripts/build_notebooks.py                      # notebooks/src/*.py -> notebooks/*.ipynb
RTCOURSE_MODE=synthetic python scripts/run_notebooks.py # wykonaj wszystkie notatniki (jak w CI)
python -m pytest                                        # testy jednostkowe
```

CI (GitHub Actions) przy każdym pushu: testy, zgodność `.ipynb` ze źródłami, wykonanie wszystkich notatników
w trybie syntetycznym, test potoku pakietu danych i oceny wyzwania, budowa wersji dla studentów.


## Powiązane repozytoria

Wszystkie na koncie [BartekTomasik](https://github.com/BartekTomasik). Ta sama zasada wszędzie: tylko dane syntetyczne lub publiczne, prawdziwe dane wyłącznie lokalnie.

| Repozytorium | Do czego |
|---|---|
| [rwd-redcap-kit](https://github.com/BartekTomasik/rwd-redcap-kit) | budowa wieloośrodkowego badania RWD w REDCap: `study.yml` → słownik danych, DAG, reguły QC, raporty dla ośrodków, eksport do analizy |
| [redcap-ecrf-validator](https://github.com/BartekTomasik/redcap-ecrf-validator) | walidacja eCRF przed startem badania: lint projektu, przypadki testowe, testy przez API, dokumentacja walidacji |
| [clinical-stats-template](https://github.com/BartekTomasik/clinical-stats-template) | analiza kohorty: przeżycie, porównania leczenia (Cox, IPTW, krzywe skorygowane, zmienna zależna od czasu), presety projektów |
| [rwd-prognostic-xai](https://github.com/BartekTomasik/rwd-prognostic-xai) | modele prognostyczne i wyjaśnialne AI (SHAP w czasie) dla dużych zbiorów RWD – predykcja, nie przyczynowość |
| [rt-toolkit](https://github.com/BartekTomasik/rt-toolkit) | dozymetria w radioterapii: DICOM RT, DVH, limity dawek, EQD2/BED, NTCP, kohorty CSV |
| **ai-rt-course** (to repozytorium) | kurs „AI w radioterapii” (notatniki Colab, karty ćwiczeń, projekty) |

Przepływ w badaniach RWD: `rwd-redcap-kit` (projekt w REDCap) → `redcap-ecrf-validator` (walidacja eCRF przed zbieraniem danych) → eksport → `clinical-stats-template` (porównania, przeżycie) lub `rwd-prognostic-xai` (rokowanie). W radioterapii: `rt-toolkit` (obliczenia) → `ai-rt-course` (dydaktyka, uproszczona kopia obliczeń); zmienne dawkowe z `rt-toolkit` można analizować w `clinical-stats-template`.

## Licencja i cytowanie

Kod: licencja MIT ([`LICENSE`](LICENSE)). Materiały dydaktyczne (teksty notatników, karty ćwiczeń, projekty, dokumentacja): CC BY 4.0 ([`LICENSE-materials.md`](LICENSE-materials.md)).
Dane zewnętrzne mają własne licencje — zobacz [`data/README.md`](data/README.md).

Autor kursu: [imię i nazwisko — uzupełnić], Gdański Uniwersytet Medyczny.
