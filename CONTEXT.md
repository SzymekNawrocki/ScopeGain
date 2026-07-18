# Kontekst domenowy ScopeGain

Kanoniczny język tego projektu. Definicje mówią, **czym coś jest**, a nie jak to
zrobić — to glosariusz, nie specyfikacja i nie brudnopis. Decyzje projektowe żyją
w `docs/adr/`.

Zasada nadrzędna: apka **mówi, czego nie wie**, zamiast zmyślać. Większość pojęć
poniżej istnieje właśnie po to, żeby dało się to powiedzieć precyzyjnie.

---

## Co użytkownik ma

**Portfel** — nazwany koszyk pozycji („Emerytura", „Spekulacje"). Reprezentuje to, co
użytkownik **posiada**.
_Unikaj_: konto, watchlista.

**Pozycja** — ile sztuk danej spółki użytkownik ma **teraz**. Odpowiada na pytanie
„co mam dziś”.
_Unikaj_: transakcja, holding.

**Transakcja** — pojedyncze kupno albo sprzedaż z datą i ceną. Log jest
append-only i istnieje **obok** pozycji.
_Unikaj_: zlecenie (order) — apka niczego nie zleca.

**Rekoncyliacja** — porównanie stanu netto wyliczonego z logu transakcji ze stanem
pozycji. Gdy się rozjeżdżają, apka **mówi to wprost**, zamiast wybierać wygodniejszą
wersję. Źródłem prawdy dla ścieżki historycznej jest log.

---

## Co użytkownik rozważa

**Temat** — pomysł inwestycyjny użytkownika („Uran", „Kwanty", „Woda"), reprezentowany
jako koszyk **kuratorowany przez niego**. Temat **nie jest** wynikiem wyszukiwarki ani
kategorią źródła danych. Patrz [ADR-0002](docs/adr/0002-temat-jest-koszykiem-kuratorowanym.md).
_Unikaj_: sektor, branża, watchlista.

**Branża** — kategoria nadana spółce przez **dostawcę danych** (np. „Uranium"). Jest
ich 145 i są zamkniętą listą. Bywa punktem wyjścia dla tematu, ale nim nie jest:
„uran” jest branżą, „kwanty” nie są i nie będą.
_Unikaj_: temat, sektor (sektor to szerszy poziom: „Energia”).
Uwaga o kompletności: lista spółek branży, którą oddaje źródło (`yf.Industry`), to
**ranking „top”, a nie spis** — gubi liderów (przy uranie pomija Cameco, dokładnie
jak wyszukiwarka po nazwie). Dlatego przeglądanie po branży niesie jawne
zastrzeżenie, a luki uzupełnia się rozbiciem ETF i szukaniem po nazwie.

**Kandydat** — spółka zaproponowana użytkownikowi do tematu. Kandydatem się bywa,
składnikiem tematu zostaje się dopiero decyzją użytkownika.

**Pochodzenie** — skąd kandydat się wziął („z branży Uranium”, „z ETF QTUM”, „dodane
ręcznie”). Widoczne zawsze, bo bez tego użytkownik nie wie, czemu ma ufać liście.

**Obserwacja** — spółka w temacie wraz z całym **planem decyzji**: Tezą,
Unieważnieniem, opcjonalnym warunkiem wejścia oraz **datą i ceną z momentu dodania**.
Ta para liczb (data + cena) pozwala później rozliczyć użytkownika z jego własnego typu.
_Unikaj_: pozycja (obserwacja to „rozważam”, nie „mam”).

**Teza** — napisany przez użytkownika powód, dla którego dodał spółkę („deficyt podaży
uranu”). Apka konfrontuje ją później z tym, co się faktycznie stało.

**Unieważnienie** — zapisany z góry warunek, przy którym użytkownik uzna, że się mylił:
**cena progu** („poniżej 55”) **albo** opisany warunek („jeśli deficyt uranu się nie
zmaterializuje do 2027”). Bez niego decyzji nie da się później uczciwie rozliczyć —
typ bez warunku porażki wygląda zawsze na trafny. To dyscyplina, nie sygnał (ADR-0001).
_Unikaj_: stop-loss (to nie zlecenie ani mechanika day-tradingu — patrz ADR-0003).

**Realizacja** — **potwierdzone** powiązanie Obserwacji z Transakcją, która wykonała ten
typ. Apka ją tylko **proponuje** (widzi kupno tej spółki po dacie dodania typu i pyta
„to realizacja tego typu?”), a użytkownik **potwierdza** — bo samo posiadanie tickera nie
znaczy, że kupił pod tę tezę (mógł mieć od dawna albo w innym portfelu). Bez potwierdzenia
typ pozostaje **nietknięty**. To ta sama zasada co przy kandydatach (ADR-0002): apka
podsuwa, użytkownik decyduje.
_Unikaj_: „acted” jako automatyczna flaga z dopasowania tickera.

---

## Co apka mówi

**Werdykt** — wniosek wyrażony po ludzku wraz z oceną 🟢🟡🔴. Apka **nie wydaje zleceń
kup/sprzedaj** ([ADR-0001](docs/adr/0001-narzedzie-do-myslenia-nie-robo-doradca.md)).

**Werdykt ryzyka** — werdykt o **pojedynczej spółce**. Ocenia wyłącznie ryzyko
(„niskie / podwyższone / wysokie”), nigdy jakość. „Mocny” przy spółce czytałoby się
jak polecenie zakupu — to ta sama decyzja co ADR-0001, tylko widziana z bliska.
_Unikaj_: rekomendacja, ocena spółki.

**Zastrzeżenie (caveat)** — jawne ograniczenie werdyktu, wyświetlane **przy nim**,
nie w stopce. Werdykt o jednej spółce czyta się jak porada dużo mocniej niż werdykt
o własnym portfelu.

**Braki danych (data_gaps)** — metryki, których zabrakło i których reguły pominięto.
Bez tego werdykt policzony z 2 reguł wyglądałby tak samo pewnie jak z 5. To kłamstwo
przez przemilczenie, więc mówimy wprost.

**Punkt odniesienia** — neutralna miara, względem której widać rozjazd (np. równe wagi
przy rebalansingu). **Nie** jest poradą, co kupić.
_Unikaj_: cel, rekomendacja.

**Rozliczenie typu** — konfrontacja Obserwacji z tym, co się faktycznie stało: ruch od
ceny dodania, czy zadziałało Unieważnienie, czy użytkownik zadziałał (kupił). Liczone na
**całej puli** typów, nie tylko na trafionych — inaczej uczyłoby FOMO (pokazywanie samych
wygranych to ta sama nieuczciwość, którą krytykuje się u sprzedawców strategii). Nigdy
nie mówi „trzeba było kupić” — to złamałoby ADR-0001 tylnymi drzwiami. Odbija decyzję
użytkownika, nie wydaje nowej.
_Unikaj_: wynik, żal, „a nie mówiłem”.

**Trafność typu** — kierunek ruchu ceny od momentu dodania względem tezy (na plus / na
minus). Opisuje fakt, nie ocenia jakości spółki i nie jest sygnałem.

**Hit rate** — udział trafionych typów w całej puli. Miara **dyscypliny selekcji**
(„ile z moich pomysłów faktycznie zadziałało”), a nie zachęta do handlu.

---

## Jak apka liczy

**Backtest hipotetyczny** — krzywa, która rzutuje **dzisiejsze** wagi portfela na całą
historię. To hipoteza „gdybym od początku trzymał to, co mam dziś”, a nie przeszłość
użytkownika. Musi być oznaczona jako hipoteza.
_Unikaj_: mój wynik, realny zwrot.

**Realna ścieżka** — krzywa odtworzona z **logu transakcji**: co użytkownik naprawdę
trzymał każdego dnia. Liczona metodą time-weighted, żeby wpłata gotówki nie wyglądała
jak zysk.

**Zachowanie (behavior gap)** — różnica między wynikiem rynku a wynikiem użytkownika
wynikająca z **momentów** jego decyzji, nie z doboru spółek.

**Benchmark** — „rynek”, do którego wszystko porównujemy: ETF SPY (S&P 500).
Reprezentuje alternatywę „nic nie rób, kup cały rynek”.

**VaR** — próg straty w normalnie zły okres (np. 5% najgorszych dni).
_Unikaj_: maksymalna strata.

**CVaR** — średnia strata **w ogonie** za progiem VaR: „a jak już jest źle, to ile”.

**Stress test** — co zrobiłby z portfelem powtórzony **historyczny** krach
(2008, COVID).

**Pokrycie** — jaka część portfela miała dane w danym oknie. Niskie pokrycie unieważnia
wnioski, więc jest widoczne.
