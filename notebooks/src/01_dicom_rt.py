# %% [markdown]
# # Blok 1. DICOM w radioterapii: CT, RTSTRUCT, RTPLAN, RTDOSE
#
# **Cel kliniczny.** Plan leczenia to nie jeden plik, tylko zestaw powiązanych obiektów DICOM:
# obrazy CT, kontury (RTSTRUCT), plan (RTPLAN) i rozkład dawki (RTDOSE). Gdy coś „nie pasuje”
# (kontur przesunięty względem obrazu, dawka z innego planu, zła wersja zestawu struktur),
# skutki kliniczne mogą być poważne. Po tych zajęciach umiesz otworzyć taki zestaw, sprawdzić
# jego spójność i pokazać kontury i dawkę na obrazie — to samo robi pod spodem każdy system
# planowania i każde narzędzie AI.
#
# **Czas:** ok. 2 h pracy z notatnikiem + dyskusja. **Programowanie nie jest wymagane** — uruchamiasz
# kolejne komórki (Shift+Enter) i zmieniasz zaznaczone parametry.
#
# ### Krótka teoria
# | Obiekt | Co zawiera | Kluczowe elementy |
# |---|---|---|
# | **CT** | jeden plik = jeden przekrój | `PixelData`, `RescaleSlope/Intercept` (→ HU), `ImagePositionPatient`, `PixelSpacing` |
# | **RTSTRUCT** | kontury jako wielokąty (punkty x, y, z w mm) | `StructureSetROISequence` (nazwy), `ROIContourSequence` (punkty) |
# | **RTPLAN** | „przepis”: wiązki, kąty, energie, liczba frakcji, dawka zadana | `BeamSequence`, `FractionGroupSequence`, `DoseReferenceSequence` |
# | **RTDOSE** | trójwymiarowa siatka dawki (zwykle grubsza niż CT) | `DoseGridScaling`, `GridFrameOffsetVector` |
#
# Wszystko łączą **identyfikatory UID**: `StudyInstanceUID`, `SeriesInstanceUID`, `SOPInstanceUID`
# i — najważniejszy dla RT — **`FrameOfReferenceUID`**, czyli wspólny układ współrzędnych.
# Współrzędne pacjenta w DICOM to układ **LPS**: oś x rośnie w stronę lewego boku pacjenta,
# y — w stronę pleców, z — w stronę głowy.

# %%
# INCLUDE: _setup.py

# %% [markdown]
# ## 1. Co jest w folderze z planem?
# W trybie `auto` używamy przypadku z pakietu kursu (TCIA), w trybie awaryjnym — syntetycznego
# fantomu wygenerowanego w kodzie (to też poprawne pliki DICOM!).

# %%
from rtcourse import dicom_io

folder, source = data.get_dicom_folder(MODE)
print("Źródło danych:", source)
files = dicom_io.scan_folder(folder)
pd.DataFrame({"modalność": list(files), "liczba plików": [len(v) for v in files.values()]})

# %% [markdown]
# ## 2. Nagłówek DICOM — „metryczka” pliku
# Poniżej najważniejsze pola pierwszego obrazu CT. Zwróć uwagę na `PixelSpacing`, `SliceThickness`
# i `ImagePositionPatient` — to one mówią, gdzie w przestrzeni leży każdy piksel.

# %%
print(dicom_io.describe(files["CT"][0]))

# %% [markdown]
# ### Sprawdzenie spójności: czy wszystkie obiekty są w tym samym układzie współrzędnych?

# %%
import pydicom

rows = []
for modality, paths in files.items():
    ds = pydicom.dcmread(paths[0], stop_before_pixels=True)
    for_uid = getattr(ds, "FrameOfReferenceUID", None)
    if for_uid is None and "ReferencedFrameOfReferenceSequence" in ds:
        for_uid = ds.ReferencedFrameOfReferenceSequence[0].FrameOfReferenceUID
    rows.append({"modalność": modality, "PatientID": ds.PatientID, "FrameOfReferenceUID": str(for_uid)[-24:]})
uid_table = pd.DataFrame(rows)
print("Wszystkie FrameOfReferenceUID zgodne:", uid_table["FrameOfReferenceUID"].nunique() == 1)
uid_table

# %% [markdown]
# ## 3. Obraz CT i jednostki Hounsfielda (HU)
# Wartości pikseli zamieniamy na HU: `HU = wartość × RescaleSlope + RescaleIntercept`.
# Powietrze ≈ −1000 HU, woda = 0 HU, tkanki miękkie 20–60 HU, kość 300–1500 HU.

# %%
ct, spacing, origin, _ = dicom_io.load_ct(files["CT"])
print(f"Wymiary CT (warstwy, wiersze, kolumny): {ct.shape}; voxel (z, y, x) = {spacing} mm")
print(f"Zakres HU: {ct.min():.0f} … {ct.max():.0f}")
plt.figure(figsize=(6, 3))
plt.hist(ct.ravel(), bins=200, range=(-1100, 1500), color="gray")
plt.yscale("log"); plt.xlabel("HU"); plt.ylabel("liczba vokseli"); plt.title("Histogram HU")
plt.show()

# %% [markdown]
# ### Okno wyświetlania
# **Zadanie 1 (zmień parametr).** Zmień `WINDOW` na `"lung"`, `"bone"` albo własną parę
# `(środek, szerokość)`, np. `(-500, 1000)`. Co lepiej widać w każdym oknie? Dlaczego w praktyce
# konturuje się płuca w innym oknie niż serce?

# %%
WINDOW = "mediastinum"  # "mediastinum" | "lung" | "bone" | (środek, szerokość)

from rtcourse.case import Case

rois = dicom_io.list_rois(files["RTSTRUCT"][0])
structures = dicom_io.load_rtstruct(files["RTSTRUCT"][0], ct.shape, spacing, origin)
case = Case(ct=ct, spacing=spacing, origin=origin, structures=structures, source=source)
fig, axs = plt.subplots(1, 2, figsize=(12, 6))
viz.show_slice(case, structures=[], window=WINDOW, ax=axs[0], title=f"CT, okno {WINDOW}")
viz.show_slice(case, window=WINDOW, ax=axs[1], title="CT + kontury z RTSTRUCT")
plt.show()

# %% [markdown]
# ## 4. RTSTRUCT: kontur to wielokąt, a nie „maska”
# W pliku zapisane są **punkty** (x, y, z w mm) na kolejnych przekrojach. Żeby policzyć objętość
# albo DVH, trzeba je zamienić na maskę vokseli (*rasteryzacja*). Różne programy robią to trochę
# inaczej — dlatego objętość tej samej struktury może się różnić między systemami o kilka procent.

# %%
print("Struktury w RTSTRUCT:", rois)
ds_struct = pydicom.dcmread(files["RTSTRUCT"][0])
ROI_TO_SHOW = rois[1] if len(rois) > 1 else rois[0]  # zmień na inną nazwę z listy
num = {r.ROIName: r.ROINumber for r in ds_struct.StructureSetROISequence}[ROI_TO_SHOW]
rc = [r for r in ds_struct.ROIContourSequence if r.ReferencedROINumber == num][0]
contours = list(rc.ContourSequence)
mid = contours[len(contours) // 2]
pts = np.asarray(mid.ContourData, float).reshape(-1, 3)
print(f"{ROI_TO_SHOW}: {len(contours)} konturów; przykładowy kontur ma {len(pts)} punktów na z = {pts[0, 2]:.1f} mm")
print("Pierwsze 3 punkty (x, y, z) [mm]:\n", pts[:3].round(1))
plt.figure(figsize=(4, 4))
plt.plot(np.append(pts[:, 0], pts[0, 0]), np.append(pts[:, 1], pts[0, 1]), "o-", ms=3)
plt.gca().invert_yaxis(); plt.axis("equal"); plt.title(f"Surowe punkty konturu: {ROI_TO_SHOW}")
plt.xlabel("x [mm]"); plt.ylabel("y [mm]")
plt.show()

# %%
vol_table = pd.DataFrame(
    {"objętość [cm³]": {n: round(metrics.volume_cc(m, spacing), 1) for n, m in structures.items()},
     "liczba przekrojów": {n: int(m.any(axis=(1, 2)).sum()) for n, m in structures.items()}}
)
vol_table

# %% [markdown]
# ## 5. RTPLAN: co i jak zaplanowano
# Zbiór LCTSC z TCIA zawiera tylko CT i kontury. Jeśli w folderze nie ma planu i dawki,
# do tej części używamy fantomu syntetycznego (komunikat poniżej).

# %%
if "RTPLAN" in files and "RTDOSE" in files:
    plan_folder, plan_files = folder, files
else:
    print("Brak RTPLAN/RTDOSE w danych rzeczywistych — używam fantomu syntetycznego dla tej części.")
    plan_folder, _ = data.get_dicom_folder("synthetic")
    plan_files = dicom_io.scan_folder(plan_folder)
plan = dicom_io.plan_summary(plan_files["RTPLAN"][0])
rx = plan["prescription_Gy"][0]
print(f"Plan: {plan['label']} | dawka zadana {rx} Gy w {plan['fractions']} frakcjach "
      f"= {rx / plan['fractions']:.2f} Gy/frakcję")
pd.DataFrame(plan["beams"])

# %% [markdown]
# ## 6. RTDOSE: siatka dawki jest inna niż siatka CT
# Systemy planowania liczą dawkę na grubszej siatce (np. 2,5–3 mm), często tylko w obrębie ciała.
# Żeby pokazać dawkę na CT, trzeba ją **przeinterpolować** na siatkę obrazu.

# %%
dose_raw, dose_grid = dicom_io.load_rtdose(plan_files["RTDOSE"][0])
pct = dicom_io.load_case_from_folder(plan_folder)
print(f"Siatka dawki: {dose_raw.shape}, krok x = {np.diff(dose_grid['x'][:2])[0]:.1f} mm")
print(f"Siatka CT:    {pct.ct.shape}, krok x = {pct.spacing[2]:.1f} mm")
print(f"Dawka maksymalna: {pct.dose.max():.1f} Gy ({100 * pct.dose.max() / rx:.0f}% dawki zadanej)")

# %% [markdown]
# **Zadanie 2 (zmień parametr).** `DOSE_MIN` to próg kolorowania dawki. Ustaw kolejno 5, 20, 57
# (= 95% z 60 Gy). Który obszar obejmuje izodoza 95%? Czy cały PTV? Gdzie trafia niska dawka?

# %%
DOSE_MIN = 20.0  # Gy
viz.show_three_views(pct, dose=pct.dose, structures=["PTV", "GTV", "Heart", "SpinalCord", "Esophagus"])
plt.show()
fig, ax = plt.subplots(figsize=(6, 6))
viz.show_slice(pct, dose=pct.dose, dose_min=DOSE_MIN, ax=ax, title=f"Dawka ≥ {DOSE_MIN} Gy")
plt.show()

# %% [markdown]
# ### Przeglądarka przekrojów
# Przesuwaj suwak (w Colab działa interaktywnie).

# %%
viz.slice_browser(pct, dose=pct.dose)

# %% [markdown]
# ## 7. Pierwszy DVH
# Histogram dawka–objętość streszcza trójwymiarowy rozkład dawki w jednym wykresie dla każdej
# struktury. W bloku 4 zobaczymy, jak zmienia się, gdy zmienimy kontur.

# %%
data.add_derived_structures(pct)
names = [n for n in ["PTV", "GTV", "Lungs-GTV", "Heart", "Esophagus", "SpinalCord"] if n in pct.structures]
viz.plot_dvh(pct.dose, pct.structures, names=names)
plt.show()
metrics.check_constraints(pct.dose, pct.structures, pct.spacing)

# %% [markdown]
# ## Zadania „zmień i zinterpretuj”
# 1. **Okno** (sekcja 3): dobierz okno do oceny granicy guz–płuco i guz–śródpiersie. Zapisz parametry.
# 2. **Izodozy** (sekcja 6): przy jakim `DOSE_MIN` kolor przestaje obejmować rdzeń kręgowy? Odczytaj z DVH D0.03cc rdzenia i porównaj.
# 3. **Rozdzielczość**: odczytaj krok siatki dawki i CT. Jak duży błąd (w mm) może powstać w miejscu stromego spadku dawki?
# 4. **Kontur** (sekcja 4): ustaw `ROI_TO_SHOW` na najmniejszą strukturę. Ile ma punktów na przekrój? Czy objętość z tabeli jest wiarygodna przy takim rozmiarze vokseli?
# 5. **Anonimizacja**: w wyniku `describe()` wskaż pola, które w prawdziwym pliku identyfikowałyby pacjenta. Czy UID mogą być daną osobową?
#
# ## Pytania do dyskusji
# - Co się stanie, jeśli RTSTRUCT zostanie przypięty do innej serii CT (inny `FrameOfReferenceUID`)? Kto i na jakim etapie powinien to wychwycić?
# - Dlaczego DVH „ukrywa” informację o tym, **gdzie** jest gorąca plama dawki?
# - Narzędzie AI do autokonturowania zwraca RTSTRUCT. Które pola DICOM sprawdzisz przy odbiorze wyniku (np. nazwy struktur, `ROIGenerationAlgorithm`, UID)?
# - Dlaczego objętość tej samej struktury może się różnić w dwóch systemach planowania?
#
# ## Zadanie dodatkowe dla chętnych (programistyczne)
# **A.** Napisz funkcję `check_rt_consistency(folder)`, która zwraca listę problemów: różne `PatientID`,
# różne `FrameOfReferenceUID`, RTSTRUCT odwołujący się do nieistniejącej serii CT, RTDOSE bez odwołania do planu.
# Przetestuj ją, „psując” celowo jeden plik (zmień UID w kopii pliku przez `pydicom`).
#
# **B.** Zaimplementuj własną rasteryzację konturu (bez `rtcourse`) i porównaj objętości z tabelą z sekcji 4.
# Jak wynik zależy od reguły „czy środek vokseli leży w wielokącie” vs „czy voksel w ogóle przecina wielokąt”?
#
# **C.** Policz indeks homogeniczności PTV: `HI = (D2% − D98%) / D50%` i indeks konformalności
# `CI = V95% / V_PTV` (V95% = objętość ciała z dawką ≥ 95% dawki zadanej). Użyj `metrics.dose_at_volume`.

# %%
# Miejsce na Twój kod (zadanie dodatkowe)
