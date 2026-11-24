"""SQLAlchemy models (tables)."""

from datetime import datetime

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class SecCache(Base):
    """Raw SEC responses, keyed by URL-like key, with the time they were fetched.

    SEC data changes slowly (a company files a few times a year), and SEC asks
    clients to stay under 10 requests/second. Keeping responses here means a
    restart does not re-download everything, and one company analysis does not
    hit SEC again for a day.
    """

    __tablename__ = "sec_cache"

    key: Mapped[str] = mapped_column(String(300), primary_key=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    payload: Mapped[dict] = mapped_column(JSON)


class WatchItem(Base):
    """A ticker the owner keeps an eye on, with the last verdict seen for it."""

    __tablename__ = "watchlist"

    ticker: Mapped[str] = mapped_column(String(15), primary_key=True)
    note: Mapped[str] = mapped_column(String(500), default="")
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_grade: Mapped[str | None] = mapped_column(String(10), nullable=True)
    last_fiscal_year_end: Mapped[str | None] = mapped_column(String(10), nullable=True)
    # {criterion_id: {"name", "outcome", "display"}} from the last check
    last_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class VerdictChange(Base):
    """A watched company's verdict moved, with the criteria that moved it."""

    __tablename__ = "verdict_changes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(15), index=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    from_grade: Mapped[str | None] = mapped_column(String(10), nullable=True)
    to_grade: Mapped[str] = mapped_column(String(10))
    fiscal_year_end: Mapped[str | None] = mapped_column(String(10), nullable=True)
    reasons: Mapped[list] = mapped_column(JSON)
