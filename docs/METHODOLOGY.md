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
