# Blok 5. Synthetic CT, CBCT i radioterapia adaptacyjna — karta ćwiczeń

**Forma:** warsztat (demo + praca w grupach 3–4 os.). **Bez trenowania modeli.**

## Cel kliniczny
Zrozumieć, po co w radioterapii tworzy się „syntetyczne CT” (sCT) z MR lub CBCT, jak wpływa to na przepływ pracy
radioterapii adaptacyjnej (ART) i **co zmienia się w pracy elektroradiologa** (akwizycja, kontrola obrazu, decyzje przy stole).

## Krótka teoria (15 min, prowadzący)
- **CBCT** na akceleratorze: dobre do pozycjonowania, ale HU niewiarygodne (promieniowanie rozproszone, artefakty, mniejsze FOV)
  → nie nadaje się wprost do liczenia dawki.
- **sCT z CBCT** (AI: np. sieci typu U-Net/GAN): poprawia HU, by przeliczyć dawkę „dnia” i ocenić, czy plan trzeba adaptować.
- **sCT z MR** (radioterapia „MR-only”): brak rejestracji CT–MR (mniej niepewności), mniej badań; ryzyko: kość, powietrze, implanty.
- **ART online:** obraz dnia → autokontury → (sCT) → reoptymalizacja → QA → leczenie, **z pacjentem na stole** (15–30 min).
  ART offline: replanowanie między frakcjami.
- Ocena sCT: MAE/ME HU (np. w ciele), różnice dawki (gamma, ΔD95 PTV), geometria (kontury kości/powietrza).
- Przykład zbioru otwartego: **SynthRAD2023** (pary MR/CBCT–CT, mózg i miednica; Thummerer i wsp., *Med Phys* 2023).

## Ćwiczenie 1 (25 min). Gdzie sCT może się pomylić?
Każda grupa dostaje jeden scenariusz i wypisuje: (a) jaki błąd HU/geometrii może wystąpić, (b) jak wpłynie na dawkę,
(c) jak elektroradiolog może to zauważyć **przy akwizycji lub przeglądzie obrazu**.

| Scenariusz | Podpowiedź |
|---|---|
| A. Pacjent z endoprotezą biodra, sCT z MR | metal, brak sygnału, przeszacowanie/niedoszacowanie HU |
| B. Gazy w odbytnicy na CBCT dnia (RT prostaty) | powietrze vs tkanka; zmiana anatomii vs błąd modelu |
| C. CBCT z obciętym polem widzenia (otyły pacjent) | truncation; skóra poza FOV |
| D. Dziecko / anatomia rzadka w danych uczących | populacja uczącą vs nasza |
| E. Nowa wersja oprogramowania CBCT po serwisie | dryf danych wejściowych |

## Ćwiczenie 2 (40 min). Przepływ pracy ART online — kto, co, kiedy
Narysujcie (na kartce/flipcharcie) przepływ pracy ART online dla pacjenta z rakiem pęcherza/prostaty.
Dla każdego kroku wpiszcie: **kto** (elektroradiolog, fizyk, lekarz), **czas**, **decyzję**, **co może pójść źle**, **kontrolę**.

Szablon:

| Krok | Kto | Czas [min] | Decyzja / działanie | Co może pójść źle | Kontrola (QA) |
|---|---|---|---|---|---|
| CBCT dnia | | | | | |
| Ocena jakości obrazu | | | | | |
| Autokontury + korekta | | | | | |
| sCT / przeliczenie dawki | | | | | |
| Wybór: plan bazowy vs adaptowany | | | | | |
| QA planu adaptowanego | | | | | |
| Weryfikacja pozycji i leczenie | | | | | |

## Ćwiczenie 3 (30 min). Kryteria decyzji „adaptować czy nie?”
Grupa ustala 3–5 mierzalnych kryteriów (np. pokrycie CTV, dawka w OAR, czas pacjenta na stole) i próg każdego.
Przedyskutujcie: co, jeśli kryteria są sprzeczne? Kto podejmuje ostateczną decyzję?

## Pytania do dyskusji (20 min)
- Jakie nowe kompetencje są potrzebne elektroradiologowi przy ART online (konturowanie, ocena sCT, praca pod presją czasu)?
- Czy sCT zwalnia z wykonania planowania na CT? W jakich sytuacjach zawsze wracamy do CT?
- Jak udokumentować, że sCT było poprawne w danej frakcji?
- Kto odpowiada za błąd, jeśli autokontur + sCT doprowadziły do złej adaptacji?

## Zadanie dodatkowe dla chętnych (programistyczne)
W notatniku bloku 1 wygeneruj „CBCT” z fantomu: dodaj szum, niejednorodność („cupping”: `ct + A * (r/R)**2`) i przesunięcie HU.
Policz MAE HU w ciele względem oryginału, a następnie „skoryguj” obraz prostą kalibracją liniową lub dopasowaniem histogramu
(`skimage.exposure.match_histograms`). Ile wynosi MAE po korekcji? Przelicz dawkę modelem `rtcourse.dose` — czy zależy od HU? (Podpowiedź: nie — i to jest ograniczenie modelu edukacyjnego; opisz, czego brakuje.)
