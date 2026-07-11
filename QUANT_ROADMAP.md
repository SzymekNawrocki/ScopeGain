# Quant roadmap — od „opisuje przeszłość" do „pomaga użytkownikowi"

> **Kontekst (07/2026).** Po zbudowaniu warstw 1–6 + UX + auth (warstwa 5) padła
> szczera diagnoza: apka **opisuje przeszłość** (urosłeś 55%, Sharpe 1.2,
> skorelowane spółki), ale użytkownik po obejrzeniu myśli *„no i co z tego?"*.
> Brakuje funkcji „pod quanta", które dają realną wartość. Ten plik zbiera
> cztery kandydatury, żeby decyzja była świadoma i obronialna na rozmowie.

## Diagnoza luki

Wszystko, co apka dziś liczy, to **retrospekcja**. Skok jakościowy to odpowiedź
na dwa pytania użytkownika, których jeszcze nie ma:

1. **Spojrzenie w przód** — „co to znaczy dla MOICH pieniędzy za 20 lat".
2. **Konkret do działania** — „co mam zrobić dzisiaj".

## Napięcie, które trzeba nazwać

Research z Warstwy 12 (PLAN.md) mówi: dla inwestora indywidualnego realną wartość
dają **koszty, zachowanie, dywersyfikacja** — nie wyrafinowane sygnały. Więc
„cool quant" (Monte Carlo, granica efektywna) to często **piękna matematyka słabo
działająca out-of-sample**. To nie dyskwalifikuje tych funkcji — ale najmocniejszy
flex na rozmowie to *zbudować je i umieć skrytykować*, a nie udawać, że model
przewiduje rynek.

---

## Cztery kandydatury

### 1. Monte Carlo — „gdzie będę za 20 lat"
- **Co robi:** z historycznego zwrotu/zmienności portfela „rzuca kośćmi" tysiące
  ścieżek w przód → wachlarz (mediana, 10. i 90. percentyl) + „szansa na cel 1 mln".
- **Pytanie usera:** najbardziej osobiste — *„co ten portfel znaczy dla mojego życia?"*.
- **Nauka/obrona:** symulacja stochastyczna, rozkład normalny vs **bootstrap**
  (losowanie realnych dni — grube ogony rynku), percentyle, prawo wielkich liczb.
- **Trudność:** średnia. Czysta funkcja w `quant.py` (numpy `cumprod`), na froncie
  wachlarz — reużywa wieloliniowego `PerformanceChart`.
- **Haczyk / flex:** μ/σ z 2 lat hossy → projekcja kłamie w górę. Danie wyboru okna
  historii + jawne ostrzeżenie = dojrzałość.

### 2. Granica efektywna (Markowitz) — „ten sam zysk mniejszym ryzykiem?"
- **Co robi:** liczy front portfeli o najlepszym zwrocie na jednostkę ryzyka,
  zaznacza TWÓJ portfel (zwykle *pod* frontem) → „przeważ tak a tak".
- **Pytanie usera:** *„czy biorę ryzyko za darmo?"*.
- **Nauka/obrona:** nowoczesna teoria portfela (Nobel), macierz kowariancji,
  optymalizacja pod ograniczeniami, Sharpe jako nachylenie.
- **Trudność:** średnia-wyższa. Start: **losowanie tysięcy portfeli** (chmura kropek
  + front) zamiast `scipy.optimize` — „brzydko-że-działa”.
- **Haczyk:** optymalizacja na przeszłości **notorycznie zawodzi w przód** (dopasowanie
  do szumu). Najbardziej efektowna, najmniej „realnie pomaga” — chyba że z ostrzeżeniem.

### 3. Silnik rebalancingu (planowane **12c**) — „co konkretnie zrobić dziś"
- **Co robi:** porównuje wagi z docelowymi i mówi wprost: *sprzedaj NVDA za ~1200 zł,
  dokup VOO za ~900 zł*.
- **Pytanie usera:** najpraktyczniejsze — *„wiem że mam problem, co kliknąć?"*.
- **Nauka/obrona:** mniej ciężkiej matematyki, więcej **realnej wartości** — zgodne
  z własnym researchem (dywersyfikacja). Spina się z `analysis.py`, który **już
  wykrywa koncentrację** (`top_weight_pct`) — werdykt z „ostrzegam” → „oto lek”.
- **Trudność:** najniższa. Arytmetyka wag; głównie UX (skąd wagi docelowe).
- **Most między warstwami:** realny ruch rusza podatki/prowizje — jest już `net_pnl`
  (12a), więc można pokazać „ten ruch kosztuje Cię X Belki”.

### 4. VaR + stress test — „ile realnie mogę stracić"
- **Co robi:** **VaR** — „z 95% pewnością nie stracisz w miesiącu >1840 zł” (ryzyko w
  **złotówkach**). **Stress test** — odtwarza krachy (2008, COVID 03/2020) na dzisiejszym
  portfelu → „gdyby się powtórzyło, −41%”.
- **Pytanie usera:** *„jak bardzo mogę oberwać?”* — tak, że user to **czuje**.
- **Nauka/obrona:** VaR/**CVaR** (expected shortfall) to codzienny język działów
  ryzyka w bankach/funduszach. Metoda historyczna vs parametryczna, po co ogon.
- **Trudność:** niska-średnia. VaR historyczny = percentyl dziennych zwrotów × wartość.
  Stress = zwroty portfela z okna krachu przyłożone do dzisiejszej wartości.
- **Haczyk:** VaR usypia („95% OK”) — dokłada się CVaR.

---

## Rekomendacja kolejności

| Chcesz… | Bierz |
|---|---|
| żeby user pomyślał „to jest o MNIE" | **1. Monte Carlo** |
| najmocniejszy flex quant na rozmowę | **2. Granica efektywna** (z ostrzeżeniem) |
| realnie użyteczne, małym kosztem, zgodne z researchem | **3. Rebalancing** |
| język działu ryzyka, „czuć" stratę | **4. VaR / stress** |

**Proponowany porządek:** najpierw **Monte Carlo** (największe „aha” dla usera —
dokładnie ta luka), zaraz po nim **rebalancing** (domyka werdykt z „ostrzegam” na
„zrób to”). Granica efektywna i VaR jako kolejne — świetne, ale albo bardziej
ryzykowne poznawczo (#2), albo bardziej „ryzyko” niż „korzyść dla usera” (#4).

_Decyzja o wyborze — do podjęcia. Plik żywy: aktualizować po decyzji i po każdej
zbudowanej funkcji._
