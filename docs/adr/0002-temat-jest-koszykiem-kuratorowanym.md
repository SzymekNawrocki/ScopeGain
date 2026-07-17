# 2. Temat jest koszykiem kuratorowanym, nie wynikiem wyszukiwarki

Data: 2026-07-17
Status: przyjęte

## Kontekst

Właściciel chce używać ScopeGain do realnego szukania spółek tematycznych: „spółek
kwantowych, może woda, uran". Oczekiwanie brzmiało: apka ma sama podpowiadać, gdzie
jest ryzyko, a gdzie szansa — czego platforma maklerska nie zrobi, bo „pokaże słupki
i elo".

Naturalna pokusa to zbudować wyszukiwarkę tematyczną: wpisujesz „uran", apka szuka
po nazwie i opisie, oddaje listę. Sprawdziliśmy to empirycznie na `yfinance` 1.5.1
(2026-07-17) i **to nie działa**:

- `yf.Search("uranium")` → UEC, URA, UROY, U-UN.TO, URNM. **Cameco (CCJ) nie ma na
  liście** — a to największa spółka uranowa świata. Wypadła, bo nie ma słowa
  „uranium" w nazwie.
- Jednocześnie `yf.Ticker("CCJ").info` mówi wprost `industry: "Uranium"`. Apka *zna*
  tę spółkę jako uranową i *nie potrafi* jej znaleźć po słowie „uran".
- Taksonomia źródła ma 145 branż (`SECTOR_INDUSTY_MAPPING`). Jest `Uranium`,
  `Utilities—Regulated Water`, `Solar`. **Nie ma** `quantum`, `nuclear` ani `lithium`
  — a „kwanty" to pierwszy temat, który właściciel wymienił. IBM i Alphabet nigdy nie
  będą sklasyfikowane jako „kwantowe”; formalnie to usługi IT.
- `yf.screen(EquityQuery("eq", ["industry", "uranium"]))` → `ValueError`.
  `EQUITY_SCREENER_EQ_MAP["industry"]` zawiera nazwy *sektorów* — quirk biblioteki.
  Screener po branży jest niepewny; `yf.Industry()` działa.
- Holdingi ETF-u (`yf.Ticker("URA").funds_data.top_holdings`) dają realny koszyk
  z Cameco — ale tylko ok. 10 pozycji i z symbolami giełd lokalnych (`CCO.TO`, nie
  `CCJ`).

Rozróżnienie, które z tego wynika: **temat ≠ branża**. Branża to kategoria źródła
(145 gotowych). Temat to pomysł inwestycyjny użytkownika, który czasem pokrywa się
z branżą (uran, woda), a czasem nie istnieje w żadnej taksonomii (kwanty).

## Decyzja

**Temat jest koszykiem kuratorowanym przez użytkownika.** Apka podsuwa kandydatów
z trzech źródeł — branża (`yf.Industry`), holdingi wskazanego ETF-u, wyszukiwarka po
nazwie — ale **to użytkownik decyduje, kto wchodzi**, a każdy składnik ma widoczne
**pochodzenie** („z ETF QTUM”, „dodane ręcznie”).

Osobno, jako doprecyzowanie granicy z [ADR-0001](0001-narzedzie-do-myslenia-nie-robo-doradca.md):
**werdykt pojedynczej spółki osądza RYZYKO, nie wydaje porady.** Etykiety to
„niskie / podwyższone / wysokie ryzyko”, nigdy „mocny / słaby”.

## Konsekwencje

- Apka nigdy nie udaje, że zna skład tematu. Automat po cichu gubiłby lidera branży,
  a użytkownik nie miałby jak się dowiedzieć, że czegoś nie widzi — to ten sam rodzaj
  cichego kłamstwa, który rekoncyliacja logu transakcji już eliminuje gdzie indziej.
- Wyszukiwarka wystawiona w Etapie A szuka **po nazwie**, i tylko tak jest uczciwa:
  `Search("cameco")` zwraca CCJ na pierwszym miejscu. Szukania tematycznego nie
  wystawiamy, bo dawałoby złudzenie kompletności.
- Kuratorowanie to koszt: użytkownik musi popracować przy zakładaniu tematu. To cena
  za to, żeby wiedzieć, co jest w koszyku i dlaczego.
- Realizuje wprost intencję właściciela: „jak się czegoś dowiem, chcę to wprowadzać
  w tej aplikacji”. Temat jest miejscem na jego wiedzę, nie na cudzy algorytm.
- Cross-listing zostaje **nierozdzielony**: CCJ (NYSE, USD) i CCO.TO (Toronto, CAD)
  to różne papiery, waluty i metryki. Nie deduplikujemy po nazwie; giełda jest jedyną
  rzeczą, która je rozróżnia w podpowiedziach.
- „Werdykt ryzyka” niesie obowiązkowe zastrzeżenie i listę `data_gaps` — werdykt
  policzony z 2 reguł nie może wyglądać tak samo pewnie jak z 5.
- Etykietowanie werdyktu spółki jakością byłoby złamaniem ADR-0001 tylnymi drzwiami
  („Cameco: MOCNY” czyta się jak polecenie zakupu). Broni tego test-strażnik
  (`test_stock_verdict_label_always_speaks_about_risk`), bo mina realnie istniała:
  `PortfolioVsMarket` miał słownik `{good:"MOCNY"}` kluczowany po severity.
