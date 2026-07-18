# 4. ScopeGain konkuruje na trwałej odpowiedzialności, nie na researchu

Data: 2026-07-17
Status: przyjęte

## Kontekst

Właściciel postawił egzystencjalne pytanie wprost: *„równie dobrze mogę odpalić
Claude/Cowork, żeby zrobił research spółki i wszystko mi opowiedział — co ta aplikacja
robi lepiej? Nie widzę tego.”*

To pytanie jest słuszne i trzeba je nazwać uczciwie. Do **researchu pojedynczej spółki
LLM wygrywa**: elastyczniej, z newsami, konwersacyjnie, bez klikania. Część „Odkrywaj”
(przeglądanie branż/ETF) jest wręcz **najsłabszym** miejscem apki — grzebanie w
dziurawych listach yfinance jest gorsze niż zapytanie chatu. Apka, która próbuje być
lepszym researchem, przegra i nie zasługuje na istnienie.

Trzeba więc nazwać, czego stateless, **przychylny** (sycophantic) LLM **strukturalnie
nie może** być — bo tylko to broni istnienia apki.

## Decyzja

ScopeGain **NIE konkuruje na researchu ani odkrywaniu** — tam wygrywa chat. Konkuruje na
trzech rzeczach, których LLM z natury dać nie może:

1. **Trwała pamięć TWOICH decyzji i rozliczenie w czasie.** Chat jest ulotny; za trzy
   miesiące nie przypomni, że dodałeś spółkę po danej cenie z daną tezą i unieważnieniem,
   i nie rozliczy Cię z własnego planu. Apka jest **dziennikiem odpowiedzialności**.
2. **Deterministyczna, uczciwa matematyka na TWOICH realnych liczbach** — VaR, TWR,
   behavior gap na faktycznym portfelu — i **odmowa zmyślania** (jawne `data_gaps`,
   caveaty). Przyciśnięty LLM zmyśli liczbę; apka policzy albo powie, że nie wie.
3. **Anty-sykofancja.** LLM jest zaprojektowany, żeby się zgadzać. Apka jest zbudowana,
   żeby **konfrontować**: hit rate na całej puli (nie na wyciętych wygranych), ile
   kosztował Cię zły timing. Ten dyskomfort to jej sens.

## Konsekwencje

- **„Odkrywaj” schodzi z roli celu** do cienkiej użytki „wprowadź spółkę do tezy”. Nie
  inwestujemy w robienie z niej narzędzia researchu; front-drzwiami apki jest dziennik /
  rozliczenie / Pulpit, nie wyszukiwarka. (Zbudowany kod zostaje, ale przestaje być
  osią.)
- **Test filtrujący każdą nową funkcję:** „czy chat zrobiłby to lepiej?”. Jeśli tak — nie
  budujemy. Budujemy tylko to, co wymaga TRWAŁOŚCI, TWOICH liczb albo KONFRONTACJI.
- **Wartość rośnie z używaniem.** Pusty dziennik na starcie nie jest wadą, tylko naturą
  rzeczy — projektujemy pod miesiące używania, nie pod pierwsze pięć minut. To tłumaczy,
  czemu apka „jeszcze nie czuć”.
- Wzmacnia [ADR-0001](0001-narzedzie-do-myslenia-nie-robo-doradca.md) (narzędzie do
  myślenia) i [ADR-0003](0003-eod-dlugoterminowy-nie-day-trading.md) (długi horyzont):
  odpowiedzialność ma sens wyłącznie rozłożona w czasie.
