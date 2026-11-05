# %% [markdown]
# # Blok 7. Wdrożenie i QA modeli AI: odbiór (commissioning) i monitorowanie dryfu
#
# **Cel kliniczny.** Narzędzie do autosegmentacji zostało kupione i wdrożone. Skąd wiadomo, że (1) działa wystarczająco dobrze
# **u nas** przed pierwszym pacjentem i (2) nadal działa dobrze po pół roku — po zmianie protokołu CT, wymianie tomografu
# albo aktualizacji modelu przez producenta? Odpowiedzią są **kryteria akceptacji** przy odbiorze i **monitorowanie** w rutynie.
#
# ### Krótka teoria
# - **Odbiór (commissioning):** test na lokalnym zbiorze (20–50 przypadków), metryki + ocena kliniczna, kryteria ustalone **przed** testem.
# - **Monitorowanie:** co tydzień porównujemy kontur AI z konturem zatwierdzonym przez człowieka (po korekcie).
#   Jeśli korekty rosną, model „dryfuje” — zwykle dlatego, że zmieniły się **dane wejściowe**, a nie sam model.
# - **Karta kontrolna Shewharta:** średnia z okresu bazowego ± 3 SD; punkt poza granicą = alarm. Dobra na duże, nagłe zmiany.
# - **CUSUM** (suma skumulowana): sumuje małe odchylenia w dół; wykrywa **niewielkie, ale trwałe** pogorszenie szybciej niż Shewhart.
# - Każda **aktualizacja modelu** = ponowny (choćby skrócony) odbiór.
#
# Dane są **symulowane**: „kontury AI” to kontury referencyjne fantomów z błędami losowanymi z określonego „reżimu”
# (`rtcourse.monitoring.REGIMES`). Notatnik działa bez internetu i bez GPU (ok. 30 s).

# %%
# INCLUDE: _setup.py

# %%
from rtcourse import monitoring as mon

pool = mon.make_pool(10, seed=0)  # 10 syntetycznych „pacjentów” (mała rozdzielczość = szybkie liczenie)
print("Reżimy błędów w symulacji:")
for k, v in mon.REGIMES.items():
    print(" -", k, "|", {o: list(p) for o, p in v.items()})

# %% [markdown]
# ## Część A. Odbiór narzędzia: kryteria akceptacji
# Mamy 20 lokalnych przypadków testowych. Zanim spojrzysz na wyniki, **zapisz kryteria** w słowniku `ACCEPTANCE`.
#
# **Zadanie 1 (zmień parametr).** Ustal kryteria dla serca i przełyku (mediana Dice, 90. percentyl HD95, najgorszy przypadek).
# Uzasadnij je (np. zmiennością między obserwatorami, wynikami z bloku 3, wpływem na dawkę z bloku 4). Czy model v1 przechodzi odbiór?

# %%
ACCEPTANCE = {
    "Heart": {"Dice_median_min": 0.90, "HD95_p90_max": 8.0, "Dice_min_case": 0.85},
    "Esophagus": {"Dice_median_min": 0.75, "HD95_p90_max": 15.0, "Dice_min_case": 0.50},
}
rng = np.random.default_rng(1)
commissioning = pd.DataFrame([{"przypadek": i, **r} for i in range(20)
                              for r in mon.simulate_case(pool[i % len(pool)], mon.REGIMES["model v1 (wdrożenie)"], rng)])
res_v1 = mon.evaluate_acceptance(commissioning, ACCEPTANCE)
print("Decyzja dla modelu v1:", "ODBIÓR POZYTYWNY" if (res_v1.wynik == "SPEŁNIONE").all() else "ODBIÓR NEGATYWNY / DO WYJAŚNIENIA")
res_v1

# %%
fig, axs = plt.subplots(1, 2, figsize=(11, 4))
for ax, col in zip(axs, ["Dice", "HD95_mm"]):
    commissioning.boxplot(column=col, by="organ", ax=ax)
    ax.set_title(col); ax.set_xlabel("")
plt.suptitle("Odbiór modelu v1 — 20 przypadków lokalnych"); plt.tight_layout(); plt.show()

# %% [markdown]
# ### Protokół odbioru — szablon do pracy w grupach (20 min)
# Uzupełnij (na kartce lub w komórce Markdown poniżej). Tabela z wynikami powyżej to sekcja 5.
#
# | Sekcja | Do uzupełnienia |
# |---|---|
# | 1. Identyfikacja | producent, wersja, data, status regulacyjny (oznakowanie CE wg MDR, klasa — z dokumentacji) |
# | 2. Zespół i odpowiedzialności | kto testuje, kto zatwierdza, kto szkoli (lekarz, fizyk, elektroradiolog, IT) |
# | 3. Testy integracji | przesył DICOM, nazwy struktur (słownik zakładu, np. TG-263), właściwa seria CT/UID, czas działania, zachowanie przy błędzie |
# | 4. Zbiór testowy | liczba przypadków, kryteria doboru, przypadki trudne (implanty, atelektaza, nietypowa anatomia), kto rysuje referencję |
# | 5. Metryki i **kryteria akceptacji** | Twój słownik `ACCEPTANCE` + ocena kliniczna (skala 1–4) + czas korekty |
# | 6. Ocena dawkowa | na ilu planach, jakie metryki (blok 4), dopuszczalna różnica |
# | 7. Szkolenie | kto, ile, jak sprawdzamy kompetencje; „automation bias” |
# | 8. Procedura kliniczna | kto weryfikuje każdy kontur; dokumentacja korekty; co robić przy awarii |
# | 9. Monitorowanie | co, jak często, progi alarmowe, kto przegląda (część B) |
# | 10. Zmiana wersji | jakie testy powtarzamy przy aktualizacji (część C) |

# %% [markdown]
# ## Część B. Rok w zakładzie: monitorowanie co tydzień
# Symulujemy `N_WEEKS` tygodni pracy; co tydzień `PATIENTS_PER_WEEK` pacjentów. W tygodniu `PROTOCOL_CHANGE_WEEK` zakład zmienia
# protokół CT (kontrast, cieńsze warstwy), a w tygodniu `MODEL_UPDATE_WEEK` producent aktualizuje model.
# **Nikt nie mówi zespołowi QA o tych zmianach** — mają je wykryć karty kontrolne.
#
# **Zadanie 2 (zmień parametr).** Zmień `PATIENTS_PER_WEEK` (2 / 5 / 10) i `BASELINE_WEEKS`. Jak szybko wykrywamy zmianę? Ile jest fałszywych alarmów?

# %%
N_WEEKS = 30
PATIENTS_PER_WEEK = 5
PROTOCOL_CHANGE_WEEK = 12
MODEL_UPDATE_WEEK = 22
BASELINE_WEEKS = 8
events = {PROTOCOL_CHANGE_WEEK: "nowy protokół CT (kontrast, cieńsze warstwy)", MODEL_UPDATE_WEEK: "model v2 (aktualizacja producenta)"}
qa = mon.simulate_weeks(N_WEEKS, PATIENTS_PER_WEEK, events=events, pool=pool, seed=2)
weekly = qa.groupby(["organ", "week"]).agg(Dice=("Dice", "mean"), HD95_mm=("HD95_mm", "mean")).reset_index()
qa.head()

# %% [markdown]
# ### Karta kontrolna Shewharta i CUSUM
# **Zadanie 3 (zmień parametr).** `K_SIGMA` — szerokość granic (2, 3, 4 SD). `CUSUM_H` — próg alarmu CUSUM.
# Który sposób szybciej wykrywa zmianę protokołu dla serca, a który dla przełyku? Dlaczego?

# %%
K_SIGMA = 3.0
CUSUM_K, CUSUM_H = 0.5, 4.0
summary = []
fig, axs = plt.subplots(2, 2, figsize=(14, 7), sharex=True)
for row, organ in enumerate(["Heart", "Esophagus"]):
    w = weekly[weekly.organ == organ].set_index("week")["Dice"]
    mean, lcl, ucl, sd = mon.shewhart_limits(w.loc[:BASELINE_WEEKS], k=K_SIGMA)
    S, alarm = mon.cusum_lower(w.values, mean, sd, k=CUSUM_K, h=CUSUM_H)
    out = w[w < lcl]
    ax = axs[row, 0]
    ax.plot(w.index, w.values, "o-", ms=4); ax.axhline(mean, color="g"); ax.axhline(lcl, color="r", ls="--")
    ax.plot(out.index, out.values, "rs", label="poza granicą")
    ax.axvspan(0.5, BASELINE_WEEKS + 0.5, color="gray", alpha=0.15, label="okres bazowy")
    for wk, lab in [(PROTOCOL_CHANGE_WEEK, "zmiana protokołu CT"), (MODEL_UPDATE_WEEK, "aktualizacja modelu")]:
        ax.axvline(wk - 0.5, color="k", ls=":"); ax.text(wk - 0.3, ax.get_ylim()[0], lab, fontsize=8, rotation=90, va="bottom")
    ax.set_ylabel(f"{organ}: średni Dice / tydzień"); ax.legend(fontsize=8, loc="lower left"); ax.grid(alpha=0.3)
    ax2 = axs[row, 1]
    ax2.plot(w.index, S, "o-", ms=4, color="C1"); ax2.axhline(CUSUM_H * sd, color="r", ls="--", label="próg CUSUM")
    ax2.set_ylabel("CUSUM (spadek Dice)"); ax2.grid(alpha=0.3); ax2.legend(fontsize=8)
    first_shew = int(out.index[out.index > BASELINE_WEEKS][0]) if (out.index > BASELINE_WEEKS).any() else None
    false_shew = int((out.index < PROTOCOL_CHANGE_WEEK).sum())
    summary.append({"narząd": organ, "zmiana w tygodniu": PROTOCOL_CHANGE_WEEK,
                    "Shewhart: pierwszy alarm": first_shew, "Shewhart: alarmy przed zmianą": false_shew,
                    "CUSUM: pierwszy alarm": None if alarm is None else int(w.index[alarm])})
axs[1, 0].set_xlabel("tydzień"); axs[1, 1].set_xlabel("tydzień")
plt.tight_layout(); plt.show()
pd.DataFrame(summary).set_index("narząd")

# %% [markdown]
# ### Alarmy na poziomie pojedynczego pacjenta
# Oprócz trendu warto oznaczać pojedyncze przypadki do przeglądu (np. HD95 > próg). **Zadanie 4.** Dobierz `CASE_HD95_ALERT_MM`
# tak, by do przeglądu trafiało ≤ 10% przypadków w okresie bazowym. Co to oznacza dla czasu pracy zespołu?

# %%
CASE_HD95_ALERT_MM = 10.0
qa["do przeglądu"] = qa.HD95_mm > CASE_HD95_ALERT_MM
qa["okres"] = np.select([qa.week < PROTOCOL_CHANGE_WEEK, qa.week < MODEL_UPDATE_WEEK], ["model v1", "nowy protokół CT"], "model v2")
qa.pivot_table(index="okres", columns="organ", values="do przeglądu", aggfunc="mean").reindex(["model v1", "nowy protokół CT", "model v2"]).mul(100).round(1)

# %% [markdown]
# ## Część C. Aktualizacja modelu = ponowny odbiór
# Producent wydał model v2 („lepsze serce”). Zanim go włączymy, sprawdzamy go **tymi samymi kryteriami** na tym samym zbiorze.
#
# **Zadanie 5.** Czy v2 przechodzi odbiór? Co z tego, że serce jest lepsze? Jaką decyzję podejmie zespół i co zgłosi producentowi?

# %%
rng = np.random.default_rng(1)
commissioning_v2 = pd.DataFrame([{"przypadek": i, **r} for i in range(20)
                                 for r in mon.simulate_case(pool[i % len(pool)], mon.REGIMES["model v2 (aktualizacja producenta)"], rng)])
res_v2 = mon.evaluate_acceptance(commissioning_v2, ACCEPTANCE)
both = res_v1[["narząd", "kryterium", "wymaganie"]].copy()
both["v1"] = res_v1["wartość"].astype(str) + " " + res_v1["wynik"]
both["v2"] = res_v2["wartość"].astype(str) + " " + res_v2["wynik"]
print("Decyzja dla modelu v2:", "ODBIÓR POZYTYWNY" if (res_v2.wynik == "SPEŁNIONE").all() else "ODBIÓR NEGATYWNY / DO WYJAŚNIENIA")
both

# %% [markdown]
# ## Zadania „zmień i zinterpretuj” — podsumowanie
# 1. (A) Zaostrz kryteria dla przełyku (mediana Dice ≥ 0,85). Czy v1 nadal przechodzi? Co jest ważniejsze: mediana czy najgorszy przypadek?
# 2. (B) Ustaw `PATIENTS_PER_WEEK = 2`. O ile tygodni później wykrywamy zmianę? Co to znaczy dla małego zakładu?
# 3. (B) Ustaw `K_SIGMA = 2`. Ile fałszywych alarmów pojawia się w okresie przed zmianą?
# 4. (B) Ustaw `PROTOCOL_CHANGE_WEEK = 40` (brak zmiany w okresie symulacji). Czy karty kontrolne „milczą”?
# 5. (C) Zaproponuj **skrócony** protokół ponownego odbioru po aktualizacji (ile przypadków, które narządy, jakie kryteria).
#
# ## Pytania do dyskusji
# - Kto w zakładzie powinien dostawać alarm z karty kontrolnej i co robi w ciągu 24 h?
# - Czy wolno wyłączyć narzędzie AI po alarmie? Jaki jest plan awaryjny (konturowanie ręczne, dodatkowe kontrole)?
# - Skąd wziąć kontur „zatwierdzony” do monitorowania bez dodatkowej pracy? (Kontur po korekcie z systemu planowania.)
# - Czy dryf może być „niewidoczny” w Dice, a widoczny w dawce? (blok 4)
# - Producent aktualizuje model automatycznie, w chmurze. Jak zapisać w umowie i procedurze prawo do testu przed włączeniem?
#
# ## Zadanie dodatkowe dla chętnych (programistyczne)
# **A.** Dodaj kartę kontrolną dla **HD95** (wzrost = gorzej → CUSUM „górny”) i porównaj czas wykrycia z kartą dla Dice.
#
# **B.** Zasymuluj 200 lat pracy bez zmian (`PROTOCOL_CHANGE_WEEK` poza zakresem) i oszacuj **średni czas do fałszywego alarmu** (ARL₀)
# dla Shewharta 3 SD i CUSUM (k = 0,5, h = 4). Który jest „spokojniejszy”?
#
# **C.** Napisz funkcję raportu miesięcznego (tabela + wykres) gotowego do wysłania kierownikowi zakładu.

# %%
# Miejsce na Twój kod (zadanie dodatkowe)
