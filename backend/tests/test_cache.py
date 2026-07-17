"""Testy cache'u TTL z cache.py.

Cache stoi miedzy apka a Yahoo: jesli trzyma za dlugo, user oglada wczorajsza
cene jako "dzisiejsza"; jesli za krotko, limit zapytan sie konczy i apka
przestaje dzialac. Oba bledy sa ciche, wiec kazda granice sprawdzamy osobno.

Czas jest WSTRZYKIWANY (FakeClock), wiec testy sa natychmiastowe i nie
migoczaby przy wolnym CI - zadnego time.sleep.
"""

from cache import ttl_cache


class FakeClock:
    """Zegar sterowany recznie: t += 10 zamiast spania 10 sekund."""

    def __init__(self, t: float = 0.0):
        self.t = t

    def __call__(self) -> float:
        return self.t


def licznik_wywolan():
    """Funkcja, ktora liczy, ile razy naprawde ja wywolano (proxy za 'strzal
    do Yahoo'). Cache ma sprawic, ze ten licznik NIE rosnie."""
    wywolania = {"n": 0}

    def fn(x):
        wywolania["n"] += 1
        return f"wynik-{x}"

    return fn, wywolania


# --- trafienie i wygasniecie ------------------------------------------------

def test_drugie_wywolanie_w_ttl_nie_woła_funkcji():
    zegar = FakeClock()
    fn, w = licznik_wywolan()
    cached = ttl_cache(100, now=zegar)(fn)

    assert cached("AAPL") == "wynik-AAPL"
    assert cached("AAPL") == "wynik-AAPL"
    assert w["n"] == 1  # drugi raz poszedl z cache'u


def test_po_wygasnieciu_ttl_woła_ponownie():
    zegar = FakeClock()
    fn, w = licznik_wywolan()
    cached = ttl_cache(100, now=zegar)(fn)

    cached("AAPL")
    zegar.t += 101  # TTL minal
    cached("AAPL")
    assert w["n"] == 2


def test_tuz_przed_wygasnieciem_jeszcze_trafia():
    zegar = FakeClock()
    fn, w = licznik_wywolan()
    cached = ttl_cache(100, now=zegar)(fn)

    cached("AAPL")
    zegar.t += 99
    cached("AAPL")
    assert w["n"] == 1


# --- klucze -----------------------------------------------------------------

def test_rozne_argumenty_to_rozne_klucze():
    zegar = FakeClock()
    fn, w = licznik_wywolan()
    cached = ttl_cache(100, now=zegar)(fn)

    assert cached("AAPL") == "wynik-AAPL"
    assert cached("MSFT") == "wynik-MSFT"
    assert w["n"] == 2


def test_kwargs_licza_sie_do_klucza():
    zegar = FakeClock()
    wywolania = {"n": 0}

    @ttl_cache(100, now=zegar)
    def fn(x, limit=8):
        wywolania["n"] += 1
        return (x, limit)

    fn("uran", limit=8)
    fn("uran", limit=8)
    assert wywolania["n"] == 1
    fn("uran", limit=20)  # inny kwarg = inny klucz
    assert wywolania["n"] == 2


# --- co wolno, a czego nie wolno cache'owac ---------------------------------

def test_none_jest_cachowane():
    """'Nie ma takiej spolki' to trwaly fakt - nie ma po co pytac Yahoo znowu."""
    zegar = FakeClock()
    wywolania = {"n": 0}

    @ttl_cache(100, now=zegar)
    def fn(x):
        wywolania["n"] += 1
        return None

    assert fn("ZLYTICKER") is None
    assert fn("ZLYTICKER") is None
    assert wywolania["n"] == 1


def test_wyjatek_nie_jest_cachowany():
    """Kluczowe: zacache'owany blad limitu zabetonowalby awarie na cale TTL.
    Po ustaniu awarii kolejne wywolanie MUSI sprobowac ponownie."""
    zegar = FakeClock()
    stan = {"psuj": True, "n": 0}

    @ttl_cache(100, now=zegar)
    def fn(x):
        stan["n"] += 1
        if stan["psuj"]:
            raise RuntimeError("limit zapytan")
        return "ok"

    for _ in range(3):
        try:
            fn("AAPL")
        except RuntimeError:
            pass
    assert stan["n"] == 3  # kazda proba poszla do zrodla, nic sie nie zabetonowalo

    stan["psuj"] = False
    assert fn("AAPL") == "ok"


# --- maxsize ----------------------------------------------------------------

def test_maxsize_ogranicza_wzrost():
    """Podpowiedzi tworza klucz z kazdego wpisanego znaku - bez limitu
    slownik rosnie w nieskonczonosc."""
    zegar = FakeClock()
    fn, _ = licznik_wywolan()
    cached = ttl_cache(100, now=zegar, maxsize=3)(fn)

    for i in range(10):
        cached(f"q{i}")

    assert len(_magazyn(cached)) <= 3


def test_maxsize_najpierw_wywala_przeterminowane():
    zegar = FakeClock()
    fn, w = licznik_wywolan()
    cached = ttl_cache(100, now=zegar, maxsize=2)(fn)

    cached("stary")
    zegar.t += 101          # "stary" przeterminowany
    cached("nowy")
    cached("nowszy")        # magazyn pelny -> ofiara to "stary", nie "nowy"

    n_przed = w["n"]
    cached("nowy")          # nadal w cache'u?
    assert w["n"] == n_przed


# --- cache_clear ------------------------------------------------------------

def test_cache_clear_czysci():
    zegar = FakeClock()
    fn, w = licznik_wywolan()
    cached = ttl_cache(100, now=zegar)(fn)

    cached("AAPL")
    cached.cache_clear()
    cached("AAPL")
    assert w["n"] == 2


def _magazyn(cached_fn):
    """Podglad wnetrza domkniecia - tylko do testu maxsize."""
    for cell in cached_fn.__closure__ or ():
        if isinstance(cell.cell_contents, dict):
            return cell.cell_contents
    return {}
