Below is a locked dataset plan, an initial design doc you can paste into your repo as `docs/design.md`, and a scaffold prompt you can drop into GitHub Copilot Chat to generate the project skeleton.

---

## Finalized dataset plan

### A) Academic factor returns (ground truth for “factor crash”)

Use **daily** and optionally **monthly** factor returns from Kenneth French Data Library.

* Daily Momentum factor (Mom, aka UMD) details and construction notes ([Tuck School of Business][1])
* Monthly Momentum factor details ([Tuck School of Business][2])
* General Fama-French factors library landing page ([Tuck School of Business][3])

**You will use (at minimum):**

* `Mkt-RF`, `SMB`, `HML`, `Mom`, `RF`

### B) Market stress and “risk-off” proxy

Use **VIX daily close** from FRED.

* VIXCLS series description ([FRED][4])

### C) Real-world “crowding proxies” (implementable, no paywalled data)

Use ETF proxies as “positioning / popularity” signals (not perfect, but defensible if you explain it correctly).

* Momentum proxy: **MTUM** (iShares MSCI USA Momentum Factor ETF) ([BlackRock][5])
* Value proxy: **VLUE** (iShares MSCI USA Value Factor ETF) (pull prices from the same data source you use for MTUM)
* Low vol proxy: **USMV** (iShares MSCI USA Min Vol Factor ETF) (same)

**Data fields needed (daily):**

* Adjusted close (returns)
* Volume (liquidity and attention proxy)

**Where to pull ETF prices/volume**

* Yahoo Finance historical data is fine for this project (you will cite it in README as data source; it is commonly used in public research prototypes). ([Yahoo Finance][6])

**Important framing**
You are not claiming you can see true institutional positioning. You are testing whether simple crowding proxies (volume surges, sharp inflows implied by volume and price trend, rising cross factor correlation) precede factor drawdowns.

---

## Initial design doc (drop into `docs/design.md`)

### Title

**Factor Crowding and Drawdown Risk: Do Crowded Factors Crash Harder in Stress?**

### 1. Objective

Test whether “crowding” in common equity factors (Momentum, Value, Low Vol) is associated with:

1. higher probability of large drawdowns, and
2. larger drawdown severity during stress periods.

### 2. Core hypotheses

**H1 (Crowding to crash):** When a factor is crowded, subsequent downside tail risk increases.
**H2 (Stress amplification):** In high stress regimes (high VIX), crowded factors experience larger drawdowns.
**H3 (Cross-factor crowding):** When correlations among factor proxies rise, diversification fails and drawdowns deepen.

### 3. Data

**Primary factor series**

* Fama-French daily factor returns: `Mkt-RF`, `SMB`, `HML`, `Mom`, `RF` ([Tuck School of Business][1])

**Stress proxy**

* VIX daily close (FRED VIXCLS) ([FRED][4])

**Factor proxy ETFs**

* MTUM (Momentum), VLUE (Value), USMV (Low Vol) prices and volume (daily) ([BlackRock][5])

**Sampling**

* Daily frequency, start date: earliest common overlap of all sources.
* Align calendars, forward fill only where appropriate (VIX holidays vs equity days should be handled carefully).

### 4. Factor crowding definitions (you will implement 3, then compare)

Define crowding as a score computed daily (or weekly) from z-scored components.

**Crowding proxy set A: Flow-attention proxy (ETF based)**

* Volume z-score (rolling 63 trading days)
* Return run-up z-score (rolling 126 trading days)
* Short-term reversal risk (negative skew or large down days frequency, rolling 63 days)

**Crowding proxy set B: Co-movement / correlation proxy**

* Rolling correlation between MTUM and USMV returns
* Rolling correlation between MTUM and VLUE returns
* Rolling average pairwise correlation among the 3 ETFs
  Interpretation: higher correlation suggests factor trades moving together, potential crowded unwinds.

**Crowding proxy set C: Factor-side proxy (French factors)**

* Rolling factor volatility (Mom volatility spike as crowding risk proxy)
* Rolling autocorrelation (crowded trend chasing may show persistence then crash)

**Final crowding index**

* `CrowdingIndex = mean(z_components)` with winsorization at 1st/99th percentile.

### 5. Defining “crash” and drawdowns

Compute drawdowns on:

* Mom factor (French)
* MTUM ETF (proxy)

**Crash events**

* Daily crash: return < 1st percentile of its own history
* Weekly crash: 5-day return < 1st percentile
* Drawdown episode: peak-to-trough drawdown exceeding X% (choose X after exploratory look, but lock it before final modeling)

### 6. Stress regimes

Define stress regime using VIX:

* High stress: VIX above its rolling 75th percentile
* Normal: middle band
* Low stress: below rolling 25th percentile
  VIX definition source ([FRED][4])

### 7. Analyses

**A) Descriptive**

* Plot crowding index over time with labeled major stress windows
* Compare drawdown distributions in low vs high crowding

**B) Predictive tests**

* Logistic regression: predict crash indicator from crowding index, controlling for recent volatility and market returns
* Quantile regression or tail-focused metrics: effect on 5th percentile returns

**C) Conditional tests**

* Interaction model: crowding * high VIX to test stress amplification

**D) Robustness**

* Different rolling windows (63, 126, 252)
* Alternative crash thresholds (0.5%, 1%, 2%)
* Replace ETFs with factor returns only (to show results not dependent on ETF microstructure)

### 8. Metrics and reporting

* AUC for crash prediction
* Precision/recall for top decile crowding days
* Average forward 5d and 20d return conditional on crowding deciles
* Worst-case drawdown conditional on crowding deciles

### 9. Deliverables

* Reproducible pipeline (download, clean, feature build, modeling, report)
* Figures folder with all charts saved
* A short research note in `report/`:

  * Hypotheses
  * Method
  * Results
  * Limitations
  * Practical implications for risk management

### 10. Limitations (state explicitly)

* ETF volume is a noisy proxy for crowding and not equal to positioning.
* Results are correlational, not causal.
* Survivorship and index methodology effects exist for ETF proxies. ([ETF Database][7])

---

## GitHub Copilot scaffold prompt (paste into Copilot Chat)

**Prompt:**

You are my coding assistant. Create a production-quality Python project scaffold for a quant research repo titled “factor-crowding-crash-risk”.

Constraints:

* Use Python 3.11
* Package manager: uv or poetry (choose one and include setup)
* Include type hints, logging, and minimal but real unit tests
* No notebooks as the main entry point. Notebooks optional later.
* Provide a CLI entry point: `python -m factor_crowding run --start YYYY-MM-DD --end YYYY-MM-DD`
* Structure must support reproducibility and easy extension.

Data sources to support (implement placeholders where API keys are needed):

1. Fama-French daily factors including Mom (download from Kenneth French Data Library)
2. FRED VIXCLS series
3. Yahoo Finance daily OHLCV for tickers: MTUM, VLUE, USMV

Pipeline requirements:

* `data/download.py`: functions to download and cache each dataset to `data/raw/`
* `data/clean.py`: align calendars, compute returns, handle missing days
* `features/crowding.py`: compute three crowding proxies:
  A) Volume z-score, return run-up z-score, crash frequency
  B) Rolling correlations among ETF returns
  C) Factor-side rolling volatility and autocorrelation
  Combine into a final `CrowdingIndex` with winsorization.
* `analysis/drawdowns.py`: compute drawdown series, crash flags (1st percentile daily and weekly)
* `models/predict.py`: logistic regression baseline predicting crash from CrowdingIndex, with interaction term for high VIX regime
* `report/figures.py`: save matplotlib figures to `outputs/figures/` with sensible filenames
* `config.py`: windows (63, 126, 252), quantile thresholds, tickers, file paths

Testing:

* tests for returns calculation, z-score, rolling correlation, drawdown logic.

Documentation:

* Generate a README with:

  * Setup
  * Data sources
  * How to run
  * How to reproduce figures
* Create `docs/design.md` placeholder with sections matching the design doc.

Deliver:

* Full folder tree
* Key files with starter implementations
* A small `Makefile` or `justfile` with commands: format, lint, test, run

Use only standard libs plus: pandas, numpy, scipy, statsmodels, scikit-learn, matplotlib, requests, yfinance.

Now generate the scaffold.

---

If you want, I can also give you a “definition of done” checklist and 6–8 plot ideas that will make the final report look like a real quant research memo.

[1]: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_mom_factor_daily.html?utm_source=chatgpt.com "Kenneth R. French - Detail for Daily Momentum Factor (Mom)"
[2]: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/Data_Library/det_mom_factor.html?utm_source=chatgpt.com "Kenneth R. French - Detail for Monthly Momentum Factor ..."
[3]: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html?utm_source=chatgpt.com "Kenneth R. French - Data Library"
[4]: https://fred.stlouisfed.org/series/VIXCLS?utm_source=chatgpt.com "CBOE Volatility Index: VIX (VIXCLS) | FRED | St. Louis Fed"
[5]: https://www.ishares.com/us/products/251614/ishares-msci-usa-momentum-factor-etf?utm_source=chatgpt.com "iShares MSCI USA Momentum Factor ETF | MTUM"
[6]: https://finance.yahoo.com/quote/RPV/history/?utm_source=chatgpt.com "Invesco S&P 500 Pure Value ETF (RPV) Stock Historical ..."
[7]: https://etfdb.com/etf/MTUM/?utm_source=chatgpt.com "MTUM iShares MSCI USA Momentum Factor ETF"
