from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    # relacja: jeden portfel ma wiele pozycji.
    # back_populates laczy obie strony, zeby dzialalo w obie strony.
    positions: Mapped[list["Position"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan"
    )


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(10))
    quantity: Mapped[float] = mapped_column(Numeric(18, 4))     # ile sztuk
    buy_price: Mapped[float] = mapped_column(Numeric(18, 4))    # cena zakupu

    # klucz obcy: ta pozycja nalezy do portfela o tym id.
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"))

    # druga strona relacji - dostep do portfela z poziomu pozycji.
    portfolio: Mapped["Portfolio"] = relationship(back_populates="positions")
