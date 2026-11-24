# ScopeGain plan

> A private, local, objective company analyzer. See
> [ADR-0005](docs/adr/0005-local-objective-company-analyzer.md) and [CONTEXT.md](CONTEXT.md).
> The previous portfolio/journal app is preserved under tag `v0-portfolio`.

## How we work

- One slice at a time; each slice is finished before the next starts.
- The owner approves each slice plan and checks the result by hand.
- Verification: `pytest`, `tsc`, `next build`, `docker compose up`.
- Local only: everything runs with `docker compose up` on 127.0.0.1.

## Stack

| Part | Choice |
|---|---|
| API | Python 3.12, FastAPI |
| Analysis | pandas, numpy, pure functions with tests |
| Data | SEC EDGAR (`companyfacts`, `frames`), yfinance, NBP API |
| Database | PostgreSQL 16 (cache), SQLAlchemy, Alembic |
| Frontend | Next.js, React, TypeScript, Tailwind |
| Run | Docker Compose, ports on 127.0.0.1 |
| CI | GitHub Actions: pytest, tsc, next build |

## Slices

- [x] **0. Cleanup** — tag `v0-portfolio`; remove portfolio, journal, Discover, charts
      and auth; ADR-0005; new CONTEXT and PLAN; Docker Compose; CI for tests.
- [x] **1. Data** — ticker → CIK, SEC `companyfacts`, cache in Postgres,
      max 10 requests/s, User-Agent from `.env`.
- [x] **2. Trust** — Piotroski F-Score, Altman Z-Score, Beneish M-Score (knock-out) as
      pure functions, tested on known examples from the literature.
- [x] **3. Company card** — verdict, pros and cons, data gaps. First usable version.
- [x] **4. Statistics** — industry percentiles from SEC `frames`; valuation against the
      company's own history.
- [x] **5. Net dividends (PLN)** — verify tax rules first (podatki.gov.pl, double tax
      treaties: PIT-38 vs PIT-36/ZG); NBP rates; dividend safety.
- [ ] **6. Watchlist** — ticker + note; verdict change with its reason after a new report.
- [ ] **7. Glossary with link-outs** — what a term means, whether ScopeGain computes it,
      and where to check it for free. Grows a little in every slice.

## Out of scope

Portfolio tracking, P&L, tax documents, charts, screeners, Polish-stock fundamentals
(link to Biznesradar), ETF analysis (link to justETF), cloud hosting, auth, ML.
