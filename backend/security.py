import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import User

# ------------------------------------------------------------------------
# Warstwa bezpieczenstwa (warstwa 5). Trzy rzeczy:
#   1. hashowanie hasel (bcrypt) - w bazie nigdy nie lezy jawne haslo,
#   2. token JWT - podpisany "bilet" potwierdzajacy, kim jest uzytkownik,
#   3. get_current_user - bramkarz czytajacy token z httpOnly cookie.
# ------------------------------------------------------------------------

# SECRET_KEY podpisuje tokeny. Kto go zna, moze sfalszowac dowolny token,
# dlatego na produkcji MUSI byc w zmiennej srodowiskowej (nie w kodzie).
# Dev-default pozwala odpalic lokalnie bez konfiguracji - ale ostrzegamy.
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-CHANGE-ME-in-production")
if SECRET_KEY == "dev-secret-CHANGE-ME-in-production":
    print("[security] UWAGA: uzywam domyslnego SECRET_KEY - ustaw wlasny w .env na produkcji.")

ALGORITHM = "HS256"                 # symetryczny podpis: ten sam klucz podpisuje i weryfikuje
TOKEN_TTL_HOURS = 24                # jak dlugo token jest wazny
COOKIE_NAME = "access_token"        # nazwa httpOnly cookie z tokenem


# --- HASLA ---

def hash_password(plain: str) -> str:
    """Haslo -> sol + hash bcrypt (jednokierunkowo). Wynik trzymamy w bazie."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Czy podane haslo pasuje do zapisanego hasha. bcrypt sam wyciaga sol."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# --- TOKEN JWT ---

def create_access_token(user_id: int) -> str:
    """Buduje podpisany token: 'sub' = id usera, 'exp' = kiedy wygasa."""
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_TTL_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# --- BRAMKARZ ---

def get_current_user(
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    """Dependency: czyta token z httpOnly cookie, weryfikuje podpis i termin,
    wczytuje usera z bazy. Kazdy blad -> 401 (front pokaze ekran logowania).
    Tras z tym dependency nie da sie ruszyc bez waznego tokenu."""
    niezalogowany = HTTPException(status_code=401, detail="Nie zalogowano.")
    if access_token is None:
        raise niezalogowany
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        # zly podpis, wygasly token, popsuty payload - wszystko to samo 401.
        raise niezalogowany

    user = db.get(User, user_id)
    if user is None:
        # token wazny, ale user skasowany - tez traktujemy jak niezalogowanego.
        raise niezalogowany
    return user
