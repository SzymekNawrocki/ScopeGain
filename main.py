from fastapi import FastAPI

from routers import portfolios, stock

app = FastAPI(title="ScopeGain API")


@app.get("/health")
def health():
    return {"status": "ok"}


# Wpinamy routery (mini-aplikacje) do glownej apki. main.py nie musi juz
# znac szczegolow tras - kazdy obszar mieszka we wlasnym pliku w routers/.
app.include_router(stock.router)
app.include_router(portfolios.router)
