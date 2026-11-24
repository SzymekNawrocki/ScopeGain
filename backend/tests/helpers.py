"""Builders for synthetic SEC payloads used across tests."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base
import models  # noqa: F401


def memory_sessions() -> sessionmaker:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def dur(year: int, val: float, filed: str | None = None, form: str = "10-K") -> dict:
    return {"start": f"{year - 1}-10-01", "end": f"{year}-09-30", "val": val,
            "form": form, "fp": "FY", "filed": filed or f"{year}-11-01"}


def inst(year: int, val: float, filed: str | None = None) -> dict:
    return {"end": f"{year}-09-30", "val": val, "form": "10-K", "fp": "FY",
            "filed": filed or f"{year}-11-01"}


def facts(tags: dict[str, list[dict]], unit_overrides: dict[str, str] | None = None) -> dict:
    units = unit_overrides or {}
    return {"entityName": "Test Corp", "facts": {"us-gaap": {
        tag: {"units": {units.get(tag, "USD"): entries}} for tag, entries in tags.items()
    }}}
