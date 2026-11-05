# Blok 9. Regulacje i krytyczna ocena publikacji — karta ćwiczeń

**Forma:** krótki wykład + praca w grupach nad jedną publikacją. Treści regulacyjne są **ogólne i edukacyjne — to nie jest porada prawna.**

## Cel
Rozumieć, w jakich ramach prawnych działają narzędzia AI w radioterapii, i umieć krytycznie przeczytać pracę o AI
(czy wynik jest wiarygodny i czy można go przenieść do naszego zakładu).

## Krótka teoria (30 min)
**Regulacje (UE, w uproszczeniu):**
- **MDR** (Rozporządzenie (UE) 2017/745): oprogramowanie o celu medycznym (np. autokonturowanie, sCT) to wyrób medyczny;
  klasa zależy m.in. od reguły 11 (najczęściej IIa lub wyżej); wymagane oznakowanie CE, ocena kliniczna, nadzór po wprowadzeniu do obrotu.
- **AI Act** (Rozporządzenie (UE) 2024/1689): systemy AI będące wyrobami medycznymi podlegającymi ocenie jednostki notyfikowanej
  są zwykle **systemami wysokiego ryzyka** — dodatkowe wymagania (zarządzanie ryzykiem, jakość danych, dokumentacja,
  nadzór człowieka, przejrzystość, rejestrowanie zdarzeń). Obowiązki stosuje się stopniowo (kilka lat od 2024 r.).
  Obowiązki mają też **podmioty stosujące** (np. szpital): używanie zgodnie z instrukcją, nadzór człowieka, kompetencje personelu, monitorowanie.
- **RODO:** dane medyczne = szczególna kategoria; rozwój modeli na danych zakładu wymaga podstawy prawnej i zwykle zgody komisji bioetycznej / IOD.
- Narzędzia „zrobione w domu” (in-house) — w MDR art. 5 ust. 5 ma szczególne warunki; zawsze konsultacja z działem prawnym/IOD.

**Krytyczna ocena publikacji:**
- **TRIPOD+AI** (Collins i wsp., *BMJ* 2024) — raportowanie modeli predykcyjnych (27 punktów).
- **CLAIM 2024** (Tejani i wsp., *Radiol AI* 2024) — AI w obrazowaniu medycznym.
- **PROBAST+AI** — ryzyko błędu systematycznego modeli predykcyjnych.
- Typowe czerwone flagi: brak walidacji zewnętrznej, podział nie po pacjentach (blok 2!), mała próba testowa, porównanie z jednym obserwatorem,
  brak przedziałów ufności, wyniki tylko geometryczne bez oceny klinicznej, autorzy = producent bez ujawnienia konfliktu interesów.

## Ćwiczenie 1 (20 min). Gdzie jest regulacja? — scenariusze
Grupa decyduje i uzasadnia (MDR? AI Act? RODO? nic?):
1. Zakład kupuje autokonturowanie z oznakowaniem CE. 2. Fizyk pisze skrypt w Pythonie liczący DVH do raportu.
3. Doktorant trenuje model na danych zakładu do publikacji. 4. Ten sam model ma być używany klinicznie.
5. Elektroradiolog używa publicznego czatu LLM do przetłumaczenia ulotki. 6. Szpital wdraża LLM do pisania wypisów.

## Ćwiczenie 2 (80 min). Ocena jednej pracy (TRIPOD+AI / CLAIM)
Prowadzący rozdaje 1 pracę na grupę (propozycje do wyboru przez prowadzącego — przykładowe tematy: walidacja kliniczna autokonturowania OAR,
sCT z CBCT do ART, predykcja dawki 3D (np. na danych OpenKBP), predykcja toksyczności z radiomiki).

1. (40 min) Wypełnijcie skróconą listę kontrolną:

| Obszar | Pytanie | Tak / Częściowo / Nie | Gdzie w tekście |
|---|---|---|---|
| Dane | skąd, z jakich lat, kryteria włączenia/wyłączenia, ilu pacjentów | | |
| Referencja | kto i jak narysował/ustalił „prawdę”; ilu obserwatorów | | |
| Podział | uczący/walidacyjny/testowy **po pacjentach**? walidacja zewnętrzna? | | |
| Model | opisany wystarczająco do odtworzenia? kod/wagi dostępne? | | |
| Metryki | właściwe dla celu klinicznego? przedziały ufności? | | |
| Porównanie | z czym (praktyka kliniczna, inny model, zmienność obserwatorów)? | | |
| Ocena kliniczna | czas, akceptowalność, wpływ na dawkę/decyzje? | | |
| Ograniczenia i bias | podgrupy, inne tomografy, inna populacja | | |
| Konflikt interesów | finansowanie, związek z producentem | | |

2. (25 min) Trzy największe słabości i jedna mocna strona.
3. (15 min) Decyzja: „Czy na podstawie tej pracy wdrożyłbym/wdrożyłabym narzędzie u nas? Co musielibyśmy sprawdzić sami?”

## Pytania do dyskusji (20 min)
- Czy oznakowanie CE oznacza, że narzędzie działa dobrze **u nas**?
- Co oznacza „nadzór człowieka” w praktyce elektroradiologa?
- Kto zgłasza incydent z narzędziem AI i do kogo (producent, URPL, wewnętrzny system zdarzeń niepożądanych)?

## Zadanie dodatkowe dla chętnych
Odtwórz jedną tabelę/rysunek z wybranej pracy na danych publicznych (np. LCTSC + TotalSegmentator z notatnika 3) i porównaj wyniki.
Czy różnice da się wyjaśnić różnicą danych, metryk lub implementacji (np. surface Dice voxelowy vs. siatkowy)?
