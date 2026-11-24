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
