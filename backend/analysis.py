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
