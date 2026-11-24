"""Shared singletons for the API (one SEC client per process)."""

from functools import lru_cache

from database import SessionLocal
from sec import SecClient
from store import Store


@lru_cache(maxsize=1)
def sec_client() -> SecClient:
    return SecClient(Store(SessionLocal))
