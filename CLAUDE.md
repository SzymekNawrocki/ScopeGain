# Instrukcje projektu (ScopeGain)

## Konwencja commitów — Conventional Commits (domyślnie)

Używaj **standardowej nomenklatury** Conventional Commits. Typ + zwięzły opis:

```
<typ>: <opis w trybie rozkazującym>
```

Dozwolone typy (tylko te, nie wymyślaj własnych):

- `feat` — nowa funkcja
- `fix` — poprawka błędu
- `chore` — sprzątanie, konfiguracja, zależności, drobiazgi
- `docs` — dokumentacja
- `refactor` — zmiana kodu bez zmiany zachowania
- `test` — testy
- `perf` — wydajność
- `ci` / `build` — pipeline / build

### Zasady

- **Scope opcjonalny** i tylko gdy to realny moduł: `feat(auth):`, `fix(quant):`.
  NIE wymyślaj scope'ów od wewnętrznej numeracji warstw ani opisowych nazw
  (unikaj `feat(risk+12b)`, `feat(12c)`, `feat(uczciwosc)` — to ma być `feat:`).
- Opis krótki, w trybie rozkazującym (np. „dodaj log transakcji", nie „dodano").
- Szczegóły (warstwy, decyzje, weryfikacja) idą do **treści** commita, nie do typu.
- Stopka jak zwykle: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
