# factor-crowding-crash-risk

Quant research project testing whether "crowded" equity factors exhibit higher drawdown and crash risk, especially during market stress.

## TL;DR

- **Question:** Do crowded factors crash harder, and does high VIX amplify the effect?
- **Universe:** Momentum, Value, Size, Market factors (Fama-French) + ETFs (MTUM, VLUE, USMV)
- **Crowding proxies:** ETF flow/attention signals, cross-factor co-movement, factor volatility and persistence
- **Outputs:** reproducible pipeline, 7 publication-quality figures, comprehensive datasets, and statistical reports

---

## Project structure

```
factor-crowding-crash-risk/
├── factor_crowding/          # Main package
│   ├── __init__.py
│   ├── cli.py               # Command-line interface
│   ├── config.py            # Configuration dataclasses
│   ├── data/
│   │   ├── download.py      # Fetch Fama-French, FRED, Yahoo Finance
│   │   └── clean.py         # Align calendars and compute returns
│   ├── features/
│   │   └── crowding.py      # Crowding index construction (24 signals)
│   ├── analysis/
│   │   └── drawdowns.py     # Crash and drawdown episode identification
│   ├── models/
│   │   └── predict.py       # Logistic regression for crash prediction
│   ├── report/
│   │   └── figures.py       # Publication-quality visualizations
│   └── utils/
│       └── __init__.py      # Logging utilities
├── tests/                   # Comprehensive test suite
│   ├── test_config.py
│   ├── test_clean.py
│   ├── test_crowding.py
│   ├── test_drawdowns.py
│   └── test_predict.py
├── data/                    # Data directory (gitignored)
│   ├── raw/                # Downloaded raw data
│   └── processed/          # Aligned and feature-engineered datasets
├── outputs/                 # Output directory (gitignored)
│   └── figures/            # Generated PNG figures
├── docs/                    # Documentation
│   ├── design.md           # Research design
│   ├── CODE_WALKTHROUGH.md # Annotated code examples
│   ├── QUICK_REFERENCE.md  # Code recipes
│   └── INDEX.md            # Navigation guide
├── CODE_ARCHITECTURE.md    # Complete learning roadmap
├── EXPLANATION.md          # Research concepts explained
├── RESULTS_SUMMARY.md      # Key findings and implications
├── pyproject.toml          # Project configuration
├── Makefile                # Automation tasks
└── README.md               # This file
```

---

## Data sources

- **Fama-French daily factors** ([Kenneth French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html))
  - Includes: Mkt-RF, SMB, HML, Mom (Momentum/UMD), RF
  - Daily returns from 1926 to present
- **FRED VIXCLS** ([Federal Reserve Economic Data](https://fred.stlouisfed.org/series/VIXCLS))
  - CBOE Volatility Index (market stress indicator)
- **Yahoo Finance** OHLCV for: `MTUM`, `VLUE`, `USMV`
  - Momentum, Value, and Low Volatility factor ETFs
  - Volume used as attention/flow proxy

**Note:** ETF volume is a noisy crowding proxy. This project treats it as attention and participation, not direct positioning.

---

## Setup

### Requirements

- Python 3.11+

### Install (choose one path)

#### Option A: uv (recommended)

```bash
# Clone the repository
git clone https://github.com/Rahul-Tak-060/Factor-Crowding-.git
cd Factor-Crowding-

# Install uv
pip install uv

# Create environment and install
uv venv
```

**Activate the virtual environment:**

macOS / Linux (bash/zsh):
```bash
source .venv/bin/activate
```

Windows PowerShell:
```powershell
.venv\Scripts\Activate.ps1
```

Windows cmd:
```cmd
.venv\Scripts\activate.bat
```

**Install dependencies:**
```bash
uv pip install -e ".[dev]"
```

#### Option B: poetry

```bash
poetry install
poetry shell
```

---

## Run the pipeline

### 1) Download and cache data

```bash
factor-crowding download --start 2013-01-01 --end 2024-12-31
```

### 2) Full run (features, crashes, model, figures)

```bash
factor-crowding run --start 2013-01-01 --end 2024-12-31
```

### 3) Outputs

- **Figures:** `outputs/figures/` (7 PNG files)
- **Datasets:** `data/processed/` (13 CSV files)
- **Model results:** `data/processed/model_results.txt`
- **Logs:** Check console output

### Individual commands

```bash
# View configuration
factor-crowding info

# Clean/align data only
factor-crowding clean --start 2013-01-01
```

---

## Methods overview

### Crowding index

We compute three proxy families, then combine into a composite index:

**1. ETF attention / flow proxy** (9 signals)
- Volume z-score (20-day rolling)
- Trailing run-up z-score (20-day cumulative returns)
- Return volatility (20-day std dev)
- For each ETF: MTUM, VLUE, USMV

**2. Co-movement proxy** (4 signals)
- Rolling pairwise correlations (20-day) among MTUM, VLUE, USMV
- Average cross-ETF correlation
- Interpretation: High correlation → crowded trades moving together

**3. Factor-side proxy** (8 signals)
- Rolling volatility of Fama-French factors (20-day)
- VIX level and changes
- Factor characteristic dispersion

**Final crowding index:**
- Equal-weighted mean of 24 z-scored components
- Winsorized at ±3σ to reduce outlier influence
- Smoothed with 20-day moving average
- Range: -2.20 (uncrowded) to +2.61 (extremely crowded)

### Crash and drawdown definitions

**Crash events:**
- **Daily crash:** Return below 1st percentile threshold
- **5-day crash:** 5-day cumulative return below 1st percentile
- Applied to each factor: Mkt-RF, SMB, HML, Mom

**Drawdown episodes:**
- Continuous periods where cumulative return is below running peak
- Episode starts when drawdown begins
- Episode ends when new high is reached
- Metrics computed: depth, duration, recovery time

### Stress regime

- **High VIX:** VIX above rolling 75th percentile (market stress)
- **Normal:** VIX between 25th and 75th percentile
- **Low VIX:** VIX below 25th percentile (complacency)

### Modeling

**Baseline logistic regression:**

```
crash_next_5d ~ crowding_index + vix + mom_vol_20d + mom_ret_20d + mkt_ret_20d + high_vix + crowding × high_vix
```

- **Target:** Binary indicator of crash in next 5 trading days
- **Features:** Crowding, market conditions, recent performance
- **Interaction term:** Tests if crowding is more dangerous during stress
- **Evaluation:** 80/20 train-test split, AUC metric

---

## Results snapshot

**Analysis Period:** April 19, 2013 to December 31, 2024 (3,174 trading days)

| Metric | Value |
|--------|-------|
| **Model AUC (test set)** | 0.88 (excellent) |
| **Crowding coefficient** | +0.60 (significant, positive) |
| **Total crash days identified** | ~30 per factor (1.02% of days) |
| **Drawdown episodes** | Mkt-RF: 14, Mom: 8, HML: 3, SMB: 2 |
| **Crowding range** | -2.20 to +2.61 (z-score units) |
| **High crowding days** | 56 days > +1.0 (1.9%) |

### Key takeaways

✅ **Crowding predicts crashes:** Logistic model achieves 88% AUC in out-of-sample testing

✅ **Momentum most vulnerable:** Despite moderate daily volatility (1.04%), Momentum has highest crash frequency (8 episodes) and worst tail risk

✅ **The crowding paradox:** High crowding periods show HIGHER average returns but MUCH higher volatility (50-60% increase) - classic "picking up pennies in front of a steamroller"

✅ **Hidden risk worse than obvious risk:** Crowding is most dangerous when VIX is LOW (complacency) - the combination of high crowding + low VIX predicts crashes better than high crowding + high VIX

✅ **Recent gains predict reversals:** Strongest predictor is 20-day market run-up (coef: +5.28) - "buy the top" effect before crashes

✅ **Validated against major events:** Model captures Taper Tantrum (2013), COVID crash (March 2020), and other known market dislocations

---

## Key Figures

### Crowding Index Over Time

![Crowding Index Timeseries](outputs/figures/crowding_index_timeseries.png)

The composite crowding index from 2013-2024, with high-VIX stress regimes indicated. Notice spikes during market dislocations (2018 vol spike, COVID crash, 2022 bear market).

### Crash Probability by Crowding Decile

![ROC Curve](outputs/figures/roc_curve.png)

Model performance showing excellent discrimination (AUC = 0.88). The curve demonstrates that crowding-based features effectively separate crash events from normal periods.

### Event Study Around Crash Dates

![Conditional Returns 5-Day](outputs/figures/conditional_returns_5d.png)

Average 5-day forward returns by crowding decile. High crowding deciles show significantly higher volatility and downside risk compared to low crowding periods.

---

## Reproduce the analysis

### Generated outputs

**Figures** (`outputs/figures/`):
- `crowding_index_timeseries.png` - Time evolution of crowding (2013-2024)
- `top_drawdown_episodes.png` - Major crash events for each factor
- `roc_curve.png` - Model prediction accuracy (AUC = 0.88)
- `model_coefficients.png` - What drives crashes (feature importance)
- `conditional_returns_5d.png` - Returns by crowding decile (5-day forward)
- `conditional_returns_20d.png` - Returns by crowding decile (20-day forward)
- `correlation_heatmap.png` - Factor relationship structure

**Datasets** (`data/processed/`):
- `master_dataset.csv` - All data aligned (3,174 days × 12 columns)
- `crowding_index_all.csv` - Composite crowding index
- `flow_attention.csv` - ETF-based crowding signals (9 columns)
- `comovement.csv` - Correlation-based signals (4 columns)
- `factor_side.csv` - Factor characteristic signals (8 columns)
- `drawdown_*.csv` - Drawdown series for each factor (4 files)
- `episodes_*.csv` - Crash episode details (4 files)
- `model_results.txt` - Statistical model diagnostics

### Documentation

**For research understanding:**
- [EXPLANATION.md](EXPLANATION.md) - Complete research walkthrough (8,000 words)
- [RESULTS_SUMMARY.md](RESULTS_SUMMARY.md) - Key findings and practical implications
- [docs/design.md](docs/design.md) - Research design and hypotheses

**For code learning:**
- [CODE_ARCHITECTURE.md](CODE_ARCHITECTURE.md) - Complete learning roadmap (12,000 words)
- [docs/CODE_WALKTHROUGH.md](docs/CODE_WALKTHROUGH.md) - Line-by-line annotated examples
- [docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md) - Copy-paste code recipes
- [docs/INDEX.md](docs/INDEX.md) - Master navigation guide

---

## Limitations

1. **ETF volume and price-based proxies do not equal true positioning:** Volume is attention/flow, not institutional holdings
2. **Results are correlational, not causal:** High crowding correlates with crashes but doesn't prove causation
3. **ETF methodology and index rebalances can affect behavior:** Factor construction changes over time
4. **Sample period:** Analysis limited to 2013-2024 (ETF data availability)
5. **U.S. equity factors only:** Results may not generalize to other markets or asset classes
6. **Daily frequency:** Intraday dynamics and execution risk not captured

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=factor_crowding --cov-report=html

# Run specific test module
pytest tests/test_crowding.py -v
```

**Test coverage:** 93%+ across all modules

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Contact & Citation

**Author:** Rahul Tak
**Email:** rahul.tak.business@gmail.com
**GitHub:** [@Rahul-Tak-060](https://github.com/Rahul-Tak-060)
**Repository:** [Factor-Crowding-](https://github.com/Rahul-Tak-060/Factor-Crowding-)

If you use this code in your research:

```bibtex
@software{factor_crowding_2026,
  author = {Rahul Tak},
  title = {Factor Crowding and Crash Risk: An Empirical Analysis},
  year = {2026},
  url = {https://github.com/Rahul-Tak-060/Factor-Crowding-}
}
```

---

## Acknowledgments

- **Data sources:** Kenneth French Data Library, Federal Reserve Economic Data (FRED), Yahoo Finance
- **Inspiration:** Academic research on factor investing, crowding in quant strategies, and tail risk
- **Built with:** Python, pandas, numpy, scipy, statsmodels, scikit-learn, matplotlib, seaborn
