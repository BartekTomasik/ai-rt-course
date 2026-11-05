# Konspekt kursu: „Sztuczna inteligencja w radioterapii”
**Elektroradiologia, studia II stopnia · 30 h (10 × 3 h) · rok 2026/27 · prowadzący: [uzupełnić], GUMed**

**Cel.** Praktyczne przygotowanie elektroradiologów do pracy z narzędziami AI w zakładzie radioterapii: rozumienie, co robi
narzędzie, jak ocenić jego wynik, jak je bezpiecznie wdrożyć i kontrolować. Kurs jest praktyczny, ale **nie wymaga programowania**.

**Forma.** Ćwiczenia w przeglądarce (Google Colab — bez instalacji, na laptopach studentów) i warsztaty w grupach.
Wyłącznie dane publiczne (The Cancer Imaging Archive) i syntetyczne — bez danych pacjentów.

| # | Blok (3 h) | Co studenci robią |
|---|---|---|
| 0 | Colab (15 min) | uruchamiają komórki, zmieniają parametr, tryb awaryjny, GPU — przed blokiem 1 |
| 1 | DICOM w RT | otwierają plan (CT, kontury, plan, dawka), sprawdzają spójność, oglądają izodozy i DVH |
| 2 | Jak „widzi” model | uczą klasyfikator jakości obrazu, widzą przeuczenie i wyciek danych na żywo |
| 3 | Autosegmentacja | porównują TotalSegmentator z konturem ręcznym (Dice, HD95, surface Dice), katalog błędów |
| 4 | Kontur a dawka | sprawdzają, jak błąd konturu zmienia DVH i spełnienie limitów dawek |
| 4b | Frakcjonowanie | przeliczają BED/EQD2, limity przy hipofrakcjonacji, DVH w EQD2, sumę dawek przy reirradiacji |
| 5 | sCT, CBCT, ART | warsztat: przepływ pracy radioterapii adaptacyjnej, rola elektroradiologa |
| 6 | Automatyczne planowanie | budują prostą predykcję dawki z geometrii (KBP) i używają jej do QA planu |
| 7 | Wdrożenie i QA AI | ustalają kryteria akceptacji, symulują rok monitorowania (karta kontrolna, CUSUM), oceniają aktualizację modelu |
| 8 | LLM w pracy | systematycznie oceniają błędy odpowiedzi LLM; RODO — co wolno wkleić |
| 9 | Regulacje i publikacje | MDR / AI Act (ogólnie); ocena pracy wg TRIPOD+AI / CLAIM |
| 10 | Prezentacje | prezentacje projektów zespołowych |

**Zaliczenie.** Projekt zespołowy 2–3 os. (80%; do wyboru: walidacja autosegmentacji z analizą dawkową, protokół odbioru
narzędzia AI, LLM w praktyce z oceną ryzyk, krytyczna ocena publikacji) + aktywność na zajęciach (20%).
Opcjonalne wyzwanie z rankingiem dla chętnych (punkty bonusowe).

**Efekty (skrót).** Student zna strukturę DICOM-RT, podstawy uczenia maszynowego i metody oceny AI; potrafi ocenić autosegmentację
geometrycznie i dawkowo, zaprojektować protokół odbioru narzędzia AI, bezpiecznie korzystać z LLM i krytycznie czytać publikacje;
jest gotów do krytycznej, odpowiedzialnej pracy z AI w zespole interdyscyplinarnym.

**Wymagania techniczne.** Laptop z przeglądarką, konto Google, dostęp do Wi-Fi (dane zajęciowe ok. 100–300 MB pobierane raz;
w razie problemów notatniki działają w trybie awaryjnym bez internetu po uruchomieniu). Sala: gniazdka zasilania, rzutnik.

**Dodatkowa wartość.** Materiały w otwartym repozytorium; kurs pozwala zidentyfikować studentów zainteresowanych pracą badawczą
(zadania dodatkowe, wyzwanie) — możliwość dalszej współpracy w zespole naukowym.
