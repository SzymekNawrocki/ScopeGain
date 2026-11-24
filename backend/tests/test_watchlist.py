import pytest
from fastapi.testclient import TestClient

from watch import diff, snapshot
from tests.helpers import memory_sessions


def analysis(grade, outcomes, fy="2024-12-31"):
    crits = [{"id": cid, "name": cid.upper(), "outcome": o, "display": d, "block": "trust"}
             for cid, (o, d) in outcomes.items()]
    return {"grade": grade, "fiscal_year_end": fy, "blocks": {"trust": {"criteria": crits}}}


# --- pure diff ---------------------------------------------------------------

def test_first_check_is_a_baseline_not_a_change():
    new = analysis("good", {"altman": ("pass", "3,40")})
    assert diff(None, None, "good", snapshot(new)) is None


def test_same_grade_is_not_a_change_even_if_numbers_move():
    old = snapshot(analysis("good", {"altman": ("pass", "3,40")}))
    new = snapshot(analysis("good", {"altman": ("pass", "3,10")}))
    assert diff("good", old, "good", new) is None


def test_change_names_the_criterion_that_moved_and_new_report():
    old = snapshot(analysis("good", {"altman": ("pass", "3,40"), "piotroski": ("pass", "8/9")}))
    new = snapshot(analysis("mixed", {"altman": ("warn", "2,60"), "piotroski": ("pass", "8/9")}))
    reasons = diff("good", old, "mixed", new, "2023-12-31", "2024-12-31")
    assert reasons[0] == "Nowy raport roczny: 2023-12-31 → 2024-12-31."
    assert reasons[1] == "ALTMAN: ✅ → 🟡 (3,40 → 2,60)"
    assert len(reasons) == 2


# --- API with a fake analysis -----------------------------------------------

@pytest.fixture
def api(monkeypatch):
    import main
    from database import get_db
    from deps import sec_client
    from routers import company as company_router

    sessions = memory_sessions()
    state = {"AAPL": analysis("good", {"altman": ("pass", "3,40")})}

    def fake_run(ticker, sec):
        return state[ticker.upper()]

    def db():
        s = sessions()
        try:
            yield s
        finally:
            s.close()

    monkeypatch.setattr(company_router, "run_analysis", fake_run)
    main.app.dependency_overrides[get_db] = db
    main.app.dependency_overrides[sec_client] = lambda: None
    yield TestClient(main.app), state
    main.app.dependency_overrides.clear()


def test_add_list_note_remove(api):
    client, _ = api
    r = client.post("/watchlist", json={"ticker": "aapl", "note": "dywidenda?"})
    assert r.status_code == 201 and r.json()["grade"] == "good"
    assert client.post("/watchlist", json={"ticker": "AAPL"}).status_code == 409
    assert client.patch("/watchlist/AAPL", json={"note": "nowa"}).json()["note"] == "nowa"
    assert [i["ticker"] for i in client.get("/watchlist").json()] == ["AAPL"]
    assert client.delete("/watchlist/AAPL").status_code == 204
    assert client.get("/watchlist").json() == []


def test_refresh_records_change_with_reason(api):
    client, state = api
    client.post("/watchlist", json={"ticker": "AAPL"})
    assert client.post("/watchlist/refresh").json()["changes"] == []

    state["AAPL"] = analysis("mixed", {"altman": ("warn", "2,60")}, fy="2025-12-31")
    out = client.post("/watchlist/refresh").json()
    assert len(out["changes"]) == 1
    change = out["changes"][0]
    assert (change["from_grade"], change["to_grade"]) == ("good", "mixed")
    assert "ALTMAN: ✅ → 🟡 (3,40 → 2,60)" in change["reasons"]
    assert out["items"][0]["last_change"]["to_grade"] == "mixed"
    assert len(client.get("/watchlist/changes").json()) == 1


def test_invalid_ticker_is_rejected(api):
    client, _ = api
    assert client.post("/watchlist", json={"ticker": "no spaces!"}).status_code == 422
