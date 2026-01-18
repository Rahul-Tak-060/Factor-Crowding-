# Factor Crowding and Drawdown Risk: Design Document

## Title

**Factor Crowding and Drawdown Risk: Do Crowded Factors Crash Harder in Stress?**

---

## 1. Objective

Test whether "crowding" in common equity factors (Momentum, Value, Low Vol) is associated with:

1. Higher probability of large drawdowns, and
2. Larger drawdown severity during stress periods.

---

## 2. Core Hypotheses

**H1 (Crowding to crash):** When a factor is crowded, subsequent downside tail risk increases.

**H2 (Stress amplification):** In high stress regimes (high VIX), crowded factors experience larger drawdowns.

**H3 (Cross-factor crowding):** When correlations among factor proxies rise, diversification fails and drawdowns deepen.

---

## 3. Data

### Primary Factor Series

* **Fama-French daily factor returns:** `Mkt-RF`, `SMB`, `HML`, `Mom`, `RF`
* Source: [Kenneth French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)

### Stress Proxy

* **VIX daily close** (FRED VIXCLS)
* Source: [Federal Reserve Economic Data](https://fred.stlouisfed.org/series/VIXCLS)

### Factor Proxy ETFs

* **MTUM** (Momentum) - iShares MSCI USA Momentum Factor ETF
* **VLUE** (Value) - iShares MSCI USA Value Factor ETF
* **USMV** (Low Vol) - iShares MSCI USA Min Vol Factor ETF

**Data fields needed (daily):**
- Adjusted close (returns)
- Volume (liquidity and attention proxy)

**Source:** Yahoo Finance historical data

### Sampling

* **Frequency:** Daily
* **Start date:** Earliest common overlap of all sources (typically ~2013 for ETFs)
* **Alignment:** Careful handling of VIX holidays vs equity trading days

---

## 4. Factor Crowding Definitions

Define crowding as a score computed daily (or weekly) from z-scored components.

### Crowding Proxy Set A: Flow-Attention Proxy (ETF based)

Components:
- **Volume z-score** (rolling 63 trading days)
- **Return run-up z-score** (rolling 126 trading days)
- **Short-term reversal risk** (negative skew or large down days frequency, rolling 63 days)

### Crowding Proxy Set B: Co-movement / Correlation Proxy

Components:
- Rolling correlation between MTUM and USMV returns
- Rolling correlation between MTUM and VLUE returns
- Rolling average pairwise correlation among the 3 ETFs

**Interpretation:** Higher correlation suggests factor trades moving together → potential crowded unwinds.

### Crowding Proxy Set C: Factor-Side Proxy (French Factors)

Components:
- **Rolling factor volatility** (Mom volatility spike as crowding risk proxy)
- **Rolling autocorrelation** (crowded trend chasing may show persistence then crash)

### Final Crowding Index

```
CrowdingIndex = mean(z_components)
```

With winsorization at 1st/99th percentile to handle outliers.

---

## 5. Defining "Crash" and Drawdowns

### Compute Drawdowns On

* **Mom factor** (French)
* **MTUM ETF** (proxy)

### Crash Events

* **Daily crash:** Return < 1st percentile of its own history
* **Weekly crash:** 5-day return < 1st percentile
* **Drawdown episode:** Peak-to-trough drawdown exceeding X% (default: 5%)

### Drawdown Metrics

* **Maximum drawdown:** Largest peak-to-trough decline
* **Episode duration:** Days from peak to recovery
* **Episode depth:** Percentage decline from peak to trough

---

## 6. Stress Regimes

Define stress regime using VIX:

* **High stress:** VIX above its rolling 75th percentile
* **Normal:** Middle band (25th to 75th percentile)
* **Low stress:** Below rolling 25th percentile

Rolling window: 252 trading days (1 year)

---

## 7. Analyses

### A) Descriptive

* Plot crowding index over time with labeled major stress windows
* Compare drawdown distributions in low vs high crowding periods
* Summary statistics by regime

### B) Predictive Tests

* **Logistic regression:** Predict crash indicator from crowding index, controlling for:
  - Recent volatility (20-day rolling std)
  - Market returns (20-day cumulative)

* **Quantile regression:** Effect on 5th percentile returns (tail risk focus)

### C) Conditional Tests

* **Interaction model:** `Crash ~ Crowding × HighVIX`
* Test whether crowding effect amplifies during stress

### D) Forward Return Analysis

* Conditional average forward returns by crowding decile
* Windows: 5-day and 20-day forward returns

### E) Robustness

* Different rolling windows (63, 126, 252)
* Alternative crash thresholds (0.5%, 1%, 2%)
* Replace ETFs with factor returns only (address ETF microstructure concerns)

---

## 8. Metrics and Reporting

### Model Performance

* **AUC** for crash prediction
* **Precision/recall** for top decile crowding days
* **Confusion matrix**

### Economic Metrics

* Average forward 5d and 20d return conditional on crowding deciles
* Worst-case drawdown conditional on crowding deciles
* Maximum drawdown statistics by regime

---

## 9. Deliverables

### Code

* Reproducible pipeline (download → clean → features → model → report)
* All modules with type hints and comprehensive tests
* CLI interface for easy execution

### Documentation

* README with setup and usage instructions
* This design document
* Inline code documentation

### Outputs

* **Figures folder** with all charts saved as PNG (300 DPI)
* **Processed data** saved to CSV for reproducibility
* **Research note** summarizing:
  - Hypotheses
  - Methodology
  - Results
  - Limitations
  - Practical implications for risk management

---

## 10. Limitations (State Explicitly)

### Data Limitations

* **ETF volume is a noisy proxy** for crowding and not equal to positioning
* **No true institutional positioning data** available publicly
* **Survivorship bias** in ETF selection
* **Index methodology effects** for factor ETF construction

### Methodological Limitations

* **Results are correlational, not causal**
* **Sample period dependency** (results may not generalize)
* **Look-ahead bias** must be carefully avoided in feature construction
* **Multiple testing** concerns (testing multiple hypotheses)

### Interpretation Limitations

* Cannot distinguish between:
  - Smart money exiting vs
  - Forced selling vs
  - Fundamental deterioration
* ETF flows ≠ factor exposure changes in institutional portfolios

---

## 11. Extensions for Future Work

* **Additional factors:** Quality, Low Beta, Profitability
* **Alternative crowding measures:**
  - Mutual fund flows
  - Options market implied correlation
  - Analyst crowding metrics
* **International markets:** Extend to European and Asian factors
* **Machine learning models:** Random Forest, XGBoost for nonlinear effects
* **Regime-switching models:** Markov-switching framework
* **High-frequency analysis:** Intraday patterns during unwinds

---

## 12. Implementation Timeline

### Phase 1: Data and Infrastructure (Week 1)
- [x] Set up project structure
- [x] Implement data download modules
- [x] Create data cleaning pipeline
- [x] Set up testing infrastructure

### Phase 2: Feature Engineering (Week 2)
- [x] Implement crowding proxy A (flow-attention)
- [x] Implement crowding proxy B (co-movement)
- [x] Implement crowding proxy C (factor-side)
- [x] Combine into composite indices

### Phase 3: Analysis (Week 3)
- [x] Drawdown computation
- [x] Crash event identification
- [x] Stress regime classification
- [x] Descriptive statistics

### Phase 4: Modeling (Week 4)
- [x] Logistic regression models
- [x] Quantile regression
- [x] Conditional analysis
- [x] Robustness checks

### Phase 5: Reporting (Week 5)
- [x] Generate all figures
- [ ] Write research note
- [ ] Create presentation
- [ ] Publish on GitHub

---

## 13. References

### Academic Literature

* **Momentum crashes:**
  - Daniel, K., & Moskowitz, T. J. (2016). Momentum crashes. *Journal of Financial Economics*.

* **Crowding and liquidity:**
  - Lou, D., & Polk, C. (2013). Comomentum: Inferring arbitrage activity from return correlations. *Review of Financial Studies*.

* **Factor investing:**
  - Fama, E. F., & French, K. R. (2015). A five-factor asset pricing model. *Journal of Financial Economics*.

### Data Sources

* Kenneth French Data Library: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html
* FRED Economic Data: https://fred.stlouisfed.org/
* Yahoo Finance: https://finance.yahoo.com/

---

**Document Version:** 1.0
**Last Updated:** January 2026
**Status:** Implementation Complete
