# 5. ScopeGain is a local, objective company analyzer

Date: 2026-11-24
Status: accepted. Supersedes [ADR-0001](0001-narzedzie-do-myslenia-nie-robo-doradca.md),
[ADR-0002](0002-temat-jest-koszykiem-kuratorowanym.md) and
[ADR-0004](0004-konkurujemy-na-odpowiedzialnosci-nie-na-researchu.md).
[ADR-0003](0003-eod-dlugoterminowy-nie-day-trading.md) (end-of-day, long horizon) stays in force.

## Context

ScopeGain started as a portfolio piece for job interviews, then became an
"accountability journal" (ADR-0004): theses, invalidation levels, hit rate, realised
results. The owner now has a job and is about to invest real money. Three things changed:

- The CV goal is gone. The only user is the owner, with real money.
- Brokers (XTB, mBank) and free trackers (myfund.pl) already show positions, P&L, tax
  documents and charts. Rebuilding that adds nothing.
- The owner does not want to be graded. He wants the app to say plainly whether a
  company is worth it, with advanced pros and cons. "The money I make or lose is my grade."

## Decision

ScopeGain is a **private, local analyzer of individual companies**.

1. **Verdict.** For a ticker the app says 🟢 worth considering / 🟡 borderline /
   🔴 not worth it, with pros and cons backed by numbers and explicit data gaps.
   This replaces ADR-0001's "never say buy or don't buy".
2. **Objective, not personal.** Thresholds are fixed and come from published research,
   cited next to every criterion: Altman (1968), Piotroski (2000), Beneish (1999).
   Beneish is a knock-out criterion. Industry percentiles come from SEC `frames`;
   valuation is compared with the company's own history. No user-editable profile, no ML.
3. **Checklist, not a score.** Four blocks (Trust, Dividend, Valuation, Health); each
   criterion is ✅/❌/⚪ with its value and threshold. No single 0–100 number: it reads
   as a rating, hides data gaps and averages things that must not be averaged.
4. **Dividends** are shown net in PLN, forward-looking (withholding tax, top-up to 19%,
   NBP rate), plus dividend safety. Received dividends are not tracked.
5. **Data.** US companies via SEC EDGAR (`companyfacts`, `frames`) and yfinance.
   Polish stocks link out to Biznesradar; ETFs link out to justETF.
6. **Build vs link.** A feature that is free and good elsewhere becomes a link in the
   glossary. A feature behind a paywall is built here.
7. **Watchlist** keeps tickers with a note and shows verdict changes with the reason
   after a new quarterly report. It never grades the owner.
8. **Local only.** `docker compose`, ports on 127.0.0.1, no auth, no cloud, no CD.
   CI runs tests only.

Removed (kept under tag `v0-portfolio`): portfolios, positions, transactions,
valuation/P&L, Belka and fees, rebalancing, correlations, portfolio backtest, candle
charts, Discover, Themes, Observations/theses/invalidation/realisation/reckoning, auth.

## Consequences

- Most of the 2026 code is deleted. The tag keeps it recoverable with one checkout.
- The app is only as good as its data: anything missing is shown as ⚪, never guessed.
- A verdict describes the company today; it is not a promise of return.
- SEC requires a contact e-mail in the User-Agent. It lives only in the local `.env`.
