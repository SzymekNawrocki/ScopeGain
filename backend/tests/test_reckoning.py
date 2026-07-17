"""Testy rozliczenia typu (analysis.build_reckoning, Etap 5).

CZYSTA funkcja: obserwacje + ceny -> wiersze + hit rate. Sedno decyzji z grilla:
rozliczamy CALA pule (nie tylko wygrane) i neutralnie (bez porady po fakcie).
"""

from datetime import date

from analysis import build_reckoning


def _obs(**kw) -> dict:
    baza = {
        "id": 1, "ticker": "CCJ", "name": "Cameco", "added_at": date(2026, 1, 1),
        "added_price": 62.0, "invalidation_price": None, "invalidation_note": None,
        "acted": False,
    }
    baza.update(kw)
    return baza


def test_ruch_od_dodania_liczony_w_procentach():
    out = build_reckoning([_obs(added_price=62.0)], {"CCJ": 71.0})
    row = out["rows"][0]
    assert row["move_pct"] == round((71 / 62 - 1) * 100, 2)   # ~+14.52
    assert row["current_price"] == 71.0
    assert out["summary"]["up"] == 1
    assert out["summary"]["down"] == 0


def test_brak_ceny_dodania_to_nie_liczymy_ruchu():
    # Rynek nie odpowiedzial przy dodaniu -> added_price None -> ruch None,
    # nie wchodzi do puli 'priced'. Uczciwie, nie zgadujemy.
    out = build_reckoning([_obs(added_price=None)], {"CCJ": 71.0})
    assert out["rows"][0]["move_pct"] is None
    assert out["summary"]["priced"] == 0


def test_uniewaznienie_cenowe_przebite():
    # prog 55, cena 50 -> przebite (dolny prog: mylilem sie).
    out = build_reckoning([_obs(invalidation_price=55.0)], {"CCJ": 50.0})
    assert out["rows"][0]["invalidation_triggered"] is True
    assert out["summary"]["invalidated"] == 1


def test_uniewaznienie_cenowe_trzyma():
    out = build_reckoning([_obs(invalidation_price=55.0)], {"CCJ": 60.0})
    assert out["rows"][0]["invalidation_triggered"] is False
    assert out["summary"]["invalidated"] == 0


def test_uniewaznienie_opisowe_to_None():
    # Tylko warunek slowny -> apka nie ocenia automatem, zostawia userowi.
    out = build_reckoning(
        [_obs(invalidation_price=None, invalidation_note="jesli deficyt uranu zniknie")],
        {"CCJ": 50.0},
    )
    assert out["rows"][0]["invalidation_triggered"] is None


def test_hit_rate_na_calej_puli():
    obs = [
        _obs(id=1, ticker="CCJ", added_price=62.0),           # up
        _obs(id=2, ticker="UEC", added_price=10.0),           # down
        _obs(id=3, ticker="URA", added_price=None),           # nieliczalne
        _obs(id=4, ticker="LEU", added_price=20.0, acted=True),  # up + acted
    ]
    prices = {"CCJ": 71.0, "UEC": 8.0, "LEU": 25.0}   # URA brak ceny
    out = build_reckoning(obs, prices)
    s = out["summary"]
    assert s["total"] == 4
    assert s["priced"] == 3      # URA odpada (brak ceny dodania)
    assert s["up"] == 2          # CCJ, LEU
    assert s["down"] == 1        # UEC
    assert s["acted"] == 1       # LEU


def test_ma_caveat_i_nie_gubi_typow():
    out = build_reckoning([_obs(), _obs(id=2, ticker="UEC")], {})
    assert out["caveat"]                       # zawsze jest zastrzezenie
    assert len(out["rows"]) == 2               # cala pula, nawet bez cen
    assert out["summary"]["total"] == 2
