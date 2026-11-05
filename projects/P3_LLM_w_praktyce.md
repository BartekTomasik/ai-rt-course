# P3. LLM w praktyce: ulotka dla pacjenta lub wsparcie protokołu — z systematyczną oceną błędów

## Pytanie
Czy duży model językowy (LLM) może pomóc przygotować materiał dla pacjenta albo fragment procedury zakładowej
— i jakie błędy oraz ryzyka trzeba wychwycić, zanim tekst trafi do użytku?

## Wybierzcie wariant
- **A. Ulotka dla pacjenta** (np. „Radioterapia klatki piersiowej — czego się spodziewać”, „Pielęgnacja skóry w trakcie RT”).
- **B. Wsparcie protokołu** (np. lista kontrolna pozycjonowania z maską termoplastyczną, procedura CBCT przed frakcją).

## Co robicie
1. Zaprojektujcie 3 różne prompty (prosty, z rolą i odbiorcą, z wymaganiami i źródłami) i wygenerujcie teksty
   w **co najmniej 2 narzędziach LLM**. **Nie wklejajcie żadnych danych pacjentów ani dokumentów wewnętrznych zakładu.**
2. Oceńcie każdą odpowiedź **systematycznie** wg arkusza z [karty bloku 8](../worksheets/08_llm.md):
   błędy merytoryczne, halucynacje (zmyślone fakty/źródła), pominięcia ważnych informacji, ton i czytelność
   (np. indeks FOG/Jasnopis), zgodność z lokalną praktyką, ryzyko szkody (skala 0–3).
3. Poproście 2 osoby spoza zespołu (np. inny zespół) o niezależną ocenę części odpowiedzi — policzcie zgodność ocen.
4. Przygotujcie **wersję końcową** poprawioną przez człowieka z listą wszystkich zmian.
5. Wnioski: do czego LLM się nadaje, do czego nie, jakie zasady wprowadzić w zakładzie (RODO, weryfikacja, odpowiedzialność).

## Kryteria merytoryczne (50 pkt)
| Kryterium | Pkt |
|---|---|
| Metodyka: prompty, narzędzia (z wersją i datą), powtarzalność | 10 |
| Systematyczna ocena błędów (arkusz, kategorie, ocena ryzyka, zgodność oceniających) | 20 |
| Jakość wersji końcowej i udokumentowane poprawki | 10 |
| Zasady bezpiecznego użycia (RODO, co wolno wklejać, kto zatwierdza) | 10 |
