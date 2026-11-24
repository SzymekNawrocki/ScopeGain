import pytest

from sec import RateLimiter, SecClient, SecNotConfigured, SecUnavailable, parse_sic_atom
from store import Store
from tests.helpers import memory_sessions

UA = "ScopeGain test@example.com"


class FakeResponse:
    def __init__(self, status=200, body=None, text=""):
        self.status_code, self._body, self.text = status, body, text

    def json(self):
        return self._body


class FakeHttp:
    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def __call__(self, url, headers=None, timeout=None):
        self.calls.append((url, headers))
        for prefix, resp in self.routes.items():
            if url.startswith(prefix):
                return resp
        return FakeResponse(404)


class NoWait(RateLimiter):
    def __init__(self):
        super().__init__(10)

    def wait(self):
        pass


def client(routes, ua=UA):
    http = FakeHttp(routes)
    return SecClient(Store(memory_sessions()), user_agent=ua, http_get=http, limiter=NoWait()), http


TICKERS = {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
           "1": {"cik_str": 1067983, "ticker": "BRK-B", "title": "Berkshire"}}


def test_ticker_to_cik_and_class_share_dot():
    sec, http = client({"https://www.sec.gov/files/company_tickers.json": FakeResponse(body=TICKERS)})
    assert sec.cik_for("aapl") == 320193
    assert sec.cik_for("BRK.B") == 1067983
    assert sec.cik_for("NOPE") is None
    assert len(http.calls) == 1  # later lookups come from the cache


def test_sends_declared_user_agent():
    sec, http = client({"https://www.sec.gov/files/": FakeResponse(body=TICKERS)})
    sec.ticker_map()
    assert http.calls[0][1]["User-Agent"] == UA


def test_refuses_to_call_sec_without_contact_user_agent():
    sec, http = client({}, ua="")
    with pytest.raises(SecNotConfigured):
        sec.ticker_map()
    assert http.calls == []


def test_server_error_is_unavailable_not_missing():
    sec, _ = client({"https://data.sec.gov/api/xbrl/companyfacts/": FakeResponse(503)})
    with pytest.raises(SecUnavailable):
        sec.company_facts(320193)


def test_missing_company_is_none():
    sec, _ = client({})
    assert sec.company_facts(1) is None


def test_frame_returns_cik_to_value():
    body = {"data": [{"cik": 1, "val": 10, "end": "2024-12-31"},
                     {"cik": 2, "val": 20.5, "end": "2024-12-31"}]}
    sec, _ = client({"https://data.sec.gov/api/xbrl/frames/us-gaap/Revenues/USD/CY2024.json":
                     FakeResponse(body=body)})
    assert sec.frame("Revenues", "CY2024") == {1: 10.0, 2: 20.5}


ATOM_PAGE = """<?xml version="1.0" encoding="ISO-8859-1" ?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <link href="https://www.sec.gov/cgi-bin/browse-edgar?start=100" rel="next" type="application/atom+xml" />
  <entry><content type="text/xml"><company-info><cik>0000320193</cik><name>Apple Inc.</name>
    <sic>3571</sic></company-info></content><title>Apple Inc.</title></entry>
  <entry><content type="text/xml"><company-info><cik>0000001234</cik></company-info></content></entry>
</feed>"""


def test_parse_sic_atom_reads_ciks_and_next_link():
    ciks, has_next = parse_sic_atom(ATOM_PAGE)
    assert ciks == [320193, 1234]
    assert has_next is True


def test_sic_peers_follows_pagination_until_no_next():
    last = ATOM_PAGE.replace('rel="next"', 'rel="self"').replace("0000320193", "0000000007")
    pages = {"start=0": ATOM_PAGE, "start=100": last}

    def http(url, headers=None, timeout=None):
        for k, v in pages.items():
            if url.endswith(k):
                return FakeResponse(text=v)
        return FakeResponse(404)

    sec = SecClient(Store(memory_sessions()), user_agent=UA, http_get=http, limiter=NoWait())
    assert sec.sic_peers("3571") == [320193, 1234, 7]


def test_rate_limiter_spaces_requests():
    t, slept = [0.0], []
    lim = RateLimiter(10, clock=lambda: t[0], sleep=lambda s: slept.append(s))
    lim.wait()
    lim.wait()
    assert slept == [pytest.approx(0.1)]
