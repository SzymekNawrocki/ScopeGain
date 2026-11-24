from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from deps import sec_client
from models import VerdictChange, WatchItem
from routers import company as company_router
from sec import SecClient
from watch import diff, snapshot

router = APIRouter(prefix="/watchlist", tags=["watchlist"])

TICKER_RE = r"^[A-Za-z0-9.\-]{1,15}$"


class WatchCreate(BaseModel):
    ticker: str = Field(pattern=TICKER_RE)
    note: str = Field(default="", max_length=500)


class WatchUpdate(BaseModel):
    note: str = Field(max_length=500)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _item(w: WatchItem, last_change: VerdictChange | None) -> dict:
    return {
        "ticker": w.ticker,
        "note": w.note,
        "added_at": w.added_at,
        "checked_at": w.checked_at,
        "grade": w.last_grade,
        "fiscal_year_end": w.last_fiscal_year_end,
        "last_change": _change(last_change) if last_change else None,
    }


def _change(c: VerdictChange) -> dict:
    return {"ticker": c.ticker, "at": c.at, "from_grade": c.from_grade, "to_grade": c.to_grade,
            "fiscal_year_end": c.fiscal_year_end, "reasons": c.reasons}


def _last_changes(db: Session) -> dict[str, VerdictChange]:
    out: dict[str, VerdictChange] = {}
    for c in db.scalars(select(VerdictChange).order_by(VerdictChange.at)):
        out[c.ticker] = c
    return out


def check(w: WatchItem, sec: SecClient, db: Session) -> VerdictChange | None:
    """Re-run the analysis for one item; store a change when the grade moved."""
    try:
        analysis = company_router.run_analysis(w.ticker, sec)
    except HTTPException:
        return None
    snap = snapshot(analysis)
    reasons = diff(w.last_grade, w.last_snapshot, analysis["grade"], snap,
                   w.last_fiscal_year_end, analysis["fiscal_year_end"])
    change = None
    if reasons:
        change = VerdictChange(ticker=w.ticker, at=_now(), from_grade=w.last_grade,
                               to_grade=analysis["grade"],
                               fiscal_year_end=analysis["fiscal_year_end"], reasons=reasons)
        db.add(change)
    w.last_grade = analysis["grade"]
    w.last_snapshot = snap
    w.last_fiscal_year_end = analysis["fiscal_year_end"]
    w.checked_at = _now()
    return change


@router.get("")
def list_watchlist(db: Session = Depends(get_db)):
    last = _last_changes(db)
    items = db.scalars(select(WatchItem).order_by(WatchItem.ticker))
    return [_item(w, last.get(w.ticker)) for w in items]


@router.post("", status_code=201)
def add(body: WatchCreate, db: Session = Depends(get_db), sec: SecClient = Depends(sec_client)):
    ticker = body.ticker.upper()
    if db.get(WatchItem, ticker):
        raise HTTPException(status_code=409, detail=f"{ticker} już jest na liście.")
    w = WatchItem(ticker=ticker, note=body.note.strip(), added_at=_now())
    db.add(w)
    check(w, sec, db)  # baseline; no change is recorded on the first check
    db.commit()
    return _item(w, None)


@router.patch("/{ticker}")
def update(body: WatchUpdate, ticker: str = Path(pattern=TICKER_RE), db: Session = Depends(get_db)):
    w = db.get(WatchItem, ticker.upper())
    if not w:
        raise HTTPException(status_code=404, detail="Nie ma tej spółki na liście.")
    w.note = body.note.strip()
    db.commit()
    return _item(w, _last_changes(db).get(w.ticker))


@router.delete("/{ticker}", status_code=204)
def remove(ticker: str = Path(pattern=TICKER_RE), db: Session = Depends(get_db)):
    w = db.get(WatchItem, ticker.upper())
    if not w:
        raise HTTPException(status_code=404, detail="Nie ma tej spółki na liście.")
    db.delete(w)
    db.commit()


@router.post("/refresh")
def refresh(db: Session = Depends(get_db), sec: SecClient = Depends(sec_client)):
    changes = []
    for w in db.scalars(select(WatchItem)).all():
        c = check(w, sec, db)
        if c:
            changes.append(c)
    db.commit()
    return {"changes": [_change(c) for c in changes], "items": list_watchlist(db)}


@router.get("/changes")
def changes(db: Session = Depends(get_db)):
    rows = db.scalars(select(VerdictChange).order_by(VerdictChange.at.desc()).limit(100))
    return [_change(c) for c in rows]
