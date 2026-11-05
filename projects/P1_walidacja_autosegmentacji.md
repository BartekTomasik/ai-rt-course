# P1. Walidacja autosegmentacji wybranego narządu i wpływ na DVH (techniczny)

## Pytanie
Czy autosegmentacja (TotalSegmentator) wybranego narządu krytycznego jest wystarczająco dobra do użytku klinicznego —
**geometrycznie i dawkowo**?

## Co robicie
1. Wybierzcie narząd (serce, przełyk, rdzeń kręgowy albo płuca) i uzasadnijcie wybór klinicznie.
2. Na wszystkich przypadkach z pakietu kursu policzcie Dice, HD95 i surface Dice (notatnik 3; pętla po `data.load_case(i)`).
3. Dla tych samych przypadków porównajcie metryki dawkowe (Dmean, Vx, D0.03cc — zależnie od narządu) dla konturu
   referencyjnego i AI na tej samej dawce (notatnik 4).
4. Zaproponujcie **kryteria akceptacji** (geometryczne + dawkowe) i sprawdźcie, ile przypadków je spełnia.
5. Opiszcie typowe błędy (zrzuty ekranu przekrojów) i gdzie się kumulują.

## Wynik
Tabela metryk per przypadek, wykres Dice vs ΔDmean, propozycja kryteriów, 2–3 przykłady błędów, wnioski.

## Kryteria merytoryczne (50 pkt)
| Kryterium | Pkt |
|---|---|
| Poprawne policzenie i opis metryk geometrycznych (z jednostkami, tolerancją surface Dice) | 10 |
| Analiza dawkowa: dobór metryk do narządu, interpretacja różnic | 15 |
| Kryteria akceptacji: uzasadnione, sprawdzone na danych, omówione przypadki graniczne | 15 |
| Analiza błędów jakościowa (przykłady, lokalizacja, możliwa przyczyna) | 10 |

## Ograniczenia, o których warto napisać
Mała liczba przypadków, jeden obserwator referencyjny, wirtualny guz i dawka modelowa, przeskalowane CT.

## Dla chętnych
Postprocessing masek AI i porównanie przed/po; analiza zmienności (bootstrap przedziałów ufności średniego Dice).
