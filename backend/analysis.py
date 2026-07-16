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
