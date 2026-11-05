# %% [markdown]
# # Blok 0 (15 min). Jak korzystać z Google Colab
#
# **Cel.** W 15 minut nauczysz się wszystkiego, czego potrzebujesz na zajęciach: uruchamiać komórki, zmieniać parametry,
# radzić sobie z zawieszeniem i błędami, włączać GPU i przełączać notatnik w **tryb awaryjny**. Nie trzeba umieć programować.
#
# | Co | Jak |
# |---|---|
# | Uruchom komórkę | kliknij ▶ po lewej stronie komórki albo **Shift+Enter** |
# | Uruchom wszystko od początku | *Środowisko wykonawcze → Uruchom wszystko* (Ctrl+F9) |
# | Zatrzymaj długie liczenie | ■ przy komórce albo *Środowisko wykonawcze → Przerwij wykonywanie* (Ctrl+M I) |
# | „Wszystko się zepsuło” | *Środowisko wykonawcze → Uruchom ponownie sesję*, potem *Uruchom wszystko* |
# | Zachowaj swoje zmiany | *Plik → Zapisz kopię na Dysku* (inaczej zmiany przepadną) |
# | Włącz GPU | *Środowisko wykonawcze → Zmień typ środowiska wykonawczego → T4 GPU* |
#
# Komórki są dwóch rodzajów: **tekstowe** (jak ta) i **z kodem** (szare pole z ▶). Kolejność ma znaczenie:
# komórka „widzi” to, co policzyły komórki uruchomione **wcześniej**.

# %% [markdown]
# ## Krok 1. Twoja pierwsza komórka
# Kliknij w komórkę poniżej i naciśnij **Shift+Enter**. Pod komórką pojawi się wynik.

# %%
print("Działa! Witaj na kursie „AI w radioterapii”.")
2 + 2

# %% [markdown]
# ## Krok 2. Przygotowanie środowiska (jak w każdym notatniku kursu)
# Każdy notatnik kursu zaczyna się od takiej komórki. Pobiera kod kursu i sprawdza, czy wszystko jest gotowe.
# Pierwsze uruchomienie w Colab trwa ok. 30–60 s.

# %%
# INCLUDE: _setup.py

# %% [markdown]
# ## Krok 3. Zmień parametr i uruchom ponownie
# W notatnikach parametry do zmiany są **WIELKIMI LITERAMI** na górze komórki, z komentarzem po `#`.
#
# **Zadanie.** Zmień `PRESCRIPTION_GY` na 50, a `N_FRACTIONS` na 25. Uruchom komórkę ponownie (Shift+Enter). Co się zmieniło?

# %%
PRESCRIPTION_GY = 60   # dawka całkowita [Gy] — zmień mnie
N_FRACTIONS = 30       # liczba frakcji — zmień mnie
print(f"Dawka na frakcję: {PRESCRIPTION_GY / N_FRACTIONS:.2f} Gy")
fractions = np.arange(1, N_FRACTIONS + 1)
plt.figure(figsize=(6, 3))
plt.step(fractions, fractions * PRESCRIPTION_GY / N_FRACTIONS, where="post")
plt.xlabel("frakcja"); plt.ylabel("dawka skumulowana [Gy]"); plt.grid(alpha=0.3); plt.title("Dawka narasta z każdą frakcją")
plt.show()

# %% [markdown]
# ## Krok 4. Obrazek i suwak
# Przesuń suwak — obraz zmienia się bez ponownego uruchamiania komórki. Tak przeglądamy przekroje CT na zajęciach.

# %%
case = data.load_case(0, "synthetic")
viz.slice_browser(case, structures=["Heart", "Lung_L", "Lung_R", "SpinalCord"])

# %% [markdown]
# ## Krok 5. Błąd to nie katastrofa
# Poniższa komórka **celowo** zawiera błąd. Uruchom ją i przeczytaj **ostatnią linię** czerwonego komunikatu — tam jest przyczyna
# (tu: `NameError: name 'dawka_calkowita' is not defined` = użyto nazwy, której nikt wcześniej nie zdefiniował).
#
# Najczęstsze przyczyny błędów na zajęciach:
# 1. **Komórki uruchomione nie po kolei** → *Uruchom wszystko*.
# 2. **Literówka przy zmianie parametru** (np. przecinek zamiast kropki: `2,5` zamiast `2.5`, brak cudzysłowu w `"lung"`).
# 3. **Sesja wygasła** (przerwa, zamknięty laptop) → *Uruchom ponownie sesję* → *Uruchom wszystko*.

# %% tags=["raises-exception"]
print(dawka_calkowita)

# %% [markdown]
# ## Krok 6. Gdy coś się zawiesi
# Komórka poniżej liczy „bardzo długo” (tu: 5 sekund, żeby nie tracić czasu). Gdy komórka się kręci (ikonka ⟳), możesz ją
# **przerwać** przyciskiem ■ albo *Przerwij wykonywanie*. Zwykłe obliczenia w kursie trwają od ułamka sekundy do ok. 30 s;
# jeśli coś trwa > 2 min, przerwij i zapytaj prowadzącego.

# %%
import time
for i in range(5):
    print(f"liczę... {i + 1}/5", flush=True)
    time.sleep(1)
print("Gotowe.")

# %% [markdown]
# ## Krok 7. Czy mam GPU?
# GPU przydaje się tylko w bloku 3 (TotalSegmentator na żywo). Wszystkie inne notatniki działają na zwykłym CPU.
# Jeśli Colab odmówi przydziału GPU (bywa w godzinach szczytu) — nic się nie stało, notatnik użyje gotowych wyników.

# %%
from rtcourse import autoseg
print("GPU dostępne:", "TAK" if autoseg.has_gpu() else "NIE (to w porządku — tryb CPU / gotowe wyniki)")

# %% [markdown]
# ## Krok 8. Tryb awaryjny
# Jeśli nie działa internet, pakiet danych się nie pobiera albo cokolwiek „dziwnego” dzieje się z danymi, w **pierwszej komórce
# notatnika** (Krok 2) zmień:
# ```python
# MODE = os.environ.get("RTCOURSE_MODE", "auto")
# ```
# na
# ```python
# MODE = "synthetic"
# ```
# i uruchom wszystko od nowa. Notatnik użyje syntetycznego fantomu wygenerowanego w kodzie — ćwiczenia działają tak samo.

# %%
for mode in ["synthetic", MODE]:
    c = data.load_case(0, mode, verbose=False)
    print(f"MODE = {mode!r:12} → źródło danych: {c.source}, {c.case_id}")

# %% [markdown]
# ## Krok 9. Zapisz swoją pracę
# *Plik → Zapisz kopię na Dysku*. Kopia pojawi się w folderze **Colab Notebooks** na Twoim Dysku Google.
# Bez tego zmiany znikną po zamknięciu karty.
#
# ### Sprawdź się (2 min)
# 1. Jak uruchomić wszystkie komórki od początku?
# 2. Co zrobisz, gdy komórka liczy się od 3 minut?
# 3. Gdzie zmienić tryb na awaryjny i jak on się nazywa w kodzie?
# 4. Gdzie szukać przyczyny błędu w czerwonym komunikacie?
#
# ### Dla chętnych
# Otwórz panel **Pliki** (ikona folderu po lewej). Znajdź folder `rt_dicom_example` (pojawi się po bloku 1) albo wgraj dowolny plik.
# Kaggle jako alternatywa: instrukcja w README repozytorium.
