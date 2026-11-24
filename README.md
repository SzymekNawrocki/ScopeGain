# ScopeGain

A private, local company analyzer. Type a ticker and get an objective verdict
(🟢 worth considering / 🟡 borderline / 🔴 not worth it) with pros and cons backed by
numbers, the published source of every threshold, and explicit data gaps.

See [ADR-0005](docs/adr/0005-local-objective-company-analyzer.md), [CONTEXT.md](CONTEXT.md)
and [PLAN.md](PLAN.md).

## Run

```sh
cp .env.example .env
docker compose up --build
```

- Frontend: http://127.0.0.1:3000
- API: http://127.0.0.1:8000 (docs at `/docs`)

Everything is published on 127.0.0.1 only. There is no login.

## Develop without Docker

```sh
cd backend
py -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m uvicorn main:app --reload --host 127.0.0.1

cd ../frontend
npm ci
npm run dev
```
