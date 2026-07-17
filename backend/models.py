from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text
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

    # relacja: jeden portfel ma wiele transakcji (log kupna/sprzedazy - warstwa 12b).
    transactions: Mapped[list["Transaction"]] = relationship(
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


class Transaction(Base):
    """Log kupna/sprzedazy (warstwa 12b) - APPEND-ONLY, obok pozycji.

    Pozycje mowia "co mam TERAZ". Transakcje mowia "co ZROBILEM i KIEDY" - tego
    stan pozycji nie pamieta. Dzieki temu werdykt zachowania umie powiedziec
    "sprzedales X 3 miesiace temu, od tamtej pory urosl o Y%" (behavior gap).
    Nie zastepuje pozycji - to osobna, historyczna prawda o decyzjach.
    """

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(10))
    side: Mapped[str] = mapped_column(String(4))               # "BUY" / "SELL"
    quantity: Mapped[float] = mapped_column(Numeric(18, 4))    # ile sztuk
    price: Mapped[float] = mapped_column(Numeric(18, 4))       # cena za sztuke w transakcji
    executed_at: Mapped[date] = mapped_column(Date)            # dzien transakcji

    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), index=True)
    portfolio: Mapped["Portfolio"] = relationship(back_populates="transactions")


class Theme(Base):
    """Temat (Etap B) - koszyk KURATOROWANY przez usera ("Uran", "Kwanty").

    NIE jest wynikiem wyszukiwarki ani branza (ADR-0002): apka podsuwa
    kandydatow z pochodzeniem, ale to user decyduje, kto wchodzi. Osobno od
    portfela - temat to "co rozwazam", portfel to "co mam".
    """

    __tablename__ = "themes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[date] = mapped_column(Date, default=date.today)

    # jak portfele: nullable dla ewentualnych osieroconych, w kodzie zawsze
    # ustawiane i filtrowane po zalogowanym userze.
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)

    observations: Mapped[list["Observation"]] = relationship(
        back_populates="theme", cascade="all, delete-orphan"
    )


class Observation(Base):
    """Obserwacja - spolka w temacie wraz z PLANEM decyzji (Etap 3).

    To nie sama spolka: to Twoj zapisany typ. Para (data, cena) z momentu
    dodania pozwala pozniej UCZCIWIE rozliczyc decyzje (Etap 5). Doszlo
    Uniewaznienie ("przy czym uznam, ze sie myle") - bez niego decyzji nie
    da sie rozliczyc z warunkiem porazki (lekcja z dyscypliny selekcji).
    """

    __tablename__ = "observations"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(15))          # CCO.TO, U-UN.TO tez
    name: Mapped[str] = mapped_column(String(255))           # nazwa czytelna spolki
    origin: Mapped[str] = mapped_column(String(100))         # Pochodzenie ("branza:uranium")

    thesis: Mapped[str] = mapped_column(Text)                # Teza (dlaczego dodalem)
    # Uniewaznienie: cena LUB napisany warunek (co najmniej jedno - pilnuje router).
    invalidation_note: Mapped[str | None] = mapped_column(Text)
    invalidation_price: Mapped[float | None] = mapped_column(Numeric(18, 4))
    entry_note: Mapped[str | None] = mapped_column(Text)     # opcjonalny warunek/cena wejscia

    added_at: Mapped[date] = mapped_column(Date, default=date.today)
    added_price: Mapped[float | None] = mapped_column(Numeric(18, 4))  # None gdy rynek nie odpowie
    acted: Mapped[bool] = mapped_column(Boolean, default=False)        # czy kupilem

    theme_id: Mapped[int] = mapped_column(ForeignKey("themes.id"), index=True)
    theme: Mapped["Theme"] = relationship(back_populates="observations")
