"""Database-backed cache for SEC responses.

`cached(key, ttl, fetch)` returns the stored payload when it is younger than
`ttl`, otherwise calls `fetch()`, stores the result and returns it. When SEC is
unreachable and an old copy exists, the old copy is returned (stale beats
nothing; the analysis shows the report date anyway).
"""

from datetime import datetime, timedelta, timezone
from typing import Callable

from sqlalchemy.orm import Session, sessionmaker

from models import SecCache


class Store:
    def __init__(
        self,
        session_factory: sessionmaker,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ):
        self._sessions = session_factory
        self._now = now

    def cached(self, key: str, ttl: timedelta, fetch: Callable[[], dict]) -> dict:
        with self._sessions() as db:
            row = db.get(SecCache, key)
            if row is not None and self._now() - _aware(row.fetched_at) < ttl:
                return row.payload

        try:
            payload = fetch()
        except Exception:
            if row is not None:
                return row.payload
            raise

        with self._sessions() as db:
            _upsert(db, key, payload, self._now())
            db.commit()
        return payload


def _aware(value: datetime) -> datetime:
    # SQLite (tests) drops the timezone; Postgres keeps it.
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _upsert(db: Session, key: str, payload: dict, at: datetime) -> None:
    row = db.get(SecCache, key)
    if row is None:
        db.add(SecCache(key=key, fetched_at=at, payload=payload))
    else:
        row.fetched_at = at
        row.payload = payload
