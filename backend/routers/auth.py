from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import UserCredentials, UserRead
from security import (
    COOKIE_NAME,
    TOKEN_TTL_HOURS,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookie(response: Response, user_id: int) -> None:
    """Wklada podpisany token do httpOnly cookie. httponly=True -> JavaScript
    w przegladarce GO NIE WIDZI (ochrona przed kradzieza tokenu przez XSS).
    samesite='lax' + brak Secure dziala lokalnie (http, ten sam host localhost);
    na produkcji (https) doszloby secure=True."""
    response.set_cookie(
        key=COOKIE_NAME,
        value=create_access_token(user_id),
        httponly=True,
        samesite="lax",
        secure=False,                       # lokalnie po http; na prod -> True
        max_age=TOKEN_TTL_HOURS * 3600,     # zycie cookie zgrane z zyciem tokenu
        path="/",
    )


@router.post("/register", response_model=UserRead, status_code=201)
def register(dane: UserCredentials, response: Response, db: Session = Depends(get_db)):
    email = dane.email.strip().lower()
    # Czy email juz zajety? Sprawdzamy grzecznie (400), zamiast czekac na
    # wybuch unikalnego indeksu w bazie.
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=400, detail="Ten email jest juz zajety.")

    user = User(email=email, password_hash=hash_password(dane.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    # Od razu logujemy po rejestracji - user nie musi wpisywac danych drugi raz.
    _set_auth_cookie(response, user.id)
    return user


@router.post("/login", response_model=UserRead)
def login(dane: UserCredentials, response: Response, db: Session = Depends(get_db)):
    email = dane.email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    # Ten sam komunikat dla zlego emaila i zlego hasla - nie zdradzamy,
    # ktore konto istnieje (drobna higiena bezpieczenstwa).
    if user is None or not verify_password(dane.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Zly email lub haslo.")

    _set_auth_cookie(response, user.id)
    return user


@router.post("/logout")
def logout(response: Response):
    # Kasujemy cookie -> kolejne zadania beda "niezalogowane".
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"ok": True}


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)):
    # Front wola to na starcie: jest cookie -> zwraca usera, brak -> 401.
    return user
