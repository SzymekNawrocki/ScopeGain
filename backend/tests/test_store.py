from datetime import datetime, timedelta, timezone

import pytest

from store import Store
from tests.helpers import memory_sessions


class Clock:
    def __init__(self):
        self.t = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def __call__(self):
        return self.t


def counting_fetch(calls: list):
    def fetch():
        calls.append(1)
        return {"v": len(calls)}
    return fetch


def test_fetches_once_within_ttl():
    clock, calls = Clock(), []
    store = Store(memory_sessions(), now=clock)
    fetch = counting_fetch(calls)
    assert store.cached("k", timedelta(hours=1), fetch) == {"v": 1}
    clock.t += timedelta(minutes=59)
    assert store.cached("k", timedelta(hours=1), fetch) == {"v": 1}
    assert len(calls) == 1


def test_refetches_after_ttl():
    clock, calls = Clock(), []
    store = Store(memory_sessions(), now=clock)
    fetch = counting_fetch(calls)
    store.cached("k", timedelta(hours=1), fetch)
    clock.t += timedelta(hours=2)
    assert store.cached("k", timedelta(hours=1), fetch) == {"v": 2}


def test_returns_stale_copy_when_source_fails():
    clock = Clock()
    store = Store(memory_sessions(), now=clock)
    store.cached("k", timedelta(hours=1), lambda: {"v": "old"})
    clock.t += timedelta(days=3)

    def broken():
        raise RuntimeError("SEC down")

    assert store.cached("k", timedelta(hours=1), broken) == {"v": "old"}


def test_raises_when_source_fails_and_nothing_cached():
    store = Store(memory_sessions())

    def broken():
        raise RuntimeError("SEC down")

    with pytest.raises(RuntimeError):
        store.cached("k", timedelta(hours=1), broken)
