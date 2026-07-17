"""Silnik werdyktu: zamienia policzone metryki w WNIOSKI po ludzku.

To jest "mozg" niezaleznego analityka - reguly, ktorych broker Ci nie da,
bo zarabia na Twoim handlu. CZYSTA funkcja: na wejsciu liczby, na wyjsciu
lista wnioskow + ocena. Zadnego HTTP, zadnego yfinance - latwe do testow
("podaj alpha -12, sprawdz, ze wychodzi czerwony wniosek").
"""

# Poziomy wagi wniosku (frontend zamieni je na 🟢/🟡/🔴).
GOOD, WARN, BAD = "good", "warn", "bad"


def _wniosek(severity: str, title: str, detail: str) -> dict:
    return {"severity": severity, "title": title, "detail": detail}


def build_verdict(
    *,
    benchmark_label: str,
    alpha_pct: float,
    sharpe: float,
    port_vol: float,
    bench_vol: float,
    avg_corr: float | None,
    n_tickers: int,
    top_weight_pct: float,
    top_ticker: str | None,
) -> dict:
    """Buduje liste wnioskow + ocene laczna na podstawie metryk portfela."""
    f: list[dict] = []

    # 1. Czy bijesz rynek? (alpha)
    if alpha_pct <= -5:
        f.append(_wniosek(BAD, "Przegrywasz z rynkiem",
                          f"Sam indeks {benchmark_label} dalby wiecej - Twoja alpha to {alpha_pct:+.1f}%."))
    elif alpha_pct < 5:
        f.append(_wniosek(WARN, "Idziesz z rynkiem",
                          f"Alpha {alpha_pct:+.1f}% - jestes blisko wyniku indeksu."))
    else:
        f.append(_wniosek(GOOD, "Bijesz rynek",
                          f"Alpha {alpha_pct:+.1f}% ponad indeks {benchmark_label}."))

    # 2. Czy zysk jest "zdrowy"? (Sharpe = zwrot na jednostke ryzyka)
    if sharpe < 0.5:
        f.append(_wniosek(BAD, "Slaby zysk za ryzyko",
                          f"Sharpe {sharpe:.2f} - malo zwrotu za podejmowane ryzyko."))
    elif sharpe < 1:
        f.append(_wniosek(WARN, "Przecietny zysk za ryzyko",
                          f"Sharpe {sharpe:.2f} - srednio."))
    else:
        f.append(_wniosek(GOOD, "Zdrowy zysk za ryzyko",
                          f"Sharpe {sharpe:.2f} - dobra relacja zysku do ryzyka."))

    # 3. Jak bardzo portfel buja w porownaniu z rynkiem? (zmiennosc)
    if bench_vol > 0:
        if port_vol / bench_vol > 1.3:
            f.append(_wniosek(WARN, "Bardziej rozchwiany niz rynek",
                              f"Zmiennosc {port_vol:.0f}% vs {bench_vol:.0f}% dla rynku."))
        else:
            f.append(_wniosek(GOOD, "Ryzyko pod kontrola",
                              f"Zmiennosc {port_vol:.0f}% vs {bench_vol:.0f}% dla rynku."))

    # 4. Czy ryzyko jest rozlozone? (dywersyfikacja przez korelacje)
    if n_tickers < 2:
        f.append(_wniosek(BAD, "Brak dywersyfikacji",
                          "Tylko jedna spolka - cale ryzyko w jednym miejscu."))
    elif avg_corr is not None:
        if avg_corr > 0.7:
            f.append(_wniosek(BAD, "Spolki chodza razem",
                              f"Srednia korelacja {avg_corr:.2f} - slaba dywersyfikacja."))
        elif avg_corr >= 0.4:
            f.append(_wniosek(WARN, "Umiarkowana dywersyfikacja",
                              f"Srednia korelacja {avg_corr:.2f}."))
        else:
            f.append(_wniosek(GOOD, "Dobra dywersyfikacja",
                              f"Srednia korelacja {avg_corr:.2f} - ryzyko niezle rozlozone."))

    # 5. Czy jedna pozycja nie rzadzi calym portfelem? (koncentracja)
    if n_tickers >= 2 and top_ticker is not None:
        if top_weight_pct > 60:
            f.append(_wniosek(BAD, "Zbyt skupiony portfel",
                              f"{top_weight_pct:.0f}% w {top_ticker} - jedna spolka decyduje o wyniku."))
        elif top_weight_pct >= 40:
            f.append(_wniosek(WARN, "Spora koncentracja",
                              f"{top_weight_pct:.0f}% portfela siedzi w {top_ticker}."))
        else:
            f.append(_wniosek(GOOD, "Pozycje rozsadnie rozlozone",
                              f"Najwieksza pozycja: {top_ticker} {top_weight_pct:.0f}%."))

    # Ocena laczna: 🟢 +1, 🟡 0, 🔴 -1 -> suma decyduje o werdykcie.
    punkty = sum({GOOD: 1, WARN: 0, BAD: -1}[w["severity"]] for w in f)
    if punkty >= 2:
        grade, label = GOOD, "mocny"
    elif punkty >= 0:
        grade, label = WARN, "przecietny"
    else:
        grade, label = BAD, "slaby"

    return {"grade": grade, "grade_label": label, "findings": f}


# --- Werdykt RYZYKA pojedynczej spolki -------------------------------------
# Uwaga na granice (ADR-0001): apka NIE mowi "kup/sprzedaj". Werdykt portfela
# wyzej ocenia JAKOSC ("mocny/przecietny/slaby") - o Twoim wlasnym portfelu to
# uczciwe. Przeniesienie tego slownika na pojedyncza spolke bylby zlamaniem
# ADR-0001 tylnymi drzwiami: "Cameco: MOCNY" czyta sie jak polecenie zakupu.
# Dlatego tutaj oceniamy WYLACZNIE RYZYKO i etykietujemy je ryzykiem.

# ODWROCONA semantyka severity - w tej funkcji (i tylko w niej):
#   GOOD = niskie ryzyko, BAD = wysokie ryzyko.
# Dzieki tej inwersji ta sama arytmetyka punktow co wyzej dziala bez zmian.

STOCK_VERDICT_CAVEAT = (
    "To ocena RYZYKA (jak mocno buja, jak gleboko spadala, jak wrazliwa na "
    "rynek) - nie ocena spolki i nie sygnal kup/sprzedaj. Liczymy z przeszlosci; "
    "fundamenty pochodza z darmowego zrodla i bywaja niepelne."
)


def build_stock_verdict(
    *,
    ticker: str,
    bench_label: str,
    volatility_pct: float,
    bench_vol: float,
    max_drawdown_pct: float,
    beta: float | None = None,
    trailing_pe: float | None = None,
    profit_margins: float | None = None,
) -> dict:
    """Werdykt RYZYKA jednej spolki. Zwraca {grade, grade_label, caveat,
    data_gaps, findings}.

    CELOWO NIE przyjmuje zwrotu ani alphy. "Bije rynek -> +1 punkt" przemycilby
    z powrotem ocene JAKOSCI i cicho zamienil ten werdykt w rekomendacje.
    Zwrot i alpha sa userowi pokazywane obok, jako kontekst - ale nie wchodza
    do oceny ryzyka.

    data_gaps: nazwy metryk, ktorych nie bylo. Bez tego werdykt policzony z
    2 regul wygladalby tak samo pewnie jak z 5 - a to by bylo klamstwo przez
    przemilczenie.
    """
    f: list[dict] = []
    braki: list[str] = []

    # 1. Zmiennosc vs rynek. Najbardziej wiarygodna regula - liczymy ja SAMI
    #    z cen, nie ufamy niczyim fundamentom.
    if bench_vol > 0:
        ile_razy = volatility_pct / bench_vol
        if ile_razy <= 1.2:
            f.append(_wniosek(GOOD, "Buja jak rynek",
                              f"Zmiennosc {volatility_pct:.0f}% vs {bench_vol:.0f}% dla {bench_label}."))
        elif ile_razy <= 1.8:
            f.append(_wniosek(WARN, "Buja mocniej niz rynek",
                              f"Zmiennosc {volatility_pct:.0f}% to {ile_razy:.1f}x rynek ({bench_vol:.0f}%)."))
        else:
            f.append(_wniosek(BAD, "Buja duzo mocniej niz rynek",
                              f"Zmiennosc {volatility_pct:.0f}% to az {ile_razy:.1f}x rynek ({bench_vol:.0f}%)."))
    else:
        braki.append("zmiennosc rynku")

    # 2. Max drawdown - ile spolka juz realnie potrafila stracic od szczytu.
    if max_drawdown_pct > -20:
        f.append(_wniosek(GOOD, "Plytkie obsuniecia",
                          f"Najgorszy zjazd od szczytu: {max_drawdown_pct:.0f}%."))
    elif max_drawdown_pct >= -40:
        f.append(_wniosek(WARN, "Spore obsuniecie w historii",
                          f"Najgorszy zjazd od szczytu: {max_drawdown_pct:.0f}%."))
    else:
        f.append(_wniosek(BAD, "Bardzo gleboki zjazd w historii",
                          f"Najgorszy zjazd od szczytu: {max_drawdown_pct:.0f}% - "
                          f"tyle juz raz zabralo."))

    # 3. Beta - jak mocno spolka rusza sie RAZEM Z RYNKIEM. To NIE to samo co
    #    zmiennosc wyzej: beta = korelacja x stosunek zmiennosci, wiec spolka
    #    moze bujac 4x mocniej niz rynek i miec bete 1.0, jesli buja na WLASNY
    #    rachunek (slaba korelacja). Dlatego mowimy tu wylacznie o ruchu z
    #    rynkiem - nazwanie niskiej bety "spokojna" przeczyloby regule 1.
    if beta is None:
        braki.append("beta")
    else:
        ruch = f"gdy rynek spada 10%, ta spolka srednio {beta * 10:.0f}%"
        if beta < 0.8:
            f.append(_wniosek(GOOD, "Slabiej reaguje na rynek",
                              f"Beta {beta:.2f} - {ruch}."))
        elif beta <= 1.1:
            f.append(_wniosek(GOOD, "Rusza sie jak rynek",
                              f"Beta {beta:.2f} - {ruch}."))
        elif beta <= 1.5:
            f.append(_wniosek(WARN, "Reaguje mocniej niz rynek",
                              f"Beta {beta:.2f} - {ruch}."))
        else:
            f.append(_wniosek(BAD, "Mocno rozhustana rynkiem",
                              f"Beta {beta:.2f} - {ruch}."))

    # 4. Marza zysku - jako RYZYKO FINANSOWE, nie jako "jakosc biznesu".
    #    Spolka, ktora traci pieniadze, moze potrzebowac finansowania.
    if profit_margins is None:
        braki.append("marza zysku")
    elif profit_margins > 0.10:
        f.append(_wniosek(GOOD, "Zarabia z zapasem",
                          f"Marza zysku {profit_margins * 100:.0f}% - zysk amortyzuje szoki."))
    elif profit_margins >= 0:
        f.append(_wniosek(WARN, "Cienka marza",
                          f"Marza zysku {profit_margins * 100:.1f}% - maly bufor na gorsze czasy."))
    else:
        f.append(_wniosek(BAD, "Spolka traci pieniadze",
                          f"Marza zysku {profit_margins * 100:.0f}% - ryzyko finansowania."))

    # 5. P/E jako RYZYKO WYCENY: wysokie P/E = w cenie siedza duze oczekiwania
    #    = boleśniejszy spadek, gdy sie nie spelnia.
    #    UWAGA: yfinance NIE odroznia "spolka nie ma zysku" od "Yahoo nie
    #    podalo" - obie sytuacje to None. To dwie rozne informacje o ryzyku,
    #    wiec NIE zgadujemy: pomijamy regule i mowimy o tym wprost.
    if trailing_pe is None or trailing_pe <= 0:
        braki.append("P/E")
    elif trailing_pe <= 25:
        f.append(_wniosek(GOOD, "Wycena bez wielkich oczekiwan",
                          f"P/E {trailing_pe:.0f} - cena nie zaklada cudow."))
    elif trailing_pe <= 50:
        f.append(_wniosek(WARN, "Wysoka wycena",
                          f"P/E {trailing_pe:.0f} - w cenie siedza spore oczekiwania."))
    else:
        f.append(_wniosek(BAD, "Bardzo wysoka wycena",
                          f"P/E {trailing_pe:.0f} - w cenie siedza duze oczekiwania; "
                          f"rozczarowanie boli podwojnie."))

    # Ta sama arytmetyka co w build_verdict - dziala dzieki inwersji severity.
    punkty = sum({GOOD: 1, WARN: 0, BAD: -1}[w["severity"]] for w in f)
    if punkty >= 2:
        grade, label = GOOD, "niskie ryzyko"
    elif punkty >= 0:
        grade, label = WARN, "podwyzszone ryzyko"
    else:
        grade, label = BAD, "wysokie ryzyko"

    return {
        "ticker": ticker.upper(),
        "grade": grade,
        "grade_label": label,
        "caveat": STOCK_VERDICT_CAVEAT,
        "data_gaps": braki,
        "findings": f,
    }


# Prog "istotnej" zmiany po sprzedazy: ponizej +/- tej wartosci uznajemy timing
# za neutralny (szum), a nie sygnal behawioralny.
BEHAVIOR_MOVE_PCT = 10.0

# Uczciwe zastrzezenie: porownujemy TYLKO cene sprzedazy z dzisiejsza. Nie wiemy,
# co zrobiles z gotowka (moze kupiles cos lepszego) - to sygnal o timingu jednej
# pozycji, nie werdykt o calej decyzji. Front pokazuje to jawnie.
BEHAVIOR_CAVEAT = (
    "Porownujemy tylko cene sprzedazy z dzisiejsza - nie wiemy, co zrobiles z "
    "gotowka. To sygnal o timingu pojedynczej pozycji, nie ocena calej decyzji."
)


def build_behavior_verdict(sells: list[dict]) -> dict:
    """Werdykt zachowania (12b): czy sprzedaze mialy dobry timing?

    Atakuje behavior gap (DALBAR: glowna przyczyna niedowazenia wyniku rynku to
    zle momenty wejscia/wyjscia, nie dobor aktywow). Dla KAZDEJ sprzedazy
    porownuje cene sprzedazy z dzisiejsza cena tej samej spolki:
    urosla po sprzedazy -> "za wczesnie" (zostawiles pieniadze na stole),
    spadla -> "dobre wyjscie". CZYSTA funkcja: na wejsciu liczby, na wyjsciu
    wnioski + ocena. Kazdy sell to dict: {ticker, quantity, sold_price,
    current_price, executed_at}.
    """
    f: list[dict] = []
    total_left = 0.0   # suma (cena_dzis - cena_sprzedazy) * ilosc po wszystkich sprzedazach

    for s in sells:
        if not s.get("sold_price") or s.get("current_price") is None:
            continue
        ilosc = float(s["quantity"])
        sprzedaz = float(s["sold_price"])
        dzis = float(s["current_price"])
        data = s.get("executed_at", "")
        zmiana_pct = (dzis / sprzedaz - 1) * 100
        roznica = (dzis - sprzedaz) * ilosc   # + = trzymanie byloby lepsze
        total_left += roznica

        if zmiana_pct >= BEHAVIOR_MOVE_PCT:
            f.append(_wniosek(
                BAD, f"Sprzedales za wczesnie: {s['ticker']}",
                f"Od sprzedazy ({data}) {s['ticker']} urosl o {zmiana_pct:+.1f}% - "
                f"trzymajac zostawiles na stole ok. {roznica:,.0f}.",
            ))
        elif zmiana_pct <= -BEHAVIOR_MOVE_PCT:
            f.append(_wniosek(
                GOOD, f"Dobre wyjscie: {s['ticker']}",
                f"Od sprzedazy ({data}) {s['ticker']} spadl o {zmiana_pct:.1f}% - "
                f"uniknales ok. {abs(roznica):,.0f} straty.",
            ))
        else:
            f.append(_wniosek(
                WARN, f"Neutralny timing: {s['ticker']}",
                f"Od sprzedazy ({data}) {s['ticker']} zmienil sie o {zmiana_pct:+.1f}% - "
                f"bez istotnej roznicy.",
            ))

    if not f:
        return {
            "grade": WARN, "grade_label": "brak danych",
            "total_left_on_table": 0.0, "caveat": BEHAVIOR_CAVEAT,
            "findings": [_wniosek(
                WARN, "Brak sprzedazy w logu",
                "Dodaj transakcje kupna/sprzedazy, zeby apka ocenila Twoj timing.",
            )],
        }

    # Ocena: liczy sie kierunek. Wiecej "za wczesnie" niz "dobre wyjscia" ->
    # timing kosztowal. Ta sama arytmetyka punktow co werdykt portfela.
    punkty = sum({GOOD: 1, WARN: 0, BAD: -1}[w["severity"]] for w in f)
    if punkty >= 1:
        grade, label = GOOD, "dobre decyzje"
    elif punkty == 0:
        grade, label = WARN, "mieszany timing"
    else:
        grade, label = BAD, "timing Cie kosztowal"

    return {
        "grade": grade,
        "grade_label": label,
        "total_left_on_table": round(total_left, 2),
        "caveat": BEHAVIOR_CAVEAT,
        "findings": f,
    }


# --- Rozliczenie typu (Etap 5) ---------------------------------------------
# Domyka petle "rozwazam -> rozliczam sie". Uczy DYSCYPLINY, nie zalu.
#
# Twarde granice (grill 07/2026):
#   - Liczymy na CALEJ puli typow (hit rate), nie tylko na wygranych - pokazanie
#     samych wygranych uczyloby FOMO (to sama krytyka, ktora user wytknal
#     filmikowi o day-tradingu).
#   - NIGDY "apka miala racje" / "trzeba bylo kupic" - to zlamaloby ADR-0001
#     tylnymi drzwiami (porada po fakcie). Odbijamy TWOJA decyzje, nie wydajemy
#     nowej. Stad neutralne liczby: ruch od dodania, stan uniewaznienia, acted.
#
# Uniewaznienie cenowe traktujemy jako DOLNY prog ("jak spadnie ponizej X,
# myle sie") - typowe dla dlugoterminowej tezy. `invalidation_triggered`:
#   True  = jest cena progu i biezaca <= prog,
#   False = jest cena progu i biezaca > prog,
#   None  = brak progu cenowego (uniewaznienie opisowe -> oceniasz recznie).

RECKONING_CAVEAT = (
    "To rozliczenie Twojej DYSCYPLINY, nie porada. Ruch liczymy od ceny z dnia "
    "dodania; apka nie mowi 'trzeba bylo kupic' - pokazuje calą pulę Twoich "
    "typow (nie tylko trafione), zebys widzial wlasny hit rate, a nie pojedyncze "
    "wygrane. Nie wiemy, co zrobiles z gotowka."
)


def build_reckoning(observations: list[dict], prices: dict[str, float]) -> dict:
    """Rozlicza typy w temacie. CZYSTA funkcja: obserwacje + ceny -> wiersze +
    podsumowanie (hit rate). Zero HTTP/yfinance.

    Kazda obserwacja to dict: {id, ticker, name, added_at, added_price,
    invalidation_price, invalidation_note, acted}. `prices` = {TICKER: cena_dzis}.
    """
    rows: list[dict] = []
    priced = up = down = invalidated = acted = 0

    for o in observations:
        ticker = str(o["ticker"]).upper()
        current = prices.get(ticker)
        added = o.get("added_price")
        inval_price = o.get("invalidation_price")

        move_pct = None
        if current is not None and added not in (None, 0):
            # `or 0.0` normalizuje -0.0 (brzydkie "-0.0%" tuz po dodaniu) do 0.0.
            move_pct = round((current / float(added) - 1) * 100, 2) or 0.0
            priced += 1
            if move_pct > 0:
                up += 1
            elif move_pct < 0:
                down += 1

        triggered = None
        if inval_price is not None and current is not None:
            triggered = current <= float(inval_price)
            if triggered:
                invalidated += 1

        if o.get("acted"):
            acted += 1

        rows.append({
            "id": o["id"],
            "ticker": ticker,
            "name": o.get("name") or ticker,
            "added_at": o.get("added_at"),
            "added_price": float(added) if added is not None else None,
            "current_price": current,
            "move_pct": move_pct,
            "invalidation_price": float(inval_price) if inval_price is not None else None,
            "invalidation_note": o.get("invalidation_note"),
            "invalidation_triggered": triggered,
            "acted": bool(o.get("acted")),
        })

    summary = {
        "total": len(observations),
        "priced": priced,
        "up": up,
        "down": down,
        "invalidated": invalidated,
        "acted": acted,
    }
    return {"rows": rows, "summary": summary, "caveat": RECKONING_CAVEAT}
