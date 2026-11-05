# %% [markdown]
# # Blok 4. Kontur a dawka: jak błędy konturu zmieniają DVH i ocenę planu
#
# **Cel kliniczny.** Decyzja „plan jest akceptowalny” opiera się na DVH i limitach dawek dla narządów
# krytycznych. DVH liczy się **z konturu** — jeśli kontur jest zły, ocena planu jest zła, nawet gdy
# dawka jest policzona perfekcyjnie. Z kolei błędny kontur PTV zmienia **samą dawkę** (plan jest
# optymalizowany do złego celu). Po zajęciach umiesz pokazać oba efekty liczbowo.
#
# ### Krótka teoria
# - **Scenariusz A — ocena:** dawka bez zmian, inny kontur OAR → inne DVH, Dmean, Vx. Wpływ jest duży,
#   gdy granica narządu leży w **gradiencie dawki** (blisko PTV), i mały, gdy narząd jest daleko.
# - **Scenariusz B — planowanie:** inny kontur PTV → inna dawka → zmienia się zarówno pokrycie guza, jak i dawki w OAR.
# - Dice mówi o geometrii, nie o dawce. Dwa kontury z tym samym Dice mogą dawać bardzo różne Dmean.
#
# ⚠️ **Dawka w tym notatniku jest liczona prostym modelem edukacyjnym** (`rtcourse.dose`: kilka wiązek,
# osłabienie, półcień). To nie jest system planowania leczenia — liczby służą do porównań „co jeśli”.
# Limity dawek są przykładowe (konwencjonalna RT płuca 60 Gy/30 fr.); w zakładzie obowiązują lokalne protokoły.

# %%
# INCLUDE: _setup.py

# %% [markdown]
# ## 1. Przypadek, dawka i limity dla planu referencyjnego

# %%
from rtcourse import autoseg, dose as dose_model

case = data.load_case(0, MODE)
if case.dose is None:  # dane bez dawki → dawka modelowa
    if "PTV" not in case.structures:
        data.place_virtual_tumor(case)
    case.dose = dose_model.compute_dose(case.structures["PTV"], case.spacing, body=case.structures.get("BODY"))
data.add_derived_structures(case)
print(case.summary())
DVH_NAMES = [n for n in ["PTV", "Lungs-GTV", "Heart", "Esophagus", "SpinalCord"] if n in case.structures]
viz.show_slice(case, dose=case.dose, structures=DVH_NAMES + ["GTV"])
plt.show()
ref_check = metrics.check_constraints(case.dose, case.structures, case.spacing)
ref_check

# %% [markdown]
# ## 2. Scenariusz A: ta sama dawka, kontury AI
# Kontury z modelu AI (lub symulowanego modelu — patrz blok 3) oceniamy na **tej samej** dawce.

# %%
ai, how = autoseg.get_autoseg(case, pack_dir=data.find_course_pack(), allow_live=False)
ai_structs = dict(case.structures)
ai_structs.update(ai)
data.add_derived_structures(type(case)(ct=case.ct, spacing=case.spacing, origin=case.origin, structures=ai_structs))
print("Kontury AI:", how)

fig, ax = plt.subplots(figsize=(9, 5))
viz.plot_dvh(case.dose, case.structures, names=DVH_NAMES, ax=ax)
viz.plot_dvh(case.dose, ai_structs, names=DVH_NAMES, ax=ax, style="--", label_suffix=" (AI)")
ax.set_title("DVH: kontur referencyjny (ciągła) vs AI (przerywana)"); plt.show()

ai_check = metrics.check_constraints(case.dose, ai_structs, case.spacing)
cmp = ref_check[["structure", "metric", "limit"]].copy()
cmp["referencja"] = ref_check["value"]
cmp["AI"] = ai_check["value"]
cmp["różnica"] = (cmp["AI"] - cmp["referencja"]).round(2)
cmp["status ref / AI"] = ref_check["status"] + " / " + ai_check["status"]
cmp

# %% [markdown]
# **Zadanie 1.** Który narząd ma największą różnicę dawki? Porównaj z Dice z bloku 3 — czy narząd
# z najgorszym Dice ma też największy błąd dawkowy?

# %% [markdown]
# ## 3. Wrażliwość: o ile zmieni się dawka, gdy kontur urośnie/zmaleje o X mm?
# **Zadanie 2 (zmień parametr).** Zmień `ORGAN`. Dla którego narządu krzywa jest najbardziej stroma i dlaczego?

# %%
ORGAN = "Heart" if "Heart" in case.structures else DVH_NAMES[-1]
METRIC = "Dmean"  # np. "Dmean", "V20Gy", "D0.03cc", "V50Gy"
MARGINS_MM = [-6, -4, -2, 0, 2, 4, 6]
vals, dices = [], []
for mm in MARGINS_MM:
    m = autoseg.perturb_mask(case.structures[ORGAN], case.spacing, dilate_mm=mm) & case.structures.get("BODY", True)
    vals.append(metrics.evaluate_metric(case.dose, m, case.spacing, METRIC))
    dices.append(metrics.dice(case.structures[ORGAN], m))
fig, ax1 = plt.subplots(figsize=(7, 4))
ax1.plot(MARGINS_MM, vals, "o-", color="C3"); ax1.set_xlabel("zmiana granicy konturu [mm]"); ax1.set_ylabel(f"{ORGAN} {METRIC}", color="C3")
ax2 = ax1.twinx(); ax2.plot(MARGINS_MM, dices, "s--", color="C0"); ax2.set_ylabel("Dice", color="C0")
ax1.set_title(f"{ORGAN}: wrażliwość {METRIC} na błąd konturu"); ax1.grid(alpha=0.3); plt.show()
pd.DataFrame({"mm": MARGINS_MM, METRIC: np.round(vals, 2), "Dice": np.round(dices, 3)})

# %% [markdown]
# ## 4. Ten sam Dice, inna dawka — kierunek błędu ma znaczenie
# Przesuwamy kontur narządu o tę samą odległość w różnych kierunkach: **do** PTV i **od** PTV.
# Dice jest podobny, a dawka — nie.

# %%
SHIFT_MM = 4.0
ptv_c = np.array(np.nonzero(case.structures["PTV"])).mean(axis=1)
org_c = np.array(np.nonzero(case.structures[ORGAN])).mean(axis=1)
direction = (ptv_c - org_c) * np.array(case.spacing)
direction[0] = 0  # tylko w płaszczyźnie poprzecznej
direction /= np.linalg.norm(direction) + 1e-9
rows = []
for label, sign in [("w stronę PTV", 1), ("od PTV", -1)]:
    shift = tuple(sign * SHIFT_MM * direction)
    m = autoseg.perturb_mask(case.structures[ORGAN], case.spacing, shift_mm=shift)
    rows.append({"przesunięcie": f"{SHIFT_MM} mm {label}", "Dice": round(metrics.dice(case.structures[ORGAN], m), 3),
                 "Dmean [Gy]": round(metrics.mean_dose(case.dose, m), 2),
                 "D0.03cc [Gy]": round(metrics.dose_at_abs_volume(case.dose, m, case.spacing), 1)})
rows.append({"przesunięcie": "referencja", "Dice": 1.0, "Dmean [Gy]": round(metrics.mean_dose(case.dose, case.structures[ORGAN]), 2),
             "D0.03cc [Gy]": round(metrics.dose_at_abs_volume(case.dose, case.structures[ORGAN], case.spacing), 1)})
pd.DataFrame(rows)

# %% [markdown]
# ### Wiele losowych błędów: Dice vs błąd dawki
# Każdy punkt to inny losowy błąd konturu (przesunięcie + zmiana rozmiaru + szum granicy).

# %%
N_TRIALS = 25
rng = np.random.default_rng(0)
ref_val = metrics.mean_dose(case.dose, case.structures[ORGAN])
pts = []
for i in range(N_TRIALS):
    params = dict(shift_mm=tuple(rng.normal(0, 3, 3) * [0.5, 1, 1]), dilate_mm=float(rng.normal(0, 2)), boundary_noise_mm=float(abs(rng.normal(0, 1.5))))
    m = autoseg.perturb_mask(case.structures[ORGAN], case.spacing, seed=i, **params)
    pts.append((metrics.dice(case.structures[ORGAN], m), metrics.mean_dose(case.dose, m) - ref_val))
pts = np.array(pts)
plt.figure(figsize=(6, 4)); plt.scatter(pts[:, 0], pts[:, 1]); plt.axhline(0, color="k", lw=0.5)
plt.xlabel("Dice"); plt.ylabel(f"Δ Dmean {ORGAN} [Gy]"); plt.title("Wysoki Dice ≠ mały błąd dawki"); plt.grid(alpha=0.3); plt.show()

# %% [markdown]
# ## 5. Scenariusz B: błąd konturu celu zmienia plan
# Plan „optymalizujemy” (tu: liczymy modelem) do PTV o różnym marginesie. Patrzymy na pokrycie
# **prawdziwego** GTV/PTV i na dawki w narządach krytycznych.
#
# **Zadanie 3 (zmień parametr).** Zmień listę `PTV_MARGINS_MM` i `GTV_ERROR_MM` (ujemny = AI/lekarz
# narysował za mały GTV). Od jakiego błędu prawdziwy GTV traci pokrycie (D98% < 95% dawki zadanej)?

# %%
PTV_MARGINS_MM = [3, 5, 8, 10]
GTV_ERROR_MM = -3.0  # błąd konturu GTV użytego do planowania
true_gtv = case.structures["GTV"]
true_ptv = case.structures["PTV"]
body = case.structures.get("BODY")
planned_gtv = autoseg.perturb_mask(true_gtv, case.spacing, dilate_mm=GTV_ERROR_MM)
from scipy import ndimage
rows = []
for marg in PTV_MARGINS_MM:
    ptv_plan = ndimage.distance_transform_edt(~planned_gtv, sampling=case.spacing) <= marg
    if body is not None:
        ptv_plan &= body
    d = dose_model.compute_dose(ptv_plan, case.spacing, body=body)
    r = {"margines PTV [mm]": marg, "V(PTV plan) [cm³]": round(metrics.volume_cc(ptv_plan, case.spacing), 1),
         "prawdziwy GTV D98% [Gy]": round(metrics.dose_at_volume(d, true_gtv, 98), 1),
         "prawdziwy PTV D95% [Gy]": round(metrics.dose_at_volume(d, true_ptv, 95), 1)}
    for n, met in [("Lungs-GTV", "V20Gy"), ("Lungs-GTV", "Dmean"), ("Heart", "Dmean"), ("Esophagus", "Dmean")]:
        if n in case.structures:
            r[f"{n} {met}"] = round(metrics.evaluate_metric(d, case.structures[n], case.spacing, met), 1)
    rows.append(r)
pd.DataFrame(rows).set_index("margines PTV [mm]")

# %% [markdown]
# ## Zadania „zmień i zinterpretuj” — podsumowanie
# 1. (sekcja 2) Który limit zmienił status (OK ↔ PRZEKROCZONY) po podmianie konturów na AI? Jeśli żaden — który był najbliżej?
# 2. (sekcja 3) Ustaw `METRIC = "D0.03cc"` i `ORGAN = "SpinalCord"`. Dlaczego dawka maksymalna jest tak wrażliwa na kontur?
# 3. (sekcja 4) Zwiększ `SHIFT_MM` do 6 mm. O ile procent zmienia się Dmean? Czy przeszłoby to niezauważone przy kontroli planu?
# 4. (sekcja 5) Znajdź najmniejszy margines PTV, który przy `GTV_ERROR_MM = -3` nadal daje D98% GTV ≥ 57 Gy. Co „kosztuje” to płuca?
#
# ## Pytania do dyskusji
# - Kontur OAR z AI zaniża dawkę w sercu o 2 Gy. Kto to zauważy i na jakim etapie (konturowanie, planowanie, akceptacja planu, kontrola fizyczna)?
# - Czy kryteria odbioru autokonturowania powinny być **dawkowe**, a nie tylko geometryczne? Jak to zorganizować w zakładzie?
# - Dla których narządów i lokalizacji guza błąd konturu ma największe znaczenie kliniczne?
# - Jak różnice konwencji konturowania (np. serce z naczyniami / bez) wpływają na porównywanie DVH między ośrodkami i w badaniach?
#
# ## Zadanie dodatkowe dla chętnych (programistyczne)
# **A. NTCP.** Zaimplementuj model Lymana–Kutchera–Burmana dla zapalenia płuc (np. n = 1, m = 0,37,
# TD50 = 30,8 Gy — parametry QUANTEC, Marks i wsp. 2010) na podstawie gEUD. Pokaż, jak błąd konturu
# płuc z sekcji 3 zmienia NTCP.
#
# **B. Mapa wrażliwości.** Policz gradient dawki (`np.gradient`) i zaznacz na obrazie miejsca granicy
# narządu, gdzie błąd 1 mm zmienia dawkę o więcej niż 1 Gy. To właśnie tam weryfikacja konturu jest najważniejsza.
#
# **C. Najgorszy przypadek.** Znajdź (przeszukując kierunki i wielkości przesunięcia) błąd konturu o Dice ≥ 0,85,
# który najbardziej zmienia Dmean wybranego narządu. Co z tego wynika dla kryteriów odbioru?

# %%
# Miejsce na Twój kod (zadanie dodatkowe)
