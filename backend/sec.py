"""SEC EDGAR client: ticker -> CIK, company facts, frames, submissions, SIC peers.

Everything goes through one rate-limited HTTP function and the database cache.
SEC asks every client to declare a User-Agent with a contact e-mail and to stay
under 10 requests/second (https://www.sec.gov/os/accessing-edgar-data).
The User-Agent comes only from the SEC_USER_AGENT environment variable.
"""

import os
import threading
import time
import xml.etree.ElementTree as ET
from datetime import timedelta
from typing import Callable

import requests

from store import Store

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
FRAME_URL = "https://data.sec.gov/api/xbrl/frames/us-gaap/{tag}/{unit}/{period}.json"
SIC_URL = (
    "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&SIC={sic}"
    "&type=10-K&owner=include&count=100&output=atom&start={start}"
)

TICKERS_TTL = timedelta(days=7)
FACTS_TTL = timedelta(days=1)
SUBMISSIONS_TTL = timedelta(days=1)
FRAME_TTL = timedelta(days=7)
SIC_TTL = timedelta(days=30)

MAX_RPS = 10
SIC_MAX_PAGES = 10  # 1000 companies per industry is plenty for a percentile

ATOM = "{http://www.w3.org/2005/Atom}"


class SecUnavailable(Exception):
    """SEC could not be reached or refused the request (not 'no such company')."""


class SecNotConfigured(SecUnavailable):
    """SEC_USER_AGENT is missing, so we do not call SEC at all."""


class RateLimiter:
    def __init__(self, per_second: int, clock: Callable[[], float] = time.monotonic,
                 sleep: Callable[[float], None] = time.sleep):
        self._interval = 1.0 / per_second
        self._clock = clock
        self._sleep = sleep
        self._next = 0.0
        self._lock = threading.Lock()

    def wait(self) -> None:
        with self._lock:
            now = self._clock()
            if now < self._next:
                self._sleep(self._next - now)
                now = self._next
            self._next = now + self._interval


class SecClient:
    def __init__(self, store: Store, user_agent: str | None = None,
                 http_get: Callable[..., requests.Response] = requests.get,
                 limiter: RateLimiter | None = None):
        self._store = store
        self._ua = user_agent if user_agent is not None else os.environ.get("SEC_USER_AGENT", "")
        self._get = http_get
        self._limiter = limiter or RateLimiter(MAX_RPS)

    # --- raw HTTP -----------------------------------------------------------

    def _fetch(self, url: str, kind: str = "json"):
        if not self._ua.strip() or "@" not in self._ua:
            raise SecNotConfigured(
                "SEC_USER_AGENT is not set in .env (format: 'ScopeGain you@example.com')."
            )
        self._limiter.wait()
        try:
            r = self._get(url, headers={"User-Agent": self._ua,
                                        "Accept-Encoding": "gzip, deflate"}, timeout=20)
        except requests.RequestException as e:
            raise SecUnavailable(f"SEC request failed: {e}") from e
        if r.status_code == 404:
            return None
        if r.status_code != 200:
            raise SecUnavailable(f"SEC returned {r.status_code} for {url}")
        return r.json() if kind == "json" else r.text

    def _cached_json(self, key: str, url: str, ttl: timedelta) -> dict | None:
        payload = self._store.cached(key, ttl, lambda: {"body": self._fetch(url)})
        return payload["body"]

    # --- public API ---------------------------------------------------------

    def ticker_map(self) -> dict[str, dict]:
        """{TICKER: {"cik": int, "title": str}} for every company SEC lists."""
        body = self._cached_json("tickers", TICKERS_URL, TICKERS_TTL) or {}
        out = {}
        for row in body.values():
            out[str(row["ticker"]).upper()] = {"cik": int(row["cik_str"]), "title": row["title"]}
        return out

    def cik_for(self, ticker: str) -> int | None:
        # SEC writes class shares with a dash (BRK-B); Yahoo uses a dot (BRK.B).
        t = ticker.upper().replace(".", "-")
        hit = self.ticker_map().get(t)
        return hit["cik"] if hit else None

    def company_facts(self, cik: int) -> dict | None:
        return self._cached_json(f"facts:{cik}", FACTS_URL.format(cik=cik), FACTS_TTL)

    def submissions(self, cik: int) -> dict | None:
        """Company metadata. Only the small fields we use are kept in the cache."""
        def fetch():
            body = self._fetch(SUBMISSIONS_URL.format(cik=cik))
            if body is None:
                return {"body": None}
            recent = body.get("filings", {}).get("recent", {})
            return {"body": {
                "name": body.get("name"),
                "sic": body.get("sic"),
                "sicDescription": body.get("sicDescription"),
                "fiscalYearEnd": body.get("fiscalYearEnd"),
                "recent": {
                    "form": recent.get("form", [])[:200],
                    "reportDate": recent.get("reportDate", [])[:200],
                    "filingDate": recent.get("filingDate", [])[:200],
                },
            }}
        return self._store.cached(f"submissions:{cik}", SUBMISSIONS_TTL, fetch)["body"]

    def frame(self, tag: str, period: str, unit: str = "USD") -> dict[int, float]:
        """{cik: value} for one concept across all filers (e.g. Revenues, CY2024)."""
        def fetch():
            body = self._fetch(FRAME_URL.format(tag=tag, unit=unit, period=period))
            data = (body or {}).get("data", [])
            return {"body": {str(d["cik"]): d["val"] for d in data}}
        body = self._store.cached(f"frame:{tag}:{unit}:{period}", FRAME_TTL, fetch)["body"]
        return {int(k): float(v) for k, v in body.items()}

    def sic_peers(self, sic: str) -> list[int]:
        """CIKs of companies registered under one SIC code (EDGAR company browse)."""
        def fetch():
            ciks: list[int] = []
            for page in range(SIC_MAX_PAGES):
                text = self._fetch(SIC_URL.format(sic=sic, start=page * 100), kind="text")
                if not text:
                    break
                found, has_next = parse_sic_atom(text)
                ciks.extend(found)
                if not has_next:
                    break
            return {"body": list(dict.fromkeys(ciks))}
        return self._store.cached(f"sic:{sic}", SIC_TTL, fetch)["body"]


def parse_sic_atom(text: str) -> tuple[list[int], bool]:
    """CIKs from one page of the EDGAR company-browse Atom feed + whether a next page exists."""
    root = ET.fromstring(text)
    ciks = []
    for entry in root.findall(f"{ATOM}entry"):
        cik = entry.find(f"{ATOM}content/{ATOM}company-info/{ATOM}cik")
        if cik is None:
            cik = entry.find("content/company-info/cik")
        if cik is not None and cik.text and cik.text.strip().isdigit():
            ciks.append(int(cik.text.strip()))
    has_next = any(link.get("rel") == "next" for link in root.findall(f"{ATOM}link"))
    return ciks, has_next
