# %% [markdown]
# # Blok 6. Automatyczne planowanie i predykcja dawki (knowledge-based planning)
#
# **Cel kliniczny.** Systemy *knowledge-based planning* (KBP, np. modele uczone na dawnych planach zakładu)
# przewidują, **jakiej dawki w narządzie krytycznym można się spodziewać** u nowego pacjenta, zanim plan powstanie.
# Służy to do: ustawienia celów optymalizacji, wykrywania planów „do poprawy” i wyrównania jakości między planującymi.
# Kluczowa obserwacja: dawka w narządzie zależy głównie od **geometrii** — jak blisko PTV leży narząd.
#
# **Po zajęciach** umiesz policzyć *overlap volume histogram* (OVH), zbudować prostą regresję „geometria → dawka”
# i użyć jej do kontroli jakości planu.
#
# ### Krótka teoria
# - **OVH(r)** = jaka część objętości narządu leży w odległości ≤ r mm od PTV (r < 0 = wewnątrz PTV).
#   Narząd „przyklejony” do PTV ma OVH rosnące już przy małym r.
# - **Model KBP** uczy się zależności: cechy OVH → punkty DVH (np. Dmean, V20).
# - Model odtwarza **praktykę, na której go uczono** — z jej zaletami i wadami.
#
# ⚠️ Pacjenci są syntetyczni, a „plany” liczone prostym modelem dawki (`rtcourse.dose`). Chodzi o zasadę działania.

# %%
# INCLUDE: _setup.py

# %%
from scipy import ndimage
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
from rtcourse.phantom import make_phantom
from rtcourse import dose as dose_model


def ovh(oar, ptv, spacing, radii):
    """Overlap volume histogram: fraction of OAR within distance r of PTV (signed, mm)."""
    d_out = ndimage.distance_transform_edt(~ptv, sampling=spacing)
    d_in = ndimage.distance_transform_edt(ptv, sampling=spacing)
    signed = np.where(ptv, -d_in, d_out)[oar]
    return np.array([(signed <= r).mean() for r in radii])

# %% [markdown]
# ## 1. Kohorta „dawnych planów” zakładu
# Generujemy pacjentów o różnej anatomii i położeniu guza; każdy dostaje plan (dawkę) z tą samą techniką.
#
# **Zadanie 1 (zmień parametr).** `N_PATIENTS` — ile planów „pamięta” zakład. `ORGAN` — narząd, dla którego budujemy model.

# %%
N_PATIENTS = 40
ORGAN = "Heart"      # "Heart" | "Esophagus" | "SpinalCord" | "Lungs-GTV"
METRIC = "Dmean"     # "Dmean" | "V20Gy" | "V5Gy" | "D0.03cc"
RADII = np.arange(-10, 81, 2.0)

patients = []
for i in range(N_PATIENTS):
    c = make_phantom(seed=200 + i, shape=(28, 96, 96), spacing=(5.0, 4.0, 4.0), with_dose=True)
    data.add_derived_structures(c)
    s = c.structures
    patients.append({"case": c, "ovh": ovh(s[ORGAN], s["PTV"], c.spacing, RADII),
                     "value": metrics.evaluate_metric(c.dose, s[ORGAN], c.spacing, METRIC)})
print(f"{len(patients)} planów; {ORGAN} {METRIC}: od {min(p['value'] for p in patients):.1f} do {max(p['value'] for p in patients):.1f}")

# %%
fig, axs = plt.subplots(1, 2, figsize=(13, 4.5))
vals = np.array([p["value"] for p in patients])
cmap = plt.cm.viridis((vals - vals.min()) / (np.ptp(vals) + 1e-9))
for p, col in zip(patients, cmap):
    axs[0].plot(RADII, 100 * p["ovh"], color=col, alpha=0.8)
axs[0].set_xlabel("odległość od PTV r [mm]"); axs[0].set_ylabel(f"% objętości {ORGAN} w odległości ≤ r")
axs[0].set_title(f"OVH (kolor = {METRIC}: żółty = wysoka dawka)"); axs[0].grid(alpha=0.3)
viz.show_slice(patients[0]["case"], dose=patients[0]["case"].dose, structures=["PTV", ORGAN], ax=axs[1], title="przykładowy plan")
plt.show()

# %% [markdown]
# ## 2. Najprostszy model: jedna liczba z OVH → dawka
# Cecha `r50` = odległość, w której mieści się 50% narządu. Im mniejsza, tym narząd bliżej PTV.

# %%
def r_at(ovh_curve, frac):
    idx = np.nonzero(ovh_curve >= frac)[0]
    return RADII[idx[0]] if len(idx) else RADII[-1]


FEATURE_FRACS = [0.1, 0.5]  # zmień: które punkty OVH są cechami modelu
feats = np.array([[r_at(p["ovh"], f) for f in FEATURE_FRACS] for p in patients])
n_train = int(0.7 * N_PATIENTS)
Xtr, Xte, ytr, yte = feats[:n_train], feats[n_train:], vals[:n_train], vals[n_train:]
reg = LinearRegression().fit(Xtr, ytr)
pred = reg.predict(Xte)
mae = mean_absolute_error(yte, pred)
fig, axs = plt.subplots(1, 2, figsize=(12, 4.5))
axs[0].scatter(feats[:, -1], vals, c=["C0"] * n_train + ["C1"] * (N_PATIENTS - n_train))
axs[0].set_xlabel(f"r{int(100 * FEATURE_FRACS[-1])} [mm]"); axs[0].set_ylabel(f"{ORGAN} {METRIC}"); axs[0].set_title("geometria vs dawka (niebieskie = uczące)")
axs[1].scatter(yte, pred, color="C1"); lim = [min(vals.min(), pred.min()), max(vals.max(), pred.max())]
axs[1].plot(lim, lim, "k--", lw=0.8); axs[1].set_xlabel("dawka w planie"); axs[1].set_ylabel("dawka przewidziana")
axs[1].set_title(f"zbiór testowy: średni błąd bezwzględny = {mae:.2f}")
for ax in axs: ax.grid(alpha=0.3)
plt.show()

# %% [markdown]
# ## 3. Predykcja całego DVH
# Dla kilku poziomów objętości (D10%, D30%, …) budujemy osobne regresje z tych samych cech OVH
# i rysujemy przewidziane DVH dla nowego pacjenta.

# %%
VOL_LEVELS = [5, 10, 20, 30, 50, 70, 90]
Dx = np.array([[metrics.dose_at_volume(p["case"].dose, p["case"].structures[ORGAN], v) for v in VOL_LEVELS] for p in patients])
models_dvh = [LinearRegression().fit(Xtr, Dx[:n_train, j]) for j in range(len(VOL_LEVELS))]
resid_sd = [np.std(Dx[:n_train, j] - m.predict(Xtr)) for j, m in enumerate(models_dvh)]
TEST_PATIENT = n_train  # zmień na inny indeks ≥ n_train
pred_D = np.array([m.predict(feats[[TEST_PATIENT]])[0] for m in models_dvh])
c = patients[TEST_PATIENT]["case"]
b, v = metrics.dvh(c.dose, c.structures[ORGAN])
plt.figure(figsize=(7, 4.5))
plt.plot(b, v, label="DVH z planu")
plt.errorbar(pred_D, VOL_LEVELS, xerr=2 * np.array(resid_sd), fmt="o", color="C3", label="predykcja KBP ± 2 SD")
plt.xlabel("Dawka [Gy]"); plt.ylabel("Objętość [%]"); plt.title(f"{ORGAN}: DVH przewidziany vs z planu"); plt.grid(alpha=0.3); plt.legend(); plt.show()

# %% [markdown]
# ## 4. KBP jako kontrola jakości: wykrywanie planów do poprawy
# Symulujemy kilka planów zrobionych „gorzej” — wiązki ustawione tak, że przechodzą przez narząd.
# Model KBP nie wie, jak plan zrobiono — porównuje dawkę z tym, czego **można się spodziewać** przy tej geometrii.
#
# **Zadanie 2 (zmień parametr).** `ALERT_SD` — ile odchyleń standardowych ponad predykcję uznajemy za alarm.
# Ile planów oznaczysz przy 1, 2, 3 SD? Co to znaczy dla obciążenia pracą fizyków?

# %%
ALERT_SD = 2.0
BAD_ANGLES = (0, 40, 80, 120, 180)  # gorszy układ wiązek
sd_main = np.std(ytr - reg.predict(Xtr))
rows = []
for k, p in enumerate(patients[n_train:]):
    case_k = p["case"]
    bad = k % 3 == 0  # co trzeci plan testowy jest „gorszy”
    d = dose_model.compute_dose(case_k.structures["PTV"], case_k.spacing, body=case_k.structures["BODY"], angles=BAD_ANGLES) if bad else case_k.dose
    actual = metrics.evaluate_metric(d, case_k.structures[ORGAN], case_k.spacing, METRIC)
    expected = reg.predict(feats[[n_train + k]])[0]
    rows.append({"pacjent": case_k.case_id, "plan": "gorszy" if bad else "standard", f"{METRIC} w planie": round(actual, 2),
                 "przewidziane": round(expected, 2), "różnica [SD]": round((actual - expected) / sd_main, 1),
                 "alarm KBP": "TAK" if actual - expected > ALERT_SD * sd_main else ""})
qa = pd.DataFrame(rows)
print(f"Wykryte gorsze plany: {((qa['plan'] == 'gorszy') & (qa['alarm KBP'] == 'TAK')).sum()} z {(qa['plan'] == 'gorszy').sum()}; "
      f"fałszywe alarmy: {((qa['plan'] == 'standard') & (qa['alarm KBP'] == 'TAK')).sum()}")
qa

# %% [markdown]
# ## Zadania „zmień i zinterpretuj” — podsumowanie
# 1. (sekcja 1–2) Zmień `N_PATIENTS` na 15 i 60. Jak zmienia się błąd predykcji? Ile planów potrzeba, by model był użyteczny?
# 2. (sekcja 2) Zmień `ORGAN` na `"SpinalCord"` i `METRIC` na `"D0.03cc"`. Czy OVH równie dobrze przewiduje dawkę maksymalną? Dlaczego?
# 3. (sekcja 2) Dodaj do `FEATURE_FRACS` wartość 0.9. Czy więcej cech zawsze pomaga?
# 4. (sekcja 4) Gdyby wszystkie plany uczące były „gorsze”, czy model wykryłby problem? Co z tego wynika dla wyboru planów uczących?
#
# ## Pytania do dyskusji
# - Kto „uczy” model KBP w zakładzie i kto odpowiada za dobór planów uczących?
# - Czy model z innego ośrodka (inna technika, inne konwencje konturowania) będzie trafny u nas?
# - KBP przewiduje, że rdzeń dostanie 30 Gy, a plan ma 38 Gy (limit 45 Gy). Plan spełnia limit — poprawiać czy nie?
# - Czy automatyczne planowanie zmieni rolę elektroradiologa/dozymetrysty? Jakie nowe zadania się pojawią?
#
# ## Zadanie dodatkowe dla chętnych (programistyczne)
# **A.** Zastąp regresję liniową modelem k najbliższych sąsiadów na całej krzywej OVH (`KNeighborsRegressor`) i porównaj błąd w walidacji krzyżowej.
#
# **B.** Zbuduj model przewidujący **mapę dawki 3D** jako funkcję odległości od PTV (np. średnia dawka w „pierścieniach” 0–5, 5–10, … mm,
# uczona na kohorcie) i policz z niej DVH dowolnego narządu. Porównaj z sekcją 3.
#
# **C.** Pobierz zbiór **OpenKBP** (AAPM 2020, https://github.com/ababier/open-kbp; zweryfikuj licencję) i powtórz analizę OVH → DVH
# dla ślinianek na prawdziwych planach głowy i szyi.

# %%
# Miejsce na Twój kod (zadanie dodatkowe)
