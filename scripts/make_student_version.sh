#!/usr/bin/env bash
# Tworzy wersję „student” repozytorium — BEZ katalogu instructor/ i bez sekcji
# README oznaczonych <!-- INSTRUCTOR-START --> ... <!-- INSTRUCTOR-END -->.
#
# Użycie:   bash scripts/make_student_version.sh [katalog_docelowy]   (domyślnie ./student_version)
#
# Kopiowane są tylko pliki śledzone przez git (git archive HEAD), więc lokalne
# dane, wyniki i pliki tymczasowe nie trafią do wersji publicznej.
# Po wygenerowaniu: sprawdź wynik, a potem np.
#   cd student_version && git init && git add . && git commit -m "Wersja dla studentów" && git push <publiczne-repo>
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$ROOT/student_version}"
cd "$ROOT"
if ! git diff --quiet HEAD -- . 2>/dev/null; then
  echo "UWAGA: masz niezacommitowane zmiany — do wersji studenckiej trafi stan z ostatniego commita (HEAD)." >&2
fi
rm -rf "$OUT"
mkdir -p "$OUT"
git archive HEAD | tar -x -C "$OUT"
rm -rf "$OUT/instructor"
# usuń sekcje README przeznaczone tylko dla prowadzącego
PY=python3; "$PY" -c 1 2>/dev/null || PY=python   # Windows: python3 bywa atrapą ze Sklepu
"$PY" - "$OUT/README.md" <<'PY'
import re, sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
s = re.sub(r"<!-- INSTRUCTOR-START -->.*?<!-- INSTRUCTOR-END -->\n?", "", s, flags=re.S)
open(p, "w", encoding="utf-8").write(s)
PY
# kontrola: żadnych odwołań do instructor/ ani plików z kluczami odpowiedzi
LEFT=$(grep -rIl --exclude-dir=.git --exclude=make_student_version.sh --exclude=ci.yml -e "instructor/" "$OUT" || true)
if [ -n "$LEFT" ]; then
  echo "UWAGA: pliki nadal wspominające 'instructor/' (sprawdź, czy to nie zdradza rozwiązań):" >&2
  echo "$LEFT" >&2
fi
test ! -e "$OUT/instructor" || { echo "BŁĄD: instructor/ nadal istnieje" >&2; exit 1; }
echo "Gotowe: $OUT  ($(find "$OUT" -type f | wc -l) plików, bez instructor/)"
