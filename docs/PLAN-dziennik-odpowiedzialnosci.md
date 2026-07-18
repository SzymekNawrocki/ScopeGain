# Plan: dziennik odpowiedzialności (to, czego chat nie może)

> Kierunek rozstrzygnięty grillem 2026-07-17 i utrwalony w
> [ADR-0004](adr/0004-konkurujemy-na-odpowiedzialnosci-nie-na-researchu.md).
> Ten plik jest żywy — aktualizować po każdym dowiezionym plastrze.

## Zasada nadrzędna (test każdej funkcji)

Przed budową każdej funkcji: **„czy Claude/Cowork zrobiłby to lepiej?”**
- Jeśli TAK (research, opis spółki, tłumaczenie pojęć) → **nie budujemy**.
- Budujemy tylko to, co wymaga jednej z trzech rzeczy, których chat dać nie może:
  **(1) trwałości** (pamięć Twoich decyzji w czasie), **(2) Twoich realnych liczb**
  (uczciwa matematyka + odmowa zmyślania), **(3) konfrontacji** (anty-sykofancja).

## Co schodzi z osi (nie kasujemy, przestajemy rozwijać)

- **„Odkrywaj”** jako narzędzie researchu — najsłabsze miejsce, chat to robi lepiej.
  Zostaje jako **cienka użytka**: „mam już spółkę na oku → wprowadź ją do tezy”.
  Przestaje być domyślnym trybem i front-drzwiami.

## Front-drzwia się zmieniają

Domyślny tryb przestaje być „Odkrywaj”. Staje się **Pulpit** (gdy powstanie) —
„co wymaga Twojej uwagi dziś”. Oś apki: **Pulpit → Tematy (dziennik) → Portfel**.

## Plaster teraz: Realizacja + realne rozliczenie + Pulpit

Cel: żeby apka robiła to, czego chat nie może — **trzymała Cię za słowo w czasie**.

### 1. Realizacja (spięcie typu z posiadaniem) — model + backend
Decyzja z grilla: **apka PROPONUJE, użytkownik POTWIERDZA** (nigdy auto z tickera —
posiadanie ≠ kupno pod tezę). Patrz pojęcie **Realizacja** w CONTEXT.md.
- Model: powiązanie `Observation` ↔ `Transaction` (potwierdzone). Zastępuje surową
  flagę `acted` — „zadziałałem” = istnieje potwierdzona Realizacja.
- Propozycja: apka znajduje BUY tej spółki z datą **≥ data dodania typu** i podsuwa
  „to realizacja tego typu?”. Kupno sprzed dodania i inny ticker (cross-listing) →
  nie proponuje (uczciwie; ewentualny link ręczny później).
- Endpoint: lista propozycji per temat/globalnie + potwierdź/odrzuć.

### 2. Realne rozliczenie (Etap 5, teraz z prawdziwymi danymi)
- „Typ trafny, ale nie kupiłeś” = ruch dodatni od dodania **i brak Realizacji**.
- Gdy jest Realizacja: policz realny wynik od ceny transakcji (nie od ceny dodania).
- Nadal hit rate na **całej puli**, neutralnie, nigdy „trzeba było kupić” (ADR-0001).

### 3. Pulpit — „co wymaga Twojej uwagi dziś” (nie skaner „kup teraz”)
Ląduje **tylko** to, co wynika z Twoich zapisów i wymaga Twojego osądu:
- tezy z **przebitym unieważnieniem** (zrewiduj!),
- **propozycje Realizacji** do potwierdzenia,
- **spełnione warunki wejścia** (Twój własny próg — fakt, nie porada),
- **typy nierozliczone** / dawno nietknięte.
Ryzyko portfela jako drugorzędny kafelek. Zero języka „kup”.

## Konkret techniczny (skrót, wzorce już w repo)
- Backend: relacja w `models.py` (wzorzec `Transaction`), migracja; logika propozycji
  jako **czysta funkcja** w `analysis.py` (test na zamrożonych danych, jak
  `build_reckoning`); trasy w `routers/themes.py`; Pulpit — nowy router/agregat.
- Frontend: nowy tryb **Pulpit** w `WorkspaceProvider`/`Nav` (domyślny); UI potwierdzania
  Realizacji w `ThemesWorkspace`; rozliczenie czyta realny wynik.
- Reużyć: `latest_prices`, `getTransactions`, `VerdictFindings`, `StatTile`, `TerminalWindow`.

## Świadomie NIE
Research/odkrywanie jako cel (ADR-0004), day-trading (ADR-0003), robo-doradca (ADR-0001),
szerokość na całe finanse (budżet/krypto) — dopiero po domknięciu pętli odpowiedzialności.

## Weryfikacja
`pytest` (propozycje + realne rozliczenie jako czyste funkcje) · migracja na żywej bazie ·
e2e: dodaj typ → zaloguj transakcję → potwierdź Realizację → Pulpit pokazuje właściwe
pozycje · `tsc` + `next build` · podgląd w przeglądarce.
