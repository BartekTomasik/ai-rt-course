# Sylabus (szkic): Sztuczna inteligencja w radioterapii

> Szkic do uzgodnienia z koordynatorem kierunku i dostosowania do formularza sylabusa GUMed (kody efektów kierunkowych do uzupełnienia).

| | |
|---|---|
| Kierunek / poziom | Elektroradiologia, studia II stopnia |
| Rok akademicki | 2026/2027 |
| Forma zajęć | ćwiczenia / seminarium praktyczne, 30 h (10 × 3 h) |
| Punkty ECTS | do ustalenia (propozycja: 2) |
| Język | polski (literatura częściowo angielska) |
| Prowadzący | [uzupełnić] |
| Wymagania wstępne | podstawy radioterapii, fizyki medycznej i technik obrazowania (CT); **programowanie nie jest wymagane** |

## Cele przedmiotu
1. Zapoznanie z zastosowaniami AI w radioterapii: autosegmentacja, synthetic CT, radioterapia adaptacyjna, automatyczne planowanie, LLM.
2. Nabycie praktycznej umiejętności pracy z danymi DICOM-RT i oceny wyników narzędzi AI (metryki geometryczne i dawkowe).
3. Przygotowanie do udziału we wdrażaniu i kontroli jakości narzędzi AI w zakładzie radioterapii.
4. Rozwinięcie krytycznej oceny publikacji i świadomości regulacyjnej (MDR, AI Act, RODO).

## Efekty uczenia się
**Wiedza — absolwent zna i rozumie:**
- W1: strukturę i powiązania obiektów DICOM-RT (CT, RTSTRUCT, RTPLAN, RTDOSE) oraz układ współrzędnych pacjenta;
- W2: podstawowe pojęcia uczenia maszynowego (zbiór uczący/walidacyjny/testowy, przeuczenie, wyciek danych) i ich konsekwencje kliniczne;
- W3: metody oceny autosegmentacji (Dice, HD95, surface Dice) i ich ograniczenia;
- W4: zasady działania synthetic CT, radioterapii adaptacyjnej i planowania opartego na wiedzy (KBP);
- W6: model liniowo-kwadratowy (BED, EQD2), jego założenia i ograniczenia przy hipofrakcjonacji i reirradiacji;
- W5: ogólne wymagania prawne dotyczące AI w medycynie (MDR, AI Act, RODO) oraz standardy raportowania (TRIPOD+AI, CLAIM).

**Umiejętności — absolwent potrafi:**
- U1: otworzyć plan leczenia w formacie DICOM-RT, sprawdzić jego spójność i zwizualizować kontury i rozkład dawki;
- U2: porównać kontur automatyczny z referencyjnym, obliczyć i zinterpretować metryki zgodności;
- U3: ocenić wpływ różnic konturu na DVH i spełnienie limitów dawek;
- U7: przeliczyć dawki i limity dawek między schematami frakcjonowania (BED/EQD2), także voxel po vokselu;
- U4: zaprojektować protokół odbioru i monitorowania narzędzia AI z kryteriami akceptacji oraz zinterpretować kartę kontrolną (Shewhart, CUSUM);
- U5: bezpiecznie użyć LLM do pracy z tekstem i systematycznie ocenić błędy odpowiedzi;
- U6: krytycznie ocenić publikację o AI wg list TRIPOD+AI / CLAIM.

**Kompetencje społeczne — absolwent jest gotów do:**
- K1: krytycznej oceny wyników narzędzi AI i nieprzyjmowania ich bez weryfikacji (świadomość „automation bias”);
- K2: współpracy w zespole interdyscyplinarnym (lekarz, fizyk, elektroradiolog, IT) przy wdrażaniu nowych technologii;
- K3: przestrzegania zasad ochrony danych pacjentów i odpowiedzialności zawodowej przy pracy z AI.

## Treści programowe (10 × 3 h)
0. (15 min na początku bloku 1) Jak korzystać z Google Colab — notatnik wprowadzający.
1. DICOM w radioterapii (CT, RTSTRUCT, RTPLAN, RTDOSE) — notatnik.
2. Jak „widzi” model: klasyfikator jakości obrazu, przeuczenie, podział danych, wyciek danych — notatnik.
3. Autosegmentacja (TotalSegmentator) i metryki zgodności — notatnik.
4. Kontur a dawka: DVH, limity dawek — notatnik; **4b.** Frakcjonowanie: BED/EQD2, hipofrakcjonacja, przeliczanie limitów,
   przerwy w leczeniu, reirradiacja — notatnik (wariant: 4 i 4b po 1,5 h w jednym bloku albo 4b zamiast części bloku 6 / jako praca własna).
5. Synthetic CT, CBCT i radioterapia adaptacyjna — warsztat.
6. Automatyczne planowanie i predykcja dawki (KBP, OVH) — notatnik.
7. Wdrożenie i QA modeli AI: odbiór z kryteriami akceptacji, monitorowanie dryfu (karta kontrolna, CUSUM) — notatnik z symulacją + praca w grupach.
8. LLM w codziennej pracy: zastosowania, halucynacje, RODO — warsztat.
9. Regulacje (MDR, AI Act) i krytyczna ocena publikacji (TRIPOD+AI, CLAIM) — warsztat.
10. Prezentacje projektów zespołowych.

## Metody dydaktyczne
Ćwiczenia z notatnikami Jupyter (Google Colab, bez instalacji), praca w grupach, studia przypadków, dyskusja, projekt zespołowy.
Dane: wyłącznie publiczne (TCIA) lub syntetyczne.

## Forma i warunki zaliczenia
- Zaliczenie na ocenę. Obecność: dopuszczalna 1 nieobecność (odrobienie: wykonanie notatnika/karty ćwiczeń z danego bloku).
- **Projekt zespołowy (2–3 os.)** — 80% oceny: raport + prezentacja, rubryka 100 pkt (karty projektów P1–P4).
- **Aktywność / karty ćwiczeń** — 20% oceny (wykonanie zadań „zmień i zinterpretuj”, udział w dyskusji).
- Bonus do +10 pkt: zadania dodatkowe, wyzwanie z rankingiem.
- Opcjonalnie: krótki test jednokrotnego wyboru (20–25 pytań z banku 40 pytań powiązanych z efektami W/U/K) jako część oceny aktywności lub warunek dopuszczenia do prezentacji — do decyzji prowadzącego.
- Skala: ≥ 91% bdb, 81–90% db+, 71–80% db, 61–70% dst+, 51–60% dst, < 51% ndst (do dostosowania do regulaminu).
- Weryfikacja efektów: W1–W6 — pytania w trakcie zajęć i obrona projektu; U1–U7 — notatniki, karty ćwiczeń, projekt; K1–K3 — obserwacja pracy w grupie, projekt.

## Wymagania na pierwsze zajęcia
- **Laptop** z aktualną przeglądarką (Chrome/Firefox/Edge) i ładowarką. Tablet/telefon nie wystarczy.
- **Konto Google** (do Google Colab) — zalecane osobne konto do nauki; opcjonalnie konto Kaggle (zapas).
- Nie trzeba niczego instalować ani umieć programować.

## Literatura
**Podstawowa**
1. Wasserthal J i wsp. TotalSegmentator: robust segmentation of 104 anatomic structures in CT images. *Radiol Artif Intell* 2023;5(5):e230024.
2. Vandewinckele L i wsp. Overview of artificial intelligence-based applications in radiotherapy: recommendations for implementation and quality assurance. *Radiother Oncol* 2020;153:55–66.
3. Hurkmans C i wsp. A joint ESTRO and AAPM guideline for development, clinical validation and reporting of artificial intelligence models in radiation therapy. *Radiother Oncol* 2024;197:110345.
4. Collins GS i wsp. TRIPOD+AI statement. *BMJ* 2024;385:e078378.
5. Yang J i wsp. Autosegmentation for thoracic radiation treatment planning: a grand challenge at AAPM 2017. *Med Phys* 2018;45(10):4568–4581.

**Uzupełniająca**
6. Nikolov S i wsp. Clinically applicable segmentation of head and neck anatomy for radiotherapy: deep learning algorithm development and validation study. *J Med Internet Res* 2021;23(7):e26151 (surface Dice).
7. Tejani AS i wsp. Checklist for Artificial Intelligence in Medical Imaging (CLAIM): 2024 update. *Radiol Artif Intell* 2024;6(4):e240300.
8. Babier A i wsp. OpenKBP: the open-access knowledge-based planning grand challenge and dataset. *Med Phys* 2021;48(9):5549–5561.
9. Marks LB i wsp. Use of normal tissue complication probability models in the clinic (QUANTEC). *Int J Radiat Oncol Biol Phys* 2010;76(3 Suppl):S10–S19.
10. Fowler JF. The linear-quadratic formula and progress in fractionated radiotherapy. *Br J Radiol* 1989;62(740):679–694.
11. Rozporządzenie (UE) 2017/745 (MDR) oraz Rozporządzenie (UE) 2024/1689 (AI Act) — teksty w EUR-Lex.

> Dane bibliograficzne sprawdzić w PubMed przed wpisaniem do systemu sylabusów.
