# Notes — preferencje i robocze

## Jak uczyć
- Język: **polski**, styl jak w projekcie (rzeczowo, bez lania wody).
- Uczy się **praktyką** — teoria wywołana potrzebą (zasada z PLAN.md). Lekcje mają się wiązać
  z realnym kodem z jego repo, nie abstrakcyjne przykłady.
- Docenia „dlaczego", nie tylko „jak" — misja to obrona projektu na rozmowie.
- Woli mały, konkretny „win" naraz. Jedna warstwa / jedno pojęcie.

## Workspace
- Materiały nauki żyją w `learn/` wewnątrz projektu (osobno od kodu, żeby nie mieszać z gitem
  portfolio-projektu). Lekcje: `learn/lessons/`, słownik: `learn/GLOSSARY.md`.
- Otwarcie lekcji (Windows): `start learn\lessons\0001-podroz-jednego-zadania.html`

## Środowisko (gotcha)
- Windows + Git Bash: `pkill` NIE działa. Serwery ubijać przez PowerShell po porcie.
  (Zapisane też w pamięci projektu Claude Code.)

## Do rozważenia na następne lekcje
- Pogłębienia w obrębie „podróży żądania": `yield` vs `return` w `get_db`; preflight OPTIONS.
- Albo start warstwy 5 (auth: hashowanie haseł, JWT) — wróci CORS, sesja, Pydantic w nowym świetle.
