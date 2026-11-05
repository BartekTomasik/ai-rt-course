# %% [markdown]
# # Blok 4b. Frakcjonowanie: BED i EQD2 w praktyce (hipofrakcjonacja, przeliczanie dawek, reirradiacja)
#
# **Cel kliniczny.** Coraz więcej pacjentów leczymy hipofrakcjonacją (pierś 26 Gy/5 fr., prostata 60 Gy/20 fr.,
# SBRT płuca). Limity dawek dla narządów krytycznych pochodzą jednak głównie z frakcjonowania 2 Gy.
# Żeby porównać schematy, przeliczyć limit albo ocenić ponowne napromienianie, trzeba umieć policzyć
# **BED** i **EQD2** — i znać ograniczenia tych obliczeń. To typowe pytanie przy stole: „ile to jest w 2 Gy?”.
#
# ### Krótka teoria (model liniowo-kwadratowy, LQ)
# $$BED = n\,d\left(1 + \frac{d}{\alpha/\beta}\right), \qquad EQD2 = \frac{BED}{1 + 2/(\alpha/\beta)} = n\,d\,\frac{d + \alpha/\beta}{2 + \alpha/\beta}$$
# - $n$ — liczba frakcji, $d$ — dawka na frakcję, $\alpha/\beta$ — „wrażliwość na wielkość frakcji” tkanki.
# - **Niskie α/β** (tkanki późno reagujące ~3 Gy, rdzeń ~2 Gy, rak prostaty ~1,5 Gy) → duże frakcje są „droższe”.
#   **Wysokie α/β** (większość guzów, odczyny wczesne ~10 Gy) → mniejsza zależność od wielkości frakcji.
# - **Ograniczenia:** α/β są niepewne (często ± kilka Gy); LQ jest dyskusyjny przy bardzo dużych frakcjach (> 8–10 Gy, SBRT);
#   podstawowe wzory pomijają czas leczenia (repopulacja) i niepełną naprawę między frakcjami.
#
# ⚠️ Materiał dydaktyczny. Dawki są syntetyczne (fantom), wartości α/β i limity — przykładowe. Decyzje kliniczne podejmuje się
# na podstawie protokołów zakładu i literatury, z udziałem lekarza i fizyka.
#
# *Notatnik wykorzystuje pomysły z notatnika „EQD2 i BED w praktyce” z repozytorium rt-toolkit (licencja MIT).*

# %%
# INCLUDE: _setup.py

# %%
from rtcourse import radiobiology as rb
from rtcourse.phantom import make_phantom
from rtcourse import dose as dose_model

pd.DataFrame({"α/β [Gy]": rb.ALPHA_BETA_TYPICAL}).T

# %% [markdown]
# ## 1. Porównanie schematów frakcjonowania
# **Zadanie 1 (zmień parametr).** Dopisz do słownika `SCHEMES` własny schemat (np. 25 Gy/5 fr. w raku odbytnicy, 30 Gy/10 fr. paliatywnie)
# i zmień listę `ALPHA_BETAS`. Który schemat jest „najsilniejszy” dla guza, a który dla tkanek późno reagujących?

# %%
SCHEMES = {  # nazwa: (dawka całkowita [Gy], liczba frakcji)
    "konwencjonalny 60/30": (60, 30),
    "pierś 40,05/15 (START-B)": (40.05, 15),
    "pierś 26/5 (FAST-Forward)": (26, 5),
    "prostata 60/20 (CHHiP)": (60, 20),
    "prostata SBRT 36,25/5": (36.25, 5),
    "płuco 55/20": (55, 20),
    "płuco SBRT 54/3": (54, 3),
    "odbytnica 25/5": (25, 5),
}
ALPHA_BETAS = [1.5, 3, 10]
tab = pd.DataFrame({f"EQD2 (α/β={ab})": {k: rb.eqd2(D, n, ab) for k, (D, n) in SCHEMES.items()} for ab in ALPHA_BETAS})
tab.insert(0, "Gy/fr.", {k: D / n for k, (D, n) in SCHEMES.items()})
tab.insert(1, "BED₁₀", {k: rb.bed(D, n, 10) for k, (D, n) in SCHEMES.items()})
tab.round(1)

# %% [markdown]
# ## 2. Dlaczego dawka frakcyjna ma znaczenie
# Na wykresie: ile „waży” 1 Gy fizyczny po przeliczeniu na EQD2, w zależności od dawki na frakcję.

# %%
d = np.linspace(1, 12, 200)
plt.figure(figsize=(7, 4))
for ab in [1.5, 2, 3, 10]:
    plt.plot(d, rb.eqd2(10 * d, 10, ab) / (10 * d), label=f"α/β = {ab} Gy")
plt.axvline(2, color="gray", ls=":"); plt.axvspan(8, 12, color="orange", alpha=0.1, label="LQ dyskusyjny")
plt.xlabel("dawka na frakcję d [Gy]"); plt.ylabel("EQD2 / dawka fizyczna"); plt.grid(alpha=0.3); plt.legend()
plt.title("Tkanki o niskim α/β są bardziej wrażliwe na dużą frakcję"); plt.show()

# %% [markdown]
# ## 3. Przeliczanie limitu na inny schemat
# Limit dla rdzenia „50 Gy w frakcjach 2 Gy” (EQD2, α/β = 2 Gy). Ile to jest dawki **fizycznej** przy innej liczbie frakcji?
#
# **Zadanie 2 (zmień parametr).** Zmień `LIMIT_EQD2` i `AB_OAR` (np. 45 Gy / 2 Gy dla rdzenia, 54 Gy / 2 Gy dla pnia mózgu,
# 3 Gy dla odbytnicy). O ile procent maleje dopuszczalna dawka fizyczna przy 5 frakcjach względem 30?

# %%
LIMIT_EQD2 = 50.0
AB_OAR = 2.0
FRACTIONS = [1, 3, 5, 8, 10, 15, 20, 25, 30]
conv = pd.DataFrame({"frakcje": FRACTIONS,
                     "dawka fizyczna [Gy]": [rb.total_dose_for_eqd2(LIMIT_EQD2, n, AB_OAR) for n in FRACTIONS]})
conv["Gy/fr."] = conv["dawka fizyczna [Gy]"] / conv["frakcje"]
conv["sprawdzenie EQD2"] = [rb.eqd2(D, n, AB_OAR) for D, n in zip(conv["dawka fizyczna [Gy]"], conv["frakcje"])]
conv.round(2)

# %% [markdown]
# ## 4. DVH w EQD2 — voxel po vokselu
# Plan fantomu (60 Gy/30 fr.) „przenosimy” na schemat hipofrakcjonowany **55 Gy/20 fr.**, zakładając ten sam kształt rozkładu dawki
# (przeskalowanie). Każdy voxel ma inną dawkę na frakcję, więc EQD2 liczymy **dla każdego voxela osobno**,
# z mapą α/β: guz (PTV/GTV) 10 Gy, rdzeń 2 Gy, pozostałe tkanki 3 Gy.
#
# **Zadanie 3 (zmień parametr).** Zmień `RX_TOTAL` i `RX_FRACTIONS` (np. 60/15, 54/3). Które limity przestają być spełnione po przeliczeniu do EQD2?

# %%
RX_TOTAL, RX_FRACTIONS = 55.0, 20
case = data.add_derived_structures(make_phantom(seed=0, variability=0.0))
S = case.structures
phys = case.dose * (RX_TOTAL / 60.0)
ab_map = rb.alpha_beta_map(S, case.shape, default=3.0, overrides={"PTV": 10.0, "GTV": 10.0, "SpinalCord": 2.0})
eq = rb.dose_to_eqd2(phys, RX_FRACTIONS, ab_map)
names = ["PTV", "Lungs-GTV", "Heart", "Esophagus", "SpinalCord"]
fig, ax = plt.subplots(figsize=(9, 5))
viz.plot_dvh(phys, S, names=names, ax=ax)
viz.plot_dvh(eq, S, names=names, ax=ax, style="--", label_suffix=" (EQD2)")
ax.set_title(f"{RX_TOTAL:g} Gy / {RX_FRACTIONS} fr.: dawka fizyczna (ciągła) vs EQD2 (przerywana)"); plt.show()

# %% [markdown]
# Limity w tabeli zdefiniowano dla frakcjonowania 2 Gy, więc porównujemy z nimi **EQD2**, a nie dawkę fizyczną.
# (Dla PTV pokazujemy też D95% w EQD2 z α/β = 10 Gy.)

# %%
c_phys = metrics.check_constraints(phys, S, case.spacing)
c_eq = metrics.check_constraints(eq, S, case.spacing)
cmp = c_phys[["structure", "metric", "limit"]].copy()
cmp["fizyczna"] = c_phys["value"]
cmp["EQD2"] = c_eq["value"]
cmp["status (EQD2)"] = c_eq["status"]
cmp

# %% [markdown]
# ### Pułapka: EQD2 ze średniej ≠ średnia z EQD2
# EQD2 jest nieliniowe względem dawki, więc przeliczenie **samej średniej** daje inny wynik niż przeliczenie każdego voxela.

# %%
rows = []
for n in ["Lungs-GTV", "Heart", "Esophagus"]:
    m = S[n]
    rows.append({"struktura": n, "Dmean fizyczna": phys[m].mean(),
                 "EQD2 ze średniej": rb.eqd2(phys[m].mean(), RX_FRACTIONS, 3.0),
                 "średnia z EQD2 (voxel)": eq[m].mean()})
pd.DataFrame(rows).set_index("struktura").round(2)

# %% [markdown]
# ## 5. Przerwa w leczeniu (czas całkowity)
# Dla szybko proliferujących guzów (np. rak płaskonabłonkowy głowy i szyi) wydłużenie leczenia obniża efekt:
# uproszczenie: $BED_{\text{eff}} = BED - K\,(T - T_k)$ dla $T > T_k$ (typowo $K \approx 0{,}9$ Gy₁₀/dzień, $T_k \approx 28$ dni — wartości niepewne).
#
# **Zadanie 4.** Ile BED₁₀ „traci” pacjent leczony 70 Gy/35 fr., jeśli przerwa wydłużyła leczenie z 46 do 53 dni?

# %%
T_PLANNED, T_ACTUAL = 46, 53
b_plan = rb.bed_with_time(70, 35, 10, T_PLANNED)
b_act = rb.bed_with_time(70, 35, 10, T_ACTUAL)
print(f"BED10 planowane: {b_plan:.1f} Gy | po przerwie: {b_act:.1f} Gy | strata: {b_plan - b_act:.1f} Gy "
      f"(≈ {rb.eqd2_from_bed(b_plan - b_act, 10):.1f} Gy EQD2)")

# %% [markdown]
# ## 6. Reirradiacja: suma EQD2 voxel po vokselu
# Pacjent po 60 Gy/30 fr. (kurs 1) ma nawrót bliżej kręgosłupa; planujemy 30 Gy/10 fr. (kurs 2, nowy PTV).
# Sumujemy EQD2 rdzenia (α/β = 2 Gy), zakładając, że część dawki z 1. kursu „odnowiła się” (recovery).
#
# ⚠️ Założenia: wspólna, zarejestrowana siatka (tu ten sam fantom — w praktyce potrzebna rejestracja, często deformowalna),
# empiryczne i niepewne współczynniki odnowy, zmiany anatomiczne. Wynik ma charakter wyłącznie dydaktyczny.
#
# **Zadanie 5 (zmień parametr).** Zmień `RECOVERY` (0, 0,25, 0,5) i położenie nawrotu `RECURRENCE_SHIFT_MM`. Kiedy suma przekracza 50 Gy EQD2?

# %%
from scipy import ndimage
RECOVERY = 0.25            # część dawki z kursu 1, która się „odnowiła”
RECURRENCE_SHIFT_MM = (0, 70, 35)  # (z, y, x): przesunięcie nawrotu względem pierwotnego GTV [mm] (tu: przykręgosłupowo)
shift_vox = [s / sp for s, sp in zip(RECURRENCE_SHIFT_MM, case.spacing)]
gtv2 = ndimage.shift(S["GTV"].astype(np.uint8), shift_vox, order=0) > 0
ptv2 = (ndimage.distance_transform_edt(~gtv2, sampling=case.spacing) <= 5.0) & S["BODY"]
dose2 = dose_model.compute_dose(ptv2, case.spacing, body=S["BODY"], prescription=30.0, angles=(0, 120, 240))
cord = S["SpinalCord"]
total = rb.sum_eqd2([(case.dose, 30), (dose2, 10)], alpha_beta=2.0, recovery_factors=[1 - RECOVERY, 1.0])
res = pd.DataFrame({
    "kurs 1 (EQD2)": [metrics.dose_at_abs_volume(rb.dose_to_eqd2(case.dose, 30, 2.0), cord, case.spacing)],
    "kurs 2 (EQD2)": [metrics.dose_at_abs_volume(rb.dose_to_eqd2(dose2, 10, 2.0), cord, case.spacing)],
    f"suma (odnowa {RECOVERY:.0%} kursu 1)": [metrics.dose_at_abs_volume(total, cord, case.spacing)],
}, index=["rdzeń D0.03cc [Gy EQD2]"]).round(1)
k = int(np.round(np.nonzero(gtv2)[0].mean())) if gtv2.any() else case.shape[0] // 2
viz.show_slice(case, index=k, dose=total, structures=["SpinalCord", "PTV", "Esophagus"], title="suma EQD2 (α/β = 2 Gy)")
plt.show()
res

# %% [markdown]
# ## Zadania „zmień i zinterpretuj” — podsumowanie
# 1. (sekcja 1) Policz EQD2 dla 5 × 5 Gy (odbytnica) przy α/β = 10 Gy i 3 Gy. Dlaczego ten sam schemat jest „słabszy” dla guza niż 50 Gy/25 fr., a „podobny” dla tkanek późnych?
# 2. (sekcja 3) Rdzeń: ile Gy fizycznie odpowiada 50 Gy EQD2 w 5 frakcjach? Porównaj z limitami stosowanymi w SBRT w Twoim zakładzie.
# 3. (sekcja 4) Dla 60 Gy/15 fr. które limity przestają być spełnione? Czy wniosek byłby inny bez przeliczenia do EQD2?
# 4. (sekcja 4) Kiedy różnica „EQD2 ze średniej” vs „średnia z EQD2” jest największa? (Wskazówka: niejednorodna dawka, niskie α/β.)
# 5. (sekcja 6) Pacjent miał 30 × 2 Gy na rdzeń (Dmax 44 Gy). Ile EQD2 zostaje do 50 Gy przy 0%, 25% i 50% odnowy?
#
# ## Pytania do dyskusji
# - Jak pewne są wartości α/β? Jak duży błąd w EQD2 daje α/β = 3 ± 1 Gy dla schematu 26 Gy/5 fr.?
# - Kiedy w zakładzie przelicza się dawki do EQD2 (zmiana schematu, przerwa, reirradiacja, raport)? Kto to robi i kto sprawdza?
# - Dlaczego sumowanie dawek z dwóch kursów „voxel po vokselu” wymaga rejestracji obrazów? Co, jeśli pacjent schudł 10 kg?
# - Czy wolno używać LQ dla SBRT 1 × 20 Gy? Jakie są alternatywy (np. model LQ-L)?
#
# ## Zadanie dodatkowe dla chętnych (programistyczne)
# **A. Niepewność α/β.** Dla wybranego schematu i narządu policz EQD2 dla α/β losowanego z rozkładu normalnego (np. 3 ± 1 Gy, obcięte do > 0)
# i podaj przedział 95%. Narysuj histogram.
#
# **B. Model LQ-L.** Zaimplementuj wariant liniowo-kwadratowo-liniowy (powyżej dawki progowej d_T krzywa przeżycia staje się liniowa)
# i porównaj EQD2 dla 54 Gy/3 fr. z wersją LQ. Podaj źródło parametrów.
#
# **C. Kompensacja przerwy.** Napisz funkcję, która dla planu 70/35 i przerwy N dni proponuje dawkę frakcyjną pozostałych frakcji
# (lub dodatkowe frakcje), tak aby przywrócić BED₁₀ guza, nie przekraczając EQD2 limitu dla rdzenia. Opisz założenia.

# %%
# Miejsce na Twój kod (zadanie dodatkowe)
