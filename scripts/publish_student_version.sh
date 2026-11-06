#!/usr/bin/env bash
# Odświeża PUBLICZNE repozytorium studentów (BartekTomasik/ai-rt-course) z bieżącego HEAD tego repozytorium.
#
# Użycie:   bash scripts/publish_student_version.sh            # przygotuj commit i pokaż zmiany (bez wysyłania)
#           bash scripts/publish_student_version.sh --push     # ... i wyślij (git push) do repozytorium publicznego
#
# Kroki: make_student_version.sh (bez instructor/ i sekcji INSTRUCTOR) -> klon repozytorium publicznego do katalogu
# tymczasowego -> podmiana całej zawartości (poza .git) -> commit "Wersja dla studentów (z ai-rt-course-instructor @ <sha>)".
# Bez --push nic nie wychodzi na zewnątrz: dostajesz ścieżkę do klonu z gotowym commitem i listę zmian do przejrzenia.
set -euo pipefail
PUBLIC="${PUBLIC_REPO:-https://github.com/BartekTomasik/ai-rt-course.git}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PUSH=0; [ "${1:-}" = "--push" ] && PUSH=1
if ! git diff --quiet HEAD -- . 2>/dev/null; then
  echo "BŁĄD: masz niezacommitowane zmiany. Zacommituj je (albo schowaj: git stash) i uruchom ponownie." >&2; exit 1
fi
SHA="$(git rev-parse --short HEAD)"
TMP="$(mktemp -d)"
bash scripts/make_student_version.sh "$TMP/student" >/dev/null
git clone -q "$PUBLIC" "$TMP/public"
# podmień zawartość (zostaw historię .git repozytorium publicznego)
find "$TMP/public" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
cp -a "$TMP/student/." "$TMP/public/"
cd "$TMP/public"
# kontrola bezpieczeństwa: nic z instructor/ ani etykiet wyzwania
if [ -e instructor ] || git ls-files --others --exclude-standard | grep -E "challenge_gt|instructor_private|solutions" >/dev/null; then
  echo "BŁĄD: w wersji publicznej są pliki prowadzącego - przerwano." >&2; exit 1
fi
git add -A
if git diff --cached --quiet; then
  echo "Repozytorium publiczne jest już aktualne (HEAD $SHA). Nic do zrobienia."; exit 0
fi
echo "Zmiany względem repozytorium publicznego:"; git diff --cached --stat | tail -25
git commit -q -m "Wersja dla studentów (z ai-rt-course-instructor @ $SHA)"
if [ "$PUSH" = 1 ]; then
  git push -q origin HEAD
  echo "Wysłano do $PUBLIC."
else
  echo
  echo "Gotowy commit (NIE wysłany) w: $TMP/public"
  echo "Przejrzyj: cd \"$TMP/public\" && git show --stat"
  echo "Wyślij:    cd \"$TMP/public\" && git push   (albo uruchom ten skrypt z --push)"
fi
