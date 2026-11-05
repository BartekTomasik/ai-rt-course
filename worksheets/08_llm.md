# Blok 8. LLM w codziennej pracy — karta ćwiczeń

**Forma:** warsztat; praca w parach z dowolnym ogólnodostępnym czatem LLM (konto prywatne lub uczelniane).

## ⚠️ Zasady bezpieczeństwa (przeczytaj przed ćwiczeniem)
- **Nigdy** nie wklejaj danych pacjentów — także „zanonimizowanych” samodzielnie (imię, PESEL, daty, rzadka diagnoza, opis + miejscowość mogą identyfikować).
- Nie wklejaj dokumentów wewnętrznych zakładu, haseł, zrzutów ekranu z systemów szpitalnych.
- Publiczne usługi LLM mogą przechowywać i wykorzystywać wpisy — **RODO** dotyczy także Ciebie jako pracownika.
- Wynik LLM to **szkic**. Odpowiedzialność za treść ponosi człowiek, który ją zatwierdza.

## Cel kliniczny
Umieć wykorzystać LLM do pracy z tekstem (protokoły, dokumentacja, informacja dla pacjenta), **systematycznie wykrywać błędy**
i znać granice: co wolno, czego nie wolno, kiedy LLM szkodzi.

## Krótka teoria (20 min)
- LLM przewiduje kolejne słowa — **nie sprawdza faktów**. Halucynacje: zmyślone liczby, zalecenia, źródła (DOI, wytyczne).
- Jakość zależy od polecenia (promptu): rola, odbiorca, format, ograniczenia, prośba o wskazanie niepewności.
- Typowe dobre zastosowania: upraszczanie języka, struktura dokumentu, listy kontrolne, tłumaczenie, streszczenie **publicznego** tekstu.
- Typowe złe: dawki, frakcjonowanie, decyzje kliniczne, cytowania bez sprawdzenia, dane osobowe.

## Ćwiczenie 1 (30 min). Polowanie na błędy
Zadajcie LLM 3 pytania (każda para inne):
1. „Wyjaśnij pacjentowi, jak przygotować się do radioterapii prostaty (pęcherz, odbytnica).”
2. „Jakie są typowe ograniczenia dawki dla rdzenia kręgowego w radioterapii konwencjonalnej? Podaj źródła.”
3. „Napisz procedurę kontroli tożsamości pacjenta przed frakcją.”

Oceńcie każdą odpowiedź w arkuszu:

| # | Fragment odpowiedzi | Kategoria błędu | Ryzyko (0–3) | Jak sprawdziliśmy | Poprawka |
|---|---|---|---|---|---|
| | | merytoryczny / halucynacja / pominięcie / nieaktualne / ton / niejasne | 0 = brak, 3 = możliwa szkoda | źródło | |

Sprawdźcie **każde** podane źródło (czy istnieje, czy mówi to, co LLM twierdzi).

## Ćwiczenie 2 (40 min). Ulotka dla pacjenta
Temat: „Pielęgnacja skóry w trakcie radioterapii piersi”. Trzy wersje promptu:
- A: jedno zdanie;
- B: rola + odbiorca (pacjentka 70 lat, poziom języka prosty) + format (max 1 strona, punkty);
- C: jak B + „wskaż, które zalecenia należy potwierdzić z zespołem leczącym; nie podawaj nazw handlowych”.

Porównajcie wersje: liczba błędów, czytelność (np. jasnopis.pl), kompletność. Która wersja jest najbezpieczniejsza i dlaczego?

## Ćwiczenie 3 (20 min). Co wolno wkleić? — szybki quiz (grupa decyduje: TAK / NIE / TAK po zmianach)
1. Fragment publicznych wytycznych ESTRO. 2. Skan skierowania z nazwiskiem. 3. Własna notatka „pacjent 67 l., rak płuca, Gdańsk, leczony od 12.03”.
4. Szablon procedury zakładowej bez danych pacjentów (czy procedura jest poufna?). 5. Zrzut ekranu planu leczenia z widocznym ID.
6. Pytanie ogólne o artefakty metaliczne w CT.

## Pytania do dyskusji (20 min)
- Czy LLM może pisać dokumentację medyczną? Jakie warunki musiałyby być spełnione (narzędzie szpitalne, umowa powierzenia danych, weryfikacja)?
- Jak zakład powinien uregulować użycie LLM przez personel (polityka, szkolenie, lista dozwolonych zastosowań)?
- Pacjent przynosi wydruk z czatu z innym zaleceniem niż nasze. Jak rozmawiać?

## Zadanie dodatkowe dla chętnych (programistyczne)
Zbuduj mały zestaw testowy: 10 pytań z poprawnymi odpowiedziami (z wytycznych) i skrypt, który porównuje odpowiedzi LLM
(wklejone ręcznie do pliku CSV) z kluczem wg prostej rubryki (zgodne / częściowo / błędne / niebezpieczne) i liczy zgodność dwóch oceniających (kappa Cohena, `sklearn.metrics.cohen_kappa_score`).
