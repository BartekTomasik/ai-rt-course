# %% [markdown]
# # Blok 3. Autosegmentacja: TotalSegmentator vs kontur ręczny
#
# **Cel kliniczny.** Narzędzia AI do autokonturowania narządów krytycznych (OAR) są już w wielu
# zakładach. Skracają czas pracy, ale **każdy kontur trzeba zweryfikować**. Żeby ocenić narzędzie
# (i zdecydować, ile poprawek wymaga), trzeba umieć porównać kontur AI z konturem referencyjnym
# i rozumieć, co mówią — a czego nie mówią — liczby takie jak Dice czy HD95.
#
# **Po zajęciach:** uruchamiasz autosegmentację (lub korzystasz z gotowych wyników), liczysz
# Dice, HD95 i surface Dice, rozpoznajesz typowe błędy modeli i wiesz, dlaczego „Dice = 0,9” może
# oznaczać zarówno kontur dobry, jak i klinicznie nieakceptowalny.
#
# ### Krótka teoria
# - **TotalSegmentator** (Wasserthal i wsp., *Radiology: AI* 2023) — otwarty model oparty na nnU-Net,
#   segmentuje ponad 100 struktur na CT. Na GPU trwa to kilkadziesiąt sekund, na CPU (tryb `fast`) kilka minut.
# - **Dice** = 2|A∩B| / (|A|+|B|): miara nakładania objętości, 0–1. Duże narządy „łatwo” mają wysoki Dice.
# - **HD95** (95. percentyl odległości Hausdorffa, mm): jak daleko są najgorsze fragmenty granicy.
# - **Surface Dice przy tolerancji τ** (Nikolov i wsp. 2021): jaka część powierzchni leży w odległości ≤ τ mm
#   od konturu referencyjnego — dobrze koreluje z **czasem potrzebnym na poprawki**.
# - Kontur „referencyjny” też ma błąd: zmienność między obserwatorami bywa porównywalna z błędem modelu.

# %%
# INCLUDE: _setup.py

# %% [markdown]
# ## 1. Wczytanie przypadku i konturu referencyjnego (ręcznego)

# %%
from rtcourse import autoseg

CASE_INDEX = 0  # zmień, aby obejrzeć inny przypadek z pakietu
case = data.load_case(CASE_INDEX, MODE)
print(case.summary())
OARS = [n for n in ["Lung_L", "Lung_R", "Heart", "Esophagus", "SpinalCord"] if n in case.structures]
reference = {n: case.structures[n] for n in OARS}

# %% [markdown]
# ## 2. Autosegmentacja
# - Dane rzeczywiste + GPU → uruchamiamy TotalSegmentator na żywo (instalacja ok. 1–2 min, pierwsze
#   uruchomienie pobiera wagi modelu).
# - Brak GPU → wyniki policzone wcześniej przez prowadzącego (pakiet kursu).
# - Fantom syntetyczny → **symulowany model AI**: kontury referencyjne z wprowadzonymi typowymi błędami
#   (opis błędów: `autoseg.DEFAULT_ERRORS`). To uczciwe ćwiczenie z oceny, nie z działania sieci.
#
# W Colab GPU włączysz: *Środowisko wykonawcze → Zmień typ środowiska → GPU (T4)*.

# %%
RUN_LIVE = "auto"  # "auto" = tylko gdy jest GPU; True = wymuś (na CPU kilka–kilkanaście minut); False = nigdy

live = case.source != "synthetic" and (RUN_LIVE is True or (RUN_LIVE == "auto" and autoseg.has_gpu()))
if live:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "TotalSegmentator"], check=False)
ai, how = autoseg.get_autoseg(case, pack_dir=data.find_course_pack(), allow_live=live)
ai = {n: ai[n] for n in OARS if n in ai}
print("Źródło konturów AI:", {"totalsegmentator": "TotalSegmentator (na żywo)",
                              "precomputed": "TotalSegmentator (wyniki przygotowane wcześniej)",
                              "simulated": "symulowany model AI (tryb syntetyczny/awaryjny)"}[how])

# %% [markdown]
# ## 3. Porównanie wizualne
# Linia ciągła = kontur referencyjny, przerywana = AI. Najpierw **popatrz**, potem licz.

# %%
viz.show_three_views(case, structures=OARS, extra=ai)
plt.show()

# %%
viz.slice_browser(case, structures=OARS, extra=ai)

# %% [markdown]
# ## 4. Metryki zgodności

# %%
TOLERANCE_MM = 2.0  # tolerancja surface Dice
table = metrics.compare_masks(reference, ai, case.spacing, tolerance_mm=TOLERANCE_MM)
table

# %% [markdown]
# **Zadanie 1.** Uszereguj narządy od „najlepszego” do „najgorszego” według Dice, a potem według HD95
# i surface Dice. Czy kolejność jest ta sama? Który narząd wymagałby najwięcej poprawek w praktyce?

# %% [markdown]
# ## 5. Dlaczego Dice zależy od wielkości narządu
# Ten sam błąd — przesunięcie granicy o 3 mm (dylatacja) — dla każdego narządu.
#
# **Zadanie 2 (zmień parametr).** Zmień `ERROR_MM` na 1, 3, 5 mm (ujemne = kontur za mały).
# Przy jakim błędzie rdzeń kręgowy spada poniżej Dice 0,8? A płuco?

# %%
ERROR_MM = 3.0
rows = []
for n in OARS:
    m = autoseg.perturb_mask(reference[n], case.spacing, dilate_mm=ERROR_MM)
    rows.append({"narząd": n, "objętość [cm³]": round(metrics.volume_cc(reference[n], case.spacing), 1),
                 "Dice": round(metrics.dice(reference[n], m), 3),
                 "HD95 [mm]": round(metrics.hd95(reference[n], m, case.spacing), 1)})
size_table = pd.DataFrame(rows).sort_values("objętość [cm³]")
ax = size_table.plot.scatter(x="objętość [cm³]", y="Dice", logx=True, figsize=(6, 4), s=40)
for _, r in size_table.iterrows():
    ax.annotate(r["narząd"], (r["objętość [cm³]"], r["Dice"]), fontsize=8)
ax.set_title(f"Ten sam błąd {ERROR_MM:+g} mm — różny Dice"); plt.show()
size_table

# %% [markdown]
# ## 6. Surface Dice: tolerancja ma znaczenie
# Tolerancja odpowiada pytaniu „jaki błąd granicy akceptujemy bez poprawiania?”. W literaturze używa się
# zwykle 1–3 mm, zależnie od narządu i rozmiaru vokseli.

# %%
tols = [1, 2, 3, 5, 8]
sd = pd.DataFrame({f"{t} mm": {n: metrics.surface_dice(reference[n], ai[n], case.spacing, t) for n in ai} for t in tols}).round(3)
sd.T.plot(marker="o", figsize=(6, 4), title="Surface Dice vs tolerancja", ylabel="surface Dice", xlabel="tolerancja")
plt.show()
sd

# %% [markdown]
# ## 7. Katalog typowych błędów modeli
# Poniżej sztucznie wywołujemy znane błędy na jednym narządzie i patrzymy, **która metryka je wyłapuje**.
#
# **Zadanie 3 (zmień parametr).** Wybierz `ORGAN` i zmień wartości w słowniku `ERRORS`.
# Który błąd prawie nie zmienia Dice, a mocno zmienia HD95? Który błąd jest groźny dla dawki?

# %%
ORGAN = "Esophagus" if "Esophagus" in reference else OARS[0]
ERRORS = {
    "przesunięcie 3 mm (rejestracja)": dict(shift_mm=(0, 3, 0)),
    "za duży o 2 mm (konwencja)": dict(dilate_mm=2),
    "za mały o 2 mm": dict(dilate_mm=-2),
    "brak 20% dolnego końca": dict(drop_caudal_frac=0.2),
    "brak 2 przekrojów w środku": dict(miss_slices=2),
    "nierówna granica (szum 2 mm)": dict(boundary_noise_mm=2),
}
rows = []
for label, params in ERRORS.items():
    m = autoseg.perturb_mask(reference[ORGAN], case.spacing, seed=1, **params)
    rows.append({"błąd": label, "Dice": metrics.dice(reference[ORGAN], m), "HD95 [mm]": metrics.hd95(reference[ORGAN], m, case.spacing),
                 "sDice 2 mm": metrics.surface_dice(reference[ORGAN], m, case.spacing, 2),
                 "ΔV [%]": 100 * (m.sum() - reference[ORGAN].sum()) / reference[ORGAN].sum()})
pd.DataFrame(rows).set_index("błąd").round(2)

# %% [markdown]
# ## 8. Gdzie są błędy? Dice warstwa po warstwie
# Średnia z całego narządu ukrywa lokalizację błędu. Błędy często kumulują się na **końcach** narządu
# (górny/dolny biegun), w okolicy guza i w miejscach o słabym kontraście.

# %%
ORGAN_Z = ORGAN
r, a = reference[ORGAN_Z], ai.get(ORGAN_Z, reference[ORGAN_Z])
zs = np.nonzero(r.any(axis=(1, 2)) | a.any(axis=(1, 2)))[0]
z_mm = case.origin[2] + zs * case.spacing[0]
per_slice = [metrics.dice(r[k], a[k]) for k in zs]
plt.figure(figsize=(8, 3))
plt.plot(z_mm, per_slice, "o-")
plt.xlabel("z [mm] (w stronę głowy →)"); plt.ylabel("Dice na przekroju"); plt.ylim(-0.05, 1.05)
plt.title(f"{ORGAN_Z}: zgodność na kolejnych przekrojach"); plt.grid(alpha=0.3); plt.show()

# %% [markdown]
# ## Zadania „zmień i zinterpretuj” — podsumowanie
# 1. (sekcja 4) Zmień `TOLERANCE_MM` na 1 i 3 mm. Który narząd najbardziej „zyskuje” na większej tolerancji?
# 2. (sekcja 5) Znajdź błąd w mm, przy którym Dice serca spada poniżej 0,9. Czy taki błąd jest klinicznie istotny?
# 3. (sekcja 7) Zaproponuj kryterium akceptacji dla przełyku (np. „Dice ≥ … i HD95 ≤ … mm”). Które błędy z katalogu przejdą Twoje kryterium, choć nie powinny?
# 4. (sekcja 8) Na którym końcu narządu model myli się najczęściej? Co to oznacza dla weryfikacji konturów przez elektroradiologa?
#
# ## Pytania do dyskusji
# - Kontur referencyjny w zbiorze publicznym narysował jeden ekspert. Co, jeśli to on się myli? Jak oszacować zmienność między obserwatorami?
# - Czy model AI może być „lepszy od człowieka”, jeśli oceniamy go względem konturów człowieka?
# - Różne zakłady konturują serce inaczej (z dużymi naczyniami lub bez). Jak to wpływa na odbiór narzędzia?
# - Które metryki powinny trafić do protokołu odbioru (blok 7)? Jak policzyć czas oszczędzony na korekcie?
# - Kto ponosi odpowiedzialność za kontur zaakceptowany bez poprawek?
#
# ## Zadanie dodatkowe dla chętnych (programistyczne)
# **A. Postprocessing.** Napisz funkcję, która poprawia maskę AI: zostawia największą spójną składową
# (`scipy.ndimage.label`), wypełnia dziury (`binary_fill_holes`) i usuwa „wyspy” mniejsze niż X cm³.
# Zmierz, czy poprawia Dice/HD95. To dobry punkt startu do **wyzwania z rankingiem** (`projects/challenge/`).
#
# **B. Added path length (APL).** Zaimplementuj metrykę APL (Vaassen i wsp. 2020): długość konturu
# referencyjnego, której nie ma w konturze AI, w mm na przekrój — przybliżenie pracy potrzebnej na poprawki.
#
# **C. Własne kryterium.** Napisz funkcję `qa_flag(reference, ai, spacing)`, która dla każdego narządu
# zwraca „akceptuj / popraw / odrzuć” na podstawie kilku metryk i uzasadnij progi.

# %%
# Miejsce na Twój kod (zadanie dodatkowe)
