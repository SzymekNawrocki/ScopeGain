import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import stock

app = FastAPI(title="ScopeGain API")

# CORS = przegladarka blokuje fetch z jednego "pochodzenia" (localhost:3000)
# do innego (localhost:8000), dopoki serwer sam nie powie "ufam temu frontowi".
# Bez ciasteczek (brak auth, ADR-0005), wiec allow_credentials zostaje False.
FRONTEND_ORIGINS = os.environ.get(
    "FRONTEND_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(stock.router)
