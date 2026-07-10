import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Adres bazy: "sterownik://uzytkownik:haslo@host:port/nazwa_bazy".
# Domyslnie lokalny kontener; w warstwie 5 przeniesiemy sekret do .env.
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:scopegain@localhost:5432/scopegain",
)

# engine = pula polaczen do bazy. Jeden na cala aplikacje.
engine = create_engine(DATABASE_URL)

# SessionLocal = fabryka "sesji" - jedna sesja to jedna rozmowa z baza.
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Base = wspolny rodzic wszystkich modeli (tabel). Modele beda go dziedziczyc.
Base = declarative_base()
