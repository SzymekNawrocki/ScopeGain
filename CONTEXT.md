# ScopeGain domain context

The canonical language of this project. Definitions say **what a thing is**, not how
to build it. Decisions live in `docs/adr/` (start with
[ADR-0005](docs/adr/0005-local-objective-company-analyzer.md)).

Guiding rule: the app **says what it does not know** instead of guessing.

---

## What the app looks at

**Company** — a single listed company identified by its ticker. Analysis is about one
company at a time. _Avoid_: stock pick, position.

**Watchlist** — tickers the owner keeps an eye on, each with an optional note. It
remembers the last verdict so it can report a **Verdict change**. _Avoid_: portfolio,
theme, thesis.

## What the app says

**Verdict** — 🟢 worth considering / 🟡 borderline / 🔴 not worth it. It follows from a
fixed, documented rule over the **Blocks** ([METHODOLOGY](docs/METHODOLOGY.md#verdict-rule)),
never from anyone's opinion. It describes
the company today; it does not promise a return.

**Block** — a group of criteria: **Trust**, **Dividend**, **Valuation**, **Health**.
Each block shows how many criteria passed, failed or lacked data.

**Criterion** — one check with a value, a threshold and a **Source**. Outcome is
✅ passed, 🟡 middle zone (where the source defines one, e.g. Altman's grey zone),
❌ failed or ⚪ no data. "Not applicable" (e.g. Altman for a bank) is not a data gap.

**Knock-out criterion** — a criterion that ends the analysis with 🔴 on its own.
Currently: Beneish M-Score above the manipulation threshold.

**Pros and cons** — the passed and failed criteria written as plain arguments, each
with its number, threshold and what it means.

**Data gaps** — criteria that could not be checked. Shown above the verdict, because a
verdict from 5 criteria must not look as certain as one from 15.

**Source** — the publication a threshold comes from (e.g. Altman 1968). Shown next to
the criterion.

**Verdict change** — a watchlist company's verdict moved after a new report, with the
criterion that caused it (e.g. "🟢 → 🟡: Altman Z fell from 3.4 to 2.6").

## How the app measures

**Industry percentile** — where a company's metric sits among companies of the same
industry, from SEC `frames`. A statistic, not an opinion.

**Own-history valuation** — today's valuation multiple compared with the company's
own median over its available history.

**Net dividend (PLN)** — the forward dividend that lands in the owner's pocket: after
the source-country withholding tax and the Polish top-up to 19%, converted at the NBP
rate. _Avoid_: dividend yield (that is gross).

**Dividend safety** — whether the dividend is covered by free cash flow, how leveraged
the company is and how long it has gone without a cut.

## What the app does not do

**Link-out** — a glossary entry that points to a free external tool instead of
rebuilding it (Biznesradar for Polish stocks, justETF for ETFs, stockanalysis.com for
long financial history). Rule: free and good elsewhere → link; paywalled → build here.
