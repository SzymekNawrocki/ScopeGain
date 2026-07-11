import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, portfolios, stock

app = FastAPI(title="ScopeGain API")

# CORS = przegladarka blokuje fetch z jednego "pochodzenia" (localhost:3000)
# do innego (localhost:8000), dopoki serwer sam nie powie "ufam temu frontowi".
# Ta lista to bialy wpis dozwolonych adresow frontu. Wiele -> po przecinku w env.
FRONTEND_ORIGINS = os.environ.get(
    "FRONTEND_ORIGINS", "http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],   # GET, POST, ... wszystkie
    allow_headers=["*"],   # dowolne naglowki (np. Content-Type)
)


@app.get("/health")
def health():
    return {"status": "ok"}


# Wpinamy routery (mini-aplikacje) do glownej apki. main.py nie musi juz
# znac szczegolow tras - kazdy obszar mieszka we wlasnym pliku w routers/.
app.include_router(auth.router)
app.include_router(stock.router)
app.include_router(portfolios.router)
