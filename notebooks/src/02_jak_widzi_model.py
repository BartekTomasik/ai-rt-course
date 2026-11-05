# %% [markdown]
# # Blok 2. Jak „widzi” model: klasyfikator jakości obrazu, przeuczenie, wyciek danych
#
# **Cel kliniczny.** Wyobraź sobie narzędzie AI, które automatycznie oznacza obrazy CT z artefaktami
# (np. metal, ruch), zanim trafią do planowania. Zanim mu zaufasz, musisz wiedzieć, **czego model się
# nauczył** i **czy jego wynik jest uczciwie zmierzony**. Najczęstsze pułapki to przeuczenie,
# wyciek danych (te same osoby w zbiorze uczącym i testowym) i „skróty” (model uczy się czegoś innego niż myślimy).
#
# Wszystko robimy na **syntetycznych** przekrojach CT (generowanych w kodzie), więc notatnik działa
# zawsze — bez danych z internetu i bez GPU. Uczenie trwa sekundy.
#
# ### Krótka teoria
# - **Zbiór uczący / walidacyjny / testowy:** uczymy na pierwszym, dobieramy ustawienia na drugim,
#   **raz** raportujemy wynik na trzecim.
# - **Przeuczenie (overfitting):** model świetny na danych uczących, słaby na nowych — „nauczył się na pamięć”.
# - **Wyciek danych (data leakage):** informacja ze zbioru testowego „przecieka” do uczenia — np. przekroje
#   tego samego pacjenta są i w uczącym, i w testowym. Wynik wygląda świetnie, w klinice — rozczarowanie.
# - **Podział na poziomie pacjenta:** wszystkie obrazy jednej osoby idą do **jednego** zbioru.

# %%
# INCLUDE: _setup.py

# %%
from rtcourse import artifacts
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from sklearn.metrics import confusion_matrix, roc_auc_score, ConfusionMatrixDisplay


def to_features(X):
    """Piksele w oknie tkanek miękkich, przeskalowane do ok. 0–1."""
    return (np.clip(X, -200, 400).reshape(len(X), -1) + 200) / 600


def patient_split(y, groups, test_size=0.3, seed=0):
    return next(GroupShuffleSplit(1, test_size=test_size, random_state=seed).split(y, y, groups))

# %% [markdown]
# ## 1. Dane: przekroje z artefaktem metalicznym i bez
# **Zadanie 1 (zmień parametr).** `ARTIFACT` = `"metal"`, `"motion"` albo `"ring"`; `STRENGTH` = siła artefaktu (HU).
# Przy jakiej sile przestajesz widzieć artefakt gołym okiem?

# %%
ARTIFACT = "metal"   # "metal" | "motion" | "ring"
STRENGTH = 150.0     # dla "motion" to przesunięcie w pikselach, np. 3
N_PATIENTS = 40
X, y, groups = artifacts.make_slice_dataset(n_patients=N_PATIENTS, slices_per_patient=8, artifact=ARTIFACT, strength=STRENGTH)
print(f"{len(X)} obrazów od {N_PATIENTS} pacjentów; z artefaktem: {y.mean():.0%}")
fig, axs = plt.subplots(2, 6, figsize=(14, 5))
for ax, i in zip(axs.ravel(), np.r_[np.nonzero(y == 0)[0][:6], np.nonzero(y == 1)[0][:6]]):
    ax.imshow(X[i], cmap="gray", vmin=-160, vmax=240); ax.set_title(f"pacjent {groups[i]}, {'ARTEFAKT' if y[i] else 'ok'}", fontsize=8); ax.axis("off")
plt.tight_layout(); plt.show()

# %% [markdown]
# ## 2. Pierwszy model: regresja logistyczna na pikselach
# Dzielimy dane **na poziomie pacjenta**: 70% pacjentów do uczenia, 30% do testu.

# %%
F = to_features(X)
tr, te = patient_split(y, groups)
model = make_pipeline(StandardScaler(), LogisticRegression(C=0.01, max_iter=3000)).fit(F[tr], y[tr])
p = model.predict_proba(F[te])[:, 1]
print(f"Dokładność — uczący: {model.score(F[tr], y[tr]):.2f} | testowy: {model.score(F[te], y[te]):.2f} | AUC test: {roc_auc_score(y[te], p):.2f}")
ConfusionMatrixDisplay(confusion_matrix(y[te], p > 0.5), display_labels=["ok", "artefakt"]).plot(colorbar=False)
plt.title("Macierz pomyłek (zbiór testowy)"); plt.show()

# %% [markdown]
# ### Jak „widzi” ten model? Mapa wag
# Regresja logistyczna ma jedną wagę na piksel. Czerwone = piksel jasny „głosuje” na artefakt, niebieskie — przeciw.
# Czy model patrzy tam, gdzie są artefakty, czy na anatomię?

# %%
w = model[-1].coef_.reshape(X.shape[1:])
plt.figure(figsize=(4, 4)); lim = np.abs(w).max()
plt.imshow(w, cmap="RdBu_r", vmin=-lim, vmax=lim); plt.colorbar(); plt.title("Wagi modelu"); plt.axis("off"); plt.show()

# %% [markdown]
# ## 3. Przeuczenie na żywo
# Parametr `C` steruje „swobodą” modelu (większe C = słabsza regularyzacja = łatwiej zapamiętać dane).
# Drzewo decyzyjne: większa głębokość = bardziej złożony model.
#
# **Zadanie 2.** Gdzie na wykresie zaczyna się przeuczenie? Który model wybrałbyś/wybrałabyś i dlaczego **nie** ten
# z najlepszym wynikiem na zbiorze uczącym?

# %%
tr2, va = patient_split(y[tr], groups[tr], test_size=0.3, seed=1)
tr2, va = tr[tr2], tr[va]  # walidacja wydzielona z części uczącej; test zostaje nietknięty
Cs = [1e-4, 1e-3, 1e-2, 1e-1, 1, 10, 100]
acc_tr, acc_va = [], []
for C in Cs:
    m = make_pipeline(StandardScaler(), LogisticRegression(C=C, max_iter=3000)).fit(F[tr2], y[tr2])
    acc_tr.append(m.score(F[tr2], y[tr2])); acc_va.append(m.score(F[va], y[va]))
depths = [1, 2, 3, 4, 6, 8, 12, 16]
d_tr, d_va = [], []
for d in depths:
    m = DecisionTreeClassifier(max_depth=d, random_state=0).fit(F[tr2], y[tr2])
    d_tr.append(m.score(F[tr2], y[tr2])); d_va.append(m.score(F[va], y[va]))
fig, axs = plt.subplots(1, 2, figsize=(12, 4))
axs[0].semilogx(Cs, acc_tr, "o-", label="uczący"); axs[0].semilogx(Cs, acc_va, "s-", label="walidacyjny"); axs[0].set_xlabel("C (złożoność)")
axs[1].plot(depths, d_tr, "o-", label="uczący"); axs[1].plot(depths, d_va, "s-", label="walidacyjny"); axs[1].set_xlabel("głębokość drzewa")
for ax, t in zip(axs, ["Regresja logistyczna", "Drzewo decyzyjne"]):
    ax.set_ylabel("dokładność"); ax.set_ylim(0.4, 1.02); ax.grid(alpha=0.3); ax.legend(); ax.set_title(t)
plt.show()

# %% [markdown]
# ### Więcej danych = mniej przeuczenia?
# **Zadanie 3 (zmień parametr).** Zmień `PATIENT_COUNTS`. Ile pacjentów potrzeba, żeby różnica uczący–testowy spadła poniżej 10 punktów procentowych?

# %%
PATIENT_COUNTS = [5, 10, 20, 28]
rows = []
for n in PATIENT_COUNTS:
    pts = np.unique(groups[tr])[:n]
    sel = tr[np.isin(groups[tr], pts)]
    m = make_pipeline(StandardScaler(), LogisticRegression(C=1, max_iter=3000)).fit(F[sel], y[sel])
    rows.append({"pacjentów w uczącym": n, "obrazów": len(sel), "dokł. uczący": m.score(F[sel], y[sel]), "dokł. test": m.score(F[te], y[te])})
pd.DataFrame(rows).round(3)

# %% [markdown]
# ## 4. Wyciek danych: podział po przekrojach vs po pacjentach
# Teraz etykieta dotyczy **pacjenta** (np. „pacjent z endoprotezą” — wszystkie jego przekroje mają tę samą etykietę),
# a sam artefakt jest słaby. Porównujemy dwa sposoby podziału na uczący/testowy:
# - **losowo po przekrojach** (błąd!) — przekroje tego samego pacjenta są w obu zbiorach,
# - **po pacjentach** (poprawnie).
#
# **Zadanie 4.** Który wynik zobaczyłby recenzent w publikacji z błędnym podziałem? Który zobaczysz w klinice?

# %%
LEAK_STRENGTH = 40.0
Xl, yl, gl = artifacts.make_slice_dataset(n_patients=40, slices_per_patient=8, artifact="metal", strength=LEAK_STRENGTH, label_level="patient", seed=1)
Fl = to_features(Xl)
a, b = train_test_split(np.arange(len(yl)), test_size=0.3, random_state=0)
tr_p, te_p = patient_split(yl, gl)
rows = []
for name, make in [("1-NN (najbliższy sąsiad)", lambda: KNeighborsClassifier(1)),
                   ("regresja logistyczna", lambda: make_pipeline(StandardScaler(), LogisticRegression(C=0.01, max_iter=3000)))]:
    rows.append({"model": name,
                 "podział po przekrojach (WYCIEK)": make().fit(Fl[a], yl[a]).score(Fl[b], yl[b]),
                 "podział po pacjentach": make().fit(Fl[tr_p], yl[tr_p]).score(Fl[te_p], yl[te_p])})
shared = len(set(gl[a]) & set(gl[b]))
print(f"Przy podziale po przekrojach {shared} z {len(set(gl))} pacjentów ma obrazy w OBU zbiorach.")
pd.DataFrame(rows).set_index("model").round(3)

# %% [markdown]
# ## 5. „Skrót”: model uczy się znacznika zamiast artefaktu
# W danych uczących obrazy z artefaktem prawie zawsze mają jasny znacznik w rogu (np. opis z innego tomografu,
# na którym robiono pacjentów z protezami). W teście znacznika już nie ma.
#
# **Zadanie 5 (zmień parametr).** Zmień `P_MATCH` (jak często znacznik towarzyszy artefaktowi): 0,5 / 0,8 / 0,99.
# Popatrz na mapę wag.

# %%
P_MATCH = 0.95
rng = np.random.default_rng(0)
Xs, ys, gs = artifacts.make_slice_dataset(n_patients=40, slices_per_patient=8, artifact="metal", strength=60.0, seed=2)
tr_s, te_s = patient_split(ys, gs)
X_train = artifacts.add_corner_marker(Xs[tr_s], ys[tr_s], rng, p_match=P_MATCH)
m_short = make_pipeline(StandardScaler(), LogisticRegression(C=0.01, max_iter=3000)).fit(to_features(X_train), ys[tr_s])
print(f"Dokładność — uczący (ze znacznikiem): {m_short.score(to_features(X_train), ys[tr_s]):.2f} | "
      f"test (bez znacznika): {m_short.score(to_features(Xs[te_s]), ys[te_s]):.2f}")
w = m_short[-1].coef_.reshape(Xs.shape[1:]); lim = np.abs(w).max()
fig, axs = plt.subplots(1, 2, figsize=(9, 4))
axs[0].imshow(X_train[np.argmax(ys[tr_s])], cmap="gray", vmin=-160, vmax=240); axs[0].set_title("obraz uczący z artefaktem")
axs[1].imshow(w, cmap="RdBu_r", vmin=-lim, vmax=lim); axs[1].set_title("wagi modelu — gdzie patrzy?")
for ax in axs: ax.axis("off")
plt.show()

# %% [markdown]
# ## Zadania „zmień i zinterpretuj” — podsumowanie
# 1. (sekcja 1–2) Zmniejszaj `STRENGTH`, aż AUC spadnie poniżej 0,8. Czy Ty nadal widzisz artefakt? Co to mówi o porównaniu „AI vs człowiek”?
# 2. (sekcja 3) Podaj wartość `C` i głębokość drzewa, które wybierasz, i uzasadnij na podstawie zbioru walidacyjnego.
# 3. (sekcja 4) Zwiększ `LEAK_STRENGTH` do 150. Czy różnica między podziałami znika? Dlaczego?
# 4. (sekcja 5) Przy jakim `P_MATCH` model przestaje „ściągać”? Jak w prawdziwym zbiorze mogłyby powstać takie skróty (typ aparatu, szpital, data, opis na obrazie)?
#
# ## Pytania do dyskusji
# - Firma podaje „dokładność 98%”. Jakie 3 pytania zadasz o sposób podziału danych?
# - Zbiór z jednego szpitala, jeden tomograf. Co się może stać po wymianie tomografu w Twoim zakładzie?
# - Kiedy dokładność jest złą miarą (np. artefakty w 2% obrazów)? Co zamiast niej?
# - Czy wolno „dostroić” model na zbiorze testowym, jeśli tylko raz? Dlaczego nie?
#
# ## Zadanie dodatkowe dla chętnych (programistyczne)
# **A. Walidacja krzyżowa po pacjentach.** Użyj `sklearn.model_selection.GroupKFold` i podaj średnią ± SD dokładności.
# Porównaj z `KFold` bez grup.
#
# **B. Mapa wrażliwości (occlusion).** Zasłaniaj kolejne fragmenty obrazu (np. kwadrat 6×6 px wartością −1000 HU)
# i zapisuj spadek prawdopodobieństwa „artefakt”. Narysuj mapę — to prosty odpowiednik Grad-CAM.
#
# **C. Sieć konwolucyjna.** W Colab z GPU zbuduj małą sieć CNN w PyTorch (2 warstwy konwolucyjne) i porównaj z regresją logistyczną
# przy 10 i przy 28 pacjentach w zbiorze uczącym. Kiedy złożony model się opłaca?

# %%
# Miejsce na Twój kod (zadanie dodatkowe)
