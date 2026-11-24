# Methodology

Every criterion ScopeGain shows, with its formula, threshold and source. Thresholds
are fixed (ADR-0005). Where a threshold is a practitioner convention rather than a
number from the cited paper, it says so.

Inputs come from annual 10-K data (`facts.annual_financials`). `t` is the latest
fiscal year, `t-1` the year before. A missing input makes the criterion ⚪ (no data);
it is never filled with a guess, except where an assumption is listed explicitly.

## Trust

### Beneish M-Score — knock-out

Beneish (1999), eight-variable model:

```
M = -4.84 + 0.920·DSRI + 0.528·GMI + 0.404·AQI + 0.892·SGI
          + 0.115·DEPI - 0.172·SGAI + 4.679·TATA - 0.327·LVGI
```

| Index | Formula |
|---|---|
| DSRI | (Receivables/Sales)ₜ / (Receivables/Sales)ₜ₋₁ |
| GMI | Gross marginₜ₋₁ / Gross marginₜ |
| AQI | (1 − (CA + PPE)/TA)ₜ / (1 − (CA + PPE)/TA)ₜ₋₁ |
| SGI | Salesₜ / Salesₜ₋₁ |
| DEPI | (Dep/(Dep + PPE))ₜ₋₁ / (Dep/(Dep + PPE))ₜ |
| SGAI | (SG&A/Sales)ₜ / (SG&A/Sales)ₜ₋₁ |
| LVGI | ((CL + LTD)/TA)ₜ / ((CL + LTD)/TA)ₜ₋₁ |
| TATA | (Income from continuing operations − CFO)ₜ / TAₜ |

Threshold: **M > −1.78** flags likely manipulation (the cut-off reported by Beneish
1999). A flagged company gets 🔴 regardless of other criteria.
Assumption: when depreciation or SG&A is not reported, DEPI or SGAI is set to 1
(neutral) and the assumption is shown. These two have the smallest coefficients.
Not applied to financial companies (SIC 6000–6799).

### Piotroski F-Score

Piotroski (2000). Nine binary signals, scaled by beginning-of-year total assets:

1. ROA > 0
2. CFO > 0
3. ΔROA > 0
4. CFO/assets > ROA (earnings backed by cash)
5. Long-term debt / average assets did not rise
6. Current ratio rose
7. No share issuance (diluted share count did not rise)
8. Gross margin rose
9. Asset turnover rose

Piotroski calls 8–9 "high" and 0–1 "low". ScopeGain uses the common practitioner
tertiles: **≥ 7 pass, 4–6 warn, ≤ 3 fail**. Unknown signals never count as passed:
the outcome is decided only if it holds for every possible value of the unknowns.

### Altman Z-Score / Z''-Score

Manufacturers (SIC 2000–3999), Altman (1968):

```
Z = 1.2·X1 + 1.4·X2 + 3.3·X3 + 0.6·X4 + 1.0·X5
X1 = working capital / TA     X2 = retained earnings / TA
X3 = EBIT / TA                X4 = market value of equity / total liabilities
X5 = sales / TA
```

Zones: **> 2.99 safe, 1.81–2.99 grey, < 1.81 distress**.

Other non-financial companies, Altman, Hartzell & Peck (1995):

```
Z'' = 6.56·X1 + 3.26·X2 + 6.72·X3 + 1.05·X4   (X4 = book equity / total liabilities)
```

Zones: **> 2.60 safe, 1.10–2.60 grey, < 1.10 distress**. EBIT is taken as operating
income. Not applied to financial companies.

### Share dilution

Annual change of the diluted share count over up to three years. Share issuance
predicts lower returns (Pontiff & Woodgate 2008) and is one of Piotroski's signals.
Thresholds are a convention: **≤ 0% pass, 0–2% warn, > 2% fail**.

## Health

| Criterion | Formula | Pass | Warn | Fail | Source |
|---|---|---|---|---|---|
| Net debt / EBITDA | (LTD + current debt − cash) / (operating income + D&A) | < 3 or net cash | 3–4 | > 4 or EBITDA ≤ 0 | S&P Global Ratings (2013) financial risk profile |
| Interest coverage | EBIT / interest expense | ≥ 2.5 or no debt | 1.5–2.5 | < 1.5 | Damodaran, synthetic rating table (≥ 2.5 ≈ BBB or better) |
| Current ratio | current assets / current liabilities | ≥ 2 | 1–2 | < 1 | Graham (1973), ch. 14 |

None of these apply to financial companies (SIC 6000–6799).

## Valuation

| Criterion | Formula | Pass | Fail | Source |
|---|---|---|---|---|
| Graham multiplier | P/E × P/B = (market cap / net income) × (market cap / equity) | ≤ 22.5 | > 22.5, loss or negative equity | Graham (1973), ch. 14 |

Market capitalisation comes from Yahoo Finance; everything else from SEC filings.

## Verdict rule

Per block: pass = +1, warn = 0, fail = −1; criteria without data are skipped.
A block is 🟢 with no fail and a positive sum, 🔴 with a negative sum, 🟡 otherwise.

Overall, in this order:

1. 🔴 if a knock-out criterion fired (Beneish).
2. 🔴 if the Trust block is 🔴.
3. 🔴 if two or more blocks are 🔴.
4. 🟡 if fewer than half of the applicable criteria had data.
5. 🟢 if Trust is 🟢, no block is 🔴 and at least two blocks are 🟢.
6. 🟡 otherwise.

"Not applicable" (e.g. Altman for a bank) does not count as missing data.

## Statistics

### Industry percentiles (Health block)

Peers are companies registered under the same SIC code in EDGAR (company browse).
Their values come from the SEC XBRL `frames` API for the calendar year the company's
fiscal year mostly overlaps (fiscal years ending in July or later map to that year).

| Criterion | Company value | Peer value |
|---|---|---|
| Operating margin | operating income / revenue | `OperatingIncomeLoss` / (`Revenues`, else `RevenueFromContractWithCustomerExcludingAssessedTax`) |
| ROA | net income / total assets | `NetIncomeLoss` / `Assets` (year-end instant) |

Percentile = share of peers below the company (ties count half). At least 10 peers
are needed. Cut-offs are a convention: **top third pass, middle warn, bottom third fail**.

### P/E against the company's own history (Valuation block)

P/E at each fiscal-year end = closing price on that date / diluted EPS of that year.
EPS is divided by every stock split that happened **after the filing date** (EPS is
stated on the share count at filing time; prices are split-adjusted to today). Prices
are split-adjusted but not dividend-adjusted. Today's P/E uses the latest close and
the latest annual EPS. At least 5 past profitable years are needed. Cut-offs:
**bottom third of its own history pass, middle warn, top third fail**.

## Dividend

### Net dividend in PLN (information, not a pass/fail criterion)

For a Polish tax resident on an ordinary brokerage account holding US shares:

| | With W-8BEN | Without W-8BEN |
|---|---|---|
| US withholding | 15% (PL-US treaty 1974, art. 11) | 30% (US statutory rate) |
| Credit in Poland | 15% | 15% (capped at the treaty rate) |
| Polish top-up to 19% (PIT-38, section G) | 4% | 4% |
| Kept | **81%** | **66%** |

The credit cap follows KIS interpretation 0113-KDIPT2-3.4011.303.2025.2.NM (27 May
2025) and NSA II FSK 1171/22. Some publications cite only the 19% limit; the app uses
the stricter reading. Net per 1000 PLN = 1000 × trailing-12-month dividend / price ×
kept share. The PLN amount uses today's NBP mid rate; the law uses the NBP rate from
the business day before payment. IKE/IKZE do not remove US withholding.

### Dividend safety

| Criterion | Formula | Pass | Warn | Fail | Source |
|---|---|---|---|---|---|
| Payout from FCF | dividends paid / (CFO − capex) | ≤ 75% | 75–100% | > 100% or FCF ≤ 0 | fact above 100%; 75% is a convention |
| Years without a cut | consecutive full years where the regular payment (median per year) did not fall by more than 1% | ≥ 10 | 5–9 | < 5 | Nasdaq US Broad Dividend Achievers (10 years of increases), milder test |

Companies that pay no dividend get "not applicable" for the whole block.
