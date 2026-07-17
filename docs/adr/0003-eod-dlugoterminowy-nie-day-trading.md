# 3. ScopeGain jest narzędziem end-of-day i długoterminowym, nie terminalem day-tradingu

Data: 2026-07-17
Status: przyjęte

## Kontekst

Właściciel przyniósł esencję filmu o day-tradingu (skanowanie luk przed otwarciem,
wolumen intraday, short covering, Opening Range Breakout, stop lossy) i zapytał, czy
ScopeGain nie powinien iść w tę stronę, żeby być „pełnoprawną aplikacją pod inwestowanie
pieniędzy”. Pytanie zderzyło się z [ADR-0001](0001-narzedzie-do-myslenia-nie-robo-doradca.md),
z wybranym kierunkiem (dziennik decyzji, długi horyzont) oraz z realnym źródłem danych.

Rozstrzygnięcie grilla (2026-07-17): właściciel wprost odrzucił day-trading —
„nie chcę siedzieć w liczbach całymi dniami, tylko na podstawie dobrej analizy
długoterminowo inwestować i się nauczyć; jak będę w tym dobry, wtedy przejdę na
day-trading”. Day-trading jest więc **odłożony**, nie porzucony na zawsze.

Trzy powody, dla których ta granica jest twarda dzisiaj:

- **Tożsamość.** Day-trading to esencja „timingu i sygnałów”, o których własny research
  (PLAN.md, warstwa 12) mówi, że inwestorowi indywidualnemu nie dają przewagi. Sam film
  to potwierdza: bez udowodnionej przewagi, pokazuje głównie wygrane, promuje kurs.
- **Dane.** `yfinance` to świece **dzienne i opóźnione** — brak premarket, brak intraday
  real-time, brak skanera całego rynku. Skaner luk na otwarciu jest na tym źródle
  technicznie niewykonalny; wymagałby płatnego dostawcy (Polygon/Alpaca/IEX).
- **Spójność.** Apka **mierzy behavior gap** — stratę z mistimingu. Day-trading to
  maksymalna forma tego zachowania; wbudowanie skanera byłoby zaszyciem choroby w lek.

## Decyzja

ScopeGain operuje na danych **end-of-day** i na horyzoncie **pozycji/tez**, nie sesji.
Skaner premarket/intraday, Opening Range Breakout, alerty na żywo i pochodne day-tradingu
są **świadomie poza zakresem**. Z materiału o day-tradingu importujemy wyłącznie warstwę
**dyscypliny** (selekcja, pisany plan, Unieważnienie, czekanie na wejście) — patrz pojęcia
w CONTEXT.md — bo ona jest niezależna od horyzontu i zgodna z ADR-0001.

## Konsekwencje

- Nie dokładamy źródeł real-time ani skanerów rynku; funkcje forward-looking zostają
  „z ostrzeżeniem” i na danych dziennych (ADR-0001).
- „Unieważnienie” w Obserwacji to warunek złamania tezy, **nie** stop-loss w sensie
  zlecenia ani mechanika intraday.
- Rozliczenie typu liczy się na zamknięciach dnia — to wystarcza dla horyzontu tygodni
  i miesięcy, o który tu chodzi.
- Decyzja jest **odwracalna świadomie**: jeśli właściciel realnie wejdzie w day-trading,
  wróci tu nowy ADR, który nazwie koszt (płatne dane, inny profil ryzyka, inny UX).
- Broni się na rozmowie: „wiem, czego NIE robię i dlaczego” — tak samo jak ADR-0001.
