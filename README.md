# Factor Crowding and Crash Risk

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **Research Question:** Do crowded factors crash harder in stress? An empirical investigation of the relationship between factor crowding and drawdown risk in equity markets.

## Overview

This project implements a complete research pipeline to test whether "crowding" in common equity factors (Momentum, Value, Low Volatility) is associated with:

1. Higher probability of large drawdowns
2. Larger drawdown severity during market stress periods
3. Reduced diversification when correlations spike

## Key Features

- **Production-ready codebase** with type hints, logging, and comprehensive testing
- **Three crowding measurement approaches:**
  - Flow-attention proxy (ETF volume and momentum)
  - Co-movement proxy (rolling correlations)
  - Factor-side proxy (volatility and autocorrelation)
- **Robust analysis pipeline:**
  - Automated data download from public sources
  - Drawdown and crash event identification
  - Predictive modeling (logistic regression, quantile regression)
  - Publication-quality figure generation
- **CLI interface** for reproducible research

## Installation

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended) or pip

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/factor-crowding-crash-risk.git
cd factor-crowding-crash-risk

# Install uv (if not already installed)
pip install uv

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
uv pip install -e ".[dev]"

# Set up pre-commit hooks and create directories
make setup

# Copy environment template
cp .env.example .env
```

## Quick Start

### Run Complete Pipeline

```bash
# Run the full analysis (download data, compute features, model, generate figures)
factor-crowding run --start 2010-01-01 --end 2024-12-31
```

### Individual Commands

```bash
# Download data only
factor-crowding download --start 2010-01-01

# Clean and align data
factor-crowding clean --start 2010-01-01

# View configuration
factor-crowding info
```

### Using Make

```bash
# Run complete pipeline
make run

# Run tests
make test

# Generate coverage report
make test-cov

# Format code
make format

# Lint
make lint

# Type check
make type-check
```

## Data Sources

All data is sourced from free, publicly available sources:

| Data Type | Source | Description |
|-----------|--------|-------------|
| **Fama-French Factors** | [Kenneth French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html) | Daily factor returns (Mkt-RF, SMB, HML, Mom, RF) |
| **VIX** | [FRED](https://fred.stlouisfed.org/series/VIXCLS) | CBOE Volatility Index (market stress proxy) |
| **ETF Data** | [Yahoo Finance](https://finance.yahoo.com) | MTUM, VLUE, USMV daily prices and volumes |

No API keys required for basic usage.

## Project Structure

```
factor-crowding-crash-risk/
├── factor_crowding/          # Main package
│   ├── __init__.py
│   ├── config.py            # Configuration and constants
│   ├── cli.py               # Command-line interface
│   ├── data/                # Data download and cleaning
│   │   ├── download.py
│   │   └── clean.py
│   ├── features/            # Feature engineering
│   │   └── crowding.py      # Crowding index computation
│   ├── analysis/            # Analysis modules
│   │   └── drawdowns.py     # Drawdown and crash identification
│   ├── models/              # Predictive models
│   │   └── predict.py       # Logistic and quantile regression
│   ├── report/              # Report generation
│   │   └── figures.py       # Publication-quality figures
│   └── utils/               # Utilities
│       └── __init__.py      # Logging setup
├── tests/                   # Test suite
│   ├── test_config.py
│   ├── test_clean.py
│   ├── test_crowding.py
│   ├── test_drawdowns.py
│   └── test_predict.py
├── data/                    # Data directory (created on setup)
│   ├── raw/                # Downloaded raw data
│   └── processed/          # Processed datasets
├── outputs/                 # Output directory
│   └── figures/            # Generated figures
├── docs/                    # Documentation
│   └── design.md           # Research design document
├── pyproject.toml          # Project configuration
├── Makefile                # Common tasks
└── README.md               # This file
```

## Methodology

### Crowding Measurement

The project implements three complementary approaches to measuring factor crowding:

**A. Flow-Attention Proxy (ETF-based)**
- Volume z-score (63-day rolling window)
- Return run-up z-score (126-day cumulative returns)
- Crash frequency (count of large down days)

**B. Co-movement Proxy**
- Pairwise rolling correlations among factor ETFs
- Average cross-factor correlation
- Interpretation: High correlation → crowded trades

**C. Factor-Side Proxy**
- Rolling factor return volatility
- Rolling autocorrelation (trend-chasing proxy)

### Crash Definition

- **Daily crash:** Return below 1st percentile of historical distribution
- **Weekly crash:** 5-day cumulative return below 1st percentile
- **Drawdown episode:** Peak-to-trough decline exceeding threshold (default 5%)

### Stress Regimes

Based on rolling VIX percentiles:
- **High stress:** VIX > 75th percentile
- **Normal:** Between 25th and 75th percentile
- **Low stress:** VIX < 25th percentile

## Outputs

### Generated Files

All outputs are saved to `outputs/`:

**Figures** (`outputs/figures/`):
- `crowding_index_timeseries.png` - Crowding index over time with VIX overlay
- `drawdown_comparison.png` - Drawdown distributions by crowding regime
- `roc_curve.png` - Model performance (crash prediction)
- `model_coefficients.png` - Logistic regression coefficients
- `conditional_returns_5d.png` - Forward returns by crowding decile
- `conditional_returns_20d.png` - Forward returns by crowding decile
- `correlation_heatmap.png` - Feature correlation matrix
- `top_drawdown_episodes.png` - Largest historical drawdowns

**Data** (`data/processed/`):
- `master_dataset.csv` - Aligned dataset with all features
- `crowding_index_*.csv` - All crowding indices
- `drawdown_*.csv` - Drawdown series by factor
- `episodes_*.csv` - Discrete drawdown episodes
- `model_results.txt` - Model performance summary

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run specific test file
pytest tests/test_crowding.py

# Run with verbose output
pytest -v
```

## Development

### Code Quality

This project uses:
- **Black** for code formatting
- **Ruff** for linting
- **MyPy** for type checking
- **Pytest** for testing
- **Pre-commit** hooks for automated checks

```bash
# Format code
black factor_crowding tests

# Lint
ruff factor_crowding tests

# Type check
mypy factor_crowding

# Run all quality checks
make format lint type-check test
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run quality checks (`make format lint type-check test`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Research Design

For detailed research design, hypotheses, and methodology, see [docs/design.md](docs/design.md).

### Core Hypotheses

- **H1 (Crowding → Crash):** High crowding predicts increased crash probability
- **H2 (Stress Amplification):** Crowding effects are stronger during high VIX regimes
- **H3 (Diversification Failure):** High cross-factor correlation predicts larger drawdowns

## Limitations

This research has several important limitations:

1. **Crowding Measurement:** ETF volume is a noisy proxy for institutional positioning
2. **Causality:** All results are correlational, not causal
3. **Survivorship Bias:** ETF proxies are subject to index methodology changes
4. **Sample Period:** Results are specific to the analysis period
5. **Factor Construction:** Uses public Fama-French factors (academic construction)

## Citation

If you use this code in your research, please cite:

```bibtex
@software{factor_crowding_2026,
  author = {Your Name},
  title = {Factor Crowding and Crash Risk: An Empirical Analysis},
  year = {2026},
  url = {https://github.com/yourusername/factor-crowding-crash-risk}
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Data:** Kenneth French, Federal Reserve Economic Data (FRED), Yahoo Finance
- **Inspiration:** Research on crowding in quant strategies and factor-based investing
- **Tools:** Built with Python, pandas, scikit-learn, statsmodels, matplotlib

## Contact

- **Author:** Rahul Tak
- **Email:** rahul.tak.business@gmail.com
- **GitHub:** [@Rahul-Tak-060](https://github.com/Rahul-Tak-060)

## Roadmap

Future enhancements:

- [ ] Add support for additional factors (quality, low beta)
- [ ] Implement alternative crowding measures (fund flows, sentiment)
- [ ] Extend to international markets
- [ ] Add regime-switching models
- [ ] Interactive dashboard for exploration
- [ ] Machine learning models (Random Forest, XGBoost)

---

**Note:** This is a research project for educational and demonstrative purposes. Results should not be used for actual investment decisions without proper validation and risk management.
