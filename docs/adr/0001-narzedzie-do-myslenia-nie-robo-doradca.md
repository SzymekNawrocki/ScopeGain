# 1. ScopeGain jest narzędziem do myślenia, nie robo-doradcą

Data: 2026-07-16
Status: przyjęte

## Kontekst

ScopeGain zaczął jako projekt-portfolio „do obrony na rozmowie" (MISSION.md), ale
realną motywacją użytkownika jest **narzędzie, które pomoże mu inwestować** i wyrobić
znajomość tematu quant. Te dwa cele cicho ciągnęły w przeciwne strony, a
`QUANT_ROADMAP.md` zdiagnozował lukę: apka „opisuje przeszłość".

Naturalna pokusa to zamienić apkę w **robo-doradcę**: dawać konkretne zlecenia
„kup NVDA za 1200 zł, sprzedaj VOO". To daje największy efekt „wow", ale opiera się
na zbacktestowanych metrykach z przeszłości i darmowym feedzie (yfinance) — czyli
dokładnie tej „pięknej matematyce, która nie działa out-of-sample", przed którą
ostrzega własny research użytkownika (Warstwa 12 w PLAN.md: dla inwestora
indywidualnego liczą się koszty, zachowanie, dywersyfikacja — nie sygnały).

## Decyzja

ScopeGain jest **narzędziem do myślenia**: liczy, pokazuje ryzyko i konfrontuje
decyzje użytkownika — ale **świadomie NIE wydaje zleceń „kup/sprzedaj"**. Wartość
apki to jasność i pokora poznawcza, nie prognoza.

## Konsekwencje

- Funkcje forward-looking wybieramy pod uczciwość: pierwsza to **VaR + stress test**
  (odtwarzają realny rozkład/historię), nie Monte Carlo (prognoza, „kłamie w górę").
- Rebalancing (12c) pokazuje koncentrację i kierunek korekty, ale **bez dosłownych
  zleceń w złotówkach**.
- Funkcje czysto matematyczne (Monte Carlo, granica efektywna) budujemy tylko
  „z ostrzeżeniem" o kruchości out-of-sample.
- Każda liczba, która jest hipotezą (np. backtest na dzisiejszych wagach), musi być
  **jawnie oznaczona** — nie udajemy realnej ścieżki.
- Na rozmowie broni się mocniej: „rozumiem, dlaczego NIE robię robo-doradcy" bije
  udawanie, że model przewiduje rynek.
