import yfinance as yf   # pobieracz kursów z giełdy

TICKER = "AAPL"          # symbol spółki (AAPL = Apple). Zmień, pobaw się.

# Pobierz kursy z ostatniego miesiąca.
# yfinance oddaje tabelę (DataFrame) z pandas: wiersz = jeden dzień giełdowy.
dane = yf.download(TICKER, period="1mo", interval="1d", progress=False)

# Kolumna "Close" = cena zamknięcia (kurs na koniec dnia).
zamkniecia = dane["Close"]

cena_poczatkowa = zamkniecia.iloc[0].item()   # pierwszy dzień w okresie
cena_koncowa    = zamkniecia.iloc[-1].item()  # ostatni dzień (najświeższy)

# TA linijka to cała geneza analizy inwestycyjnej:
zwrot = (cena_koncowa - cena_poczatkowa) / cena_poczatkowa

# Wypisz wynik po ludzku:
print(f"Spolka:            {TICKER}")
print(f"Cena poczatkowa:   {cena_poczatkowa:.2f} USD")
print(f"Cena koncowa:      {cena_koncowa:.2f} USD")
print(f"Zwrot za miesiac:  {zwrot * 100:+.2f}%")
