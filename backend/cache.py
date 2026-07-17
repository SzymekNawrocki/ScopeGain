"""Cache z czasem zycia (TTL) - w pamieci procesu, bez bazy i bez zaleznosci.

Po co? Yahoo (yfinance) to darmowe, NIEOFICJALNE zrodlo bez klucza. Przy
podpowiedziach w wyszukiwarce (zapytanie na kazdy znak) i fundamentach
(.info NIE da sie pobrac hurtem - to strzal na spolke) limit zapytan sie
konczy, a wtedy leci 429 -> cala funkcja przestaje dzialac w losowych
momentach. Dane, o ktore chodzi, sa wolnozmienne: sektor spolki nie zmieni
sie do jutra. Stad TTL liczony w godzinach - tani i skuteczny.

functools.lru_cache NIE nadaje sie: nie ma TTL (trzymaloby stara cene w
nieskonczonosc).
"""

import functools
import threading
import time
from typing import Callable


def ttl_cache(
    ttl_seconds: float,
    *,
    now: Callable[[], float] = time.monotonic,
    maxsize: int = 256,
    cache_if: Callable[[object], bool] | None = None,
):
    """Dekorator: zapamietuje wynik funkcji na ttl_seconds.

    now: wstrzykiwany zegar - dzieki temu testy przesuwaja czas zamiast spac
    (patrz tests/test_cache.py). Domyslnie monotonic, a NIE time.time, bo
    monotonic nie cofnie sie przy zmianie czasu w systemie (zima/lato, NTP).

    maxsize: podpowiedzi tworza nowy klucz z KAZDEGO wpisanego znaku
    ("c", "ca", "cam"...), wiec bez limitu slownik rosnie w nieskonczonosc.

    cache_if: predykat "czy ten wynik warto zapamietac". Domyslnie zapamietujemy
    wszystko. Potrzebne, bo darmowe zrodlo potrafi oddac ODPOWIEDZ NIEPELNA
    (czesc pol brakuje) - a taka, zapisana na 12 h, pokazywalaby userowi
    okrojone dane przez pol dnia, mimo ze jedno ponowne pytanie by je
    naprawilo. Widziane na zywo: profil Cameco bez branzy i marzy.

    Owinieta funkcja dostaje .cache_clear() (jak w lru_cache) - do testow.
    """

    def dekorator(func):
        # klucz -> (kiedy_wygasa, wynik)
        magazyn: dict[tuple, tuple[float, object]] = {}
        # Zamek jest KONIECZNY: endpointy w tym projekcie to zwykle "def"
        # (nie "async def"), a takie trasy FastAPI odpala w PULI WATKOW.
        # Rownolegle zadania realnie wchodza tu naraz.
        zamek = threading.Lock()

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            klucz = (args, tuple(sorted(kwargs.items())))

            with zamek:
                wpis = magazyn.get(klucz)
                if wpis is not None and wpis[0] > now():
                    return wpis[1]
                if wpis is not None:
                    del magazyn[klucz]  # przeterminowany

            # UWAGA: pobieramy POZA zamkiem. Trzymanie zamka przez czas I/O
            # (1-3 s na .info) zablokowaloby wszystkie inne watki. Cena: dwa
            # rownolegle zimne zadania moga zdublowac strzal do Yahoo - przy
            # jednym uzytkowniku to nie problem, a zamek per-klucz to
            # zlozonosc bez wartosci.
            wynik = func(*args, **kwargs)

            # Wynik podejrzany (np. niepelna odpowiedz zrodla) - oddajemy go,
            # ale NIE zapamietujemy, zeby nastepne pytanie mialo szanse
            # dostac komplet.
            if cache_if is not None and not cache_if(wynik):
                return wynik

            with zamek:
                # Wyjatek tu nie dojdzie (poleci wyzej) i to jest CELOWE:
                # zacache'owany blad limitu zabetonowalby awarie na 12 h.
                # None natomiast cache'ujemy - "nie ma takiej spolki" to
                # trwaly fakt, nie chwilowa awaria.
                if len(magazyn) >= maxsize:
                    _zrob_miejsce(magazyn, now)
                magazyn[klucz] = (now() + ttl_seconds, wynik)

            return wynik

        def cache_clear() -> None:
            with zamek:
                magazyn.clear()

        wrapper.cache_clear = cache_clear  # type: ignore[attr-defined]
        return wrapper

    return dekorator


def _zrob_miejsce(magazyn: dict, now: Callable[[], float]) -> None:
    """Magazyn pelny: wywal przeterminowane, a jak nie ma - najblizszy konca.

    Wolane pod zamkiem. Najpierw sprzatamy smieci (za darmo), a dopiero gdy
    wszystko jest swieze, poswiecamy wpis o najkrotszym pozostalym zyciu.
    """
    teraz = now()
    przeterminowane = [k for k, (wygasa, _) in magazyn.items() if wygasa <= teraz]
    if przeterminowane:
        for k in przeterminowane:
            del magazyn[k]
        return
    najblizszy = min(magazyn, key=lambda k: magazyn[k][0])
    del magazyn[najblizszy]
