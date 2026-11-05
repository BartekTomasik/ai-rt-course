# P2. Protokół odbioru (commissioning) narzędzia AI w zakładzie

## Pytanie
Jak powinien wyglądać protokół odbioru i kontroli jakości narzędzia AI (np. autokonturowania OAR klatki piersiowej)
w konkretnym zakładzie radioterapii — zanim zostanie użyte u pierwszego pacjenta i później, w codziennej pracy?

## Co robicie
1. Opiszcie narzędzie (przeznaczenie, wersja, dane wejściowe/wyjściowe, status regulacyjny — ogólnie, wg karty producenta).
2. Napiszcie protokół odbioru wg szablonu z [notatnika bloku 7](../notebooks/07_monitorowanie_qa.ipynb) (część A):
   zakres, odpowiedzialności, zbiór testowy (ile przypadków, jak dobranych), metryki i **kryteria akceptacji**,
   testy integracji (DICOM, nazwy struktur, UID), scenariusze błędów, szkolenie personelu, dokumentacja.
3. Zaplanujcie **monitorowanie po wdrożeniu**: co mierzyć (np. odsetek poprawianych konturów, czas korekty), jak często,
   jakie progi uruchamiają działanie, jak wykrywać dryf (zmiana tomografu, protokołu, populacji pacjentów).
4. Analiza ryzyka (np. uproszczona FMEA: 8–10 trybów awarii z oceną S/O/D i działaniami).
5. (Opcjonalnie) przetestujcie kryteria i monitorowanie w symulacji z notatnika 7 oraz na danych kursu (notatnik 3).

## Wynik
Protokół (3–4 strony) gotowy do adaptacji przez zakład + tabela FMEA + plan monitorowania.

## Kryteria merytoryczne (50 pkt)
| Kryterium | Pkt |
|---|---|
| Kompletność protokołu (zakres, role, zbiór testowy, metryki, kryteria, dokumentacja) | 15 |
| Kryteria akceptacji: mierzalne, uzasadnione literaturą/danymi | 10 |
| Analiza ryzyka (FMEA): realistyczne tryby awarii, sensowne działania | 15 |
| Plan monitorowania i reakcji na dryf | 10 |

## Literatura startowa
- Vandewinckele L. i wsp. Overview of artificial intelligence-based applications in radiotherapy: Recommendations for
  implementation and quality assurance. *Radiother Oncol* 2020;153:55–66.
- Hurkmans C. i wsp. A joint ESTRO and AAPM guideline for development, clinical validation and reporting of artificial
  intelligence models in radiation therapy. *Radiother Oncol* 2024;197:110345.
- Baroudi H. i wsp. Automated contouring and planning in radiation therapy: what is 'clinically acceptable'?
  *Diagnostics* 2023;13(4):667.

Zweryfikujcie dane bibliograficzne w PubMed.
