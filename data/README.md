# Dane w kursie

Używamy **wyłącznie** danych publicznych z otwartą licencją albo danych syntetycznych. Żadnych danych pacjentów
z zakładu — także na projektach zaliczeniowych.

## 1. Główny zbiór: TCIA LCTSC (Lung CT Segmentation Challenge 2017)

| | |
|---|---|
| Zawartość | 60 pacjentów, CT klatki piersiowej do planowania RT + RTSTRUCT: `Lung_L`, `Lung_R`, `Heart`, `Esophagus`, `SpinalCord` (konturowane wg wytycznych RTOG 1106) |
| Strona | https://www.cancerimagingarchive.net/collection/lctsc/ |
| DOI danych | https://doi.org/10.7937/K9/TCIA.2017.3R3FVZ08 |
| Licencja | **CC BY 3.0** (Creative Commons Attribution 3.0 Unported) — tak podaje strona TCIA/wiki kolekcji; ⚠️ **przed kursem sprawdź na stronie kolekcji**, czy licencja się nie zmieniła (TCIA przenosi część kolekcji na CC BY 4.0) |
| Dlaczego ten zbiór | kontury OAR zrobione do RT, mały rozmiar, standardowe nazwy struktur, używany jako benchmark autosegmentacji |
| Czego nie ma | planu (RTPLAN) i dawki (RTDOSE), konturu guza → w notatnikach dodajemy **wirtualny guz** i liczymy **dawkę modelem edukacyjnym** |

**Wymagane cytowania** (w każdej prezentacji/pracy z użyciem danych):

1. Yang J, Sharp G, Veeraraghavan H, van Elmpt W, Dekker A, Lustberg T, Gooding M. *Data from Lung CT Segmentation
   Challenge (LCTSC) (Version 3)* [Data set]. The Cancer Imaging Archive; 2017. https://doi.org/10.7937/K9/TCIA.2017.3R3FVZ08
2. Yang J, Veeraraghavan H, Armato SG 3rd, et al. Autosegmentation for thoracic radiation treatment planning:
   A grand challenge at AAPM 2017. *Med Phys.* 2018;45(10):4568–4581. https://doi.org/10.1002/mp.13141
3. Clark K, Vendt B, Smith K, et al. The Cancer Imaging Archive (TCIA): Maintaining and Operating a Public
   Information Repository. *J Digit Imaging.* 2013;26(6):1045–1057. https://doi.org/10.1007/s10278-013-9622-7

Obowiązują też [zasady korzystania z danych TCIA](https://www.cancerimagingarchive.net/data-usage-policies-and-restrictions/)
(m.in. zakaz prób reidentyfikacji pacjentów).

## 2. Narzędzie: TotalSegmentator

Wasserthal J, Breit HC, Meyer MT, et al. TotalSegmentator: Robust Segmentation of 104 Anatomic Structures in CT Images.
*Radiol Artif Intell.* 2023;5(5):e230024. https://doi.org/10.1148/ryai.230024 — kod: https://github.com/wasserth/TotalSegmentator
(licencja Apache 2.0 dla kodu i podstawowego zadania `total`; niektóre dodatkowe modele mają licencję niekomercyjną — sprawdź przed użyciem).

## 3. Dane syntetyczne

`rtcourse/phantom.py` generuje fantom klatki piersiowej (ciało, płuca, serce, kręgosłup, rdzeń, przełyk, guz + PTV)
i zapisuje go jako poprawne pliki DICOM (CT, RTSTRUCT, RTPLAN, RTDOSE). Używany w CI, w trybie awaryjnym i w blokach 2 i 6.
Dane syntetyczne można swobodnie udostępniać.

## 4. Zbiory opcjonalne (do projektów chętnych — zweryfikuj licencję przed użyciem)

- **NSCLC-Radiomics** (TCIA; Aerts i wsp. 2014) — CT + kontury GTV i OAR, ~420 pacjentów, CC BY-NC 3.0 → https://doi.org/10.7937/K9/TCIA.2015.PF0M9REI
- **OpenKBP** (AAPM 2020, predykcja dawki w H&N; Babier i wsp., *Med Phys* 2021) — dawki + struktury → https://github.com/ababier/open-kbp
- **SynthRAD2023** (synthetic CT z MR/CBCT; Thummerer i wsp., *Med Phys* 2023) — do bloku 5 → https://synthrad2023.grand-challenge.org/

## 5. Pakiet zajęciowy (`course_pack.zip`)

Salowe Wi-Fi nie udźwignie pobierania całych kolekcji, więc prowadzący **raz** przygotowuje mały pakiet:

```bash
# w Google Colab (z GPU, jeśli mają być policzone maski TotalSegmentator)
!git clone https://github.com/bartektomasik/ai-rt-course && cd ai-rt-course
!pip install -q pydicom TotalSegmentator
!python data/prepare_course_pack.py --source lctsc --n-cases 10 --n-challenge 4 --totalseg
```

Wynik: `course_pack/` + `course_pack.zip` (do udostępnienia: Google Drive / Zenodo) i `instructor_private/challenge_gt/`
(**etykiety wyzwania — nie udostępniać**). Po wgraniu pakietu wpisz link do pliku w `COURSE_PACK_URL`
w `rtcourse/data.py` (albo ustaw zmienną środowiskową `RTCOURSE_PACK_URL`).

Zawartość pakietu: `cases/*.npz` (CT przeskalowane 2× w płaszczyźnie poprzecznej, struktury, wirtualny guz, dawka modelowa),
`dicom/` (oryginalne DICOM 2 przypadków do bloku 1), `totalseg/` (gotowe maski AI na wypadek braku GPU),
`challenge/images/` (CT bez etykiet), `rtcourse/` (kopia kodu), `MANIFEST.json`, `LICENSE_AND_CITATION.md`.

> Na Zenodo pakiet z danymi pochodnymi LCTSC można opublikować pod tą samą licencją (CC BY) z podaniem źródła
> i opisem modyfikacji (plik `LICENSE_AND_CITATION.md` jest tworzony automatycznie).

Test bez internetu: `python data/prepare_course_pack.py --source synthetic --n-cases 3 --n-challenge 2`.
