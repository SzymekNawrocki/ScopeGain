from fastapi import FastAPI   # nasz "kelner"

# Tworzymy aplikacje API. To jest cala restauracja.
app = FastAPI(title="ScopeGain API")

# @app.get("/health") mowi: "gdy ktos zapyta o adres /health, uruchom te funkcje".
# To jest jedno "danie w menu".
@app.get("/health")
def health():
    # FastAPI sam zamieni ten slownik Pythona na JSON (jezyk, ktorym gadaja API).
    return {"status": "ok"}
