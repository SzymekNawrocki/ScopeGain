from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    # email = login. unique -> baza sama pilnuje, ze dwoch userow nie ma tego
    # samego adresu (drugi INSERT wybucha, lapiemy go w routerze -> 400).
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    # NIGDY nie trzymamy hasla jawnie - tylko jego hash (bcrypt). Nawet my
    # (wlasciciel bazy) nie odczytamy hasla; przy logowaniu porownujemy hashe.
    password_hash: Mapped[str] = mapped_column(String(255))

    # jeden user ma wiele portfeli.
    portfolios: Mapped[list["Portfolio"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    # klucz obcy: ten portfel nalezy do usera. Nullable, bo w bazie moga byc
    # stare portfele sprzed auth (osierocone) - nie chcemy, zeby migracja
    # wybuchla. W kodzie ZAWSZE ustawiamy user_id przy tworzeniu i filtrujemy
    # listy po zalogowanym userze, wiec osierocone po prostu sie nie pokazuja.
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), index=True
    )
    user: Mapped["User | None"] = relationship(back_populates="portfolios")

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
