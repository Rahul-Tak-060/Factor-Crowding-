# Factor Crowding Project - Complete Documentation Index

Welcome! This index helps you navigate all the documentation based on what you want to learn.

---

## Start Here Based on Your Goal

### If you want to **understand what the research is about**
 Read: **[EXPLANATION.md](../EXPLANATION.md)**
- What factors are (Market, Size, Value, Momentum)
- What crowding means (too many investors in same trade)
- What we found (crowding predicts crashes with 88% accuracy)
- How to interpret the results
- Real-world investment implications


---

### If you want to **see the results quickly**
 Read: **[RESULTS_SUMMARY.txt](../RESULTS_SUMMARY.txt)**
- Executive summary of findings
- Key statistics and metrics
- Main conclusions
- Output files generated


---

### If you want to **learn the code architecture**
 Read: **[CODE_ARCHITECTURE.md](CODE_ARCHITECTURE.md)**
- Complete codebase map
- What each module does
- Reading order (beginner → advanced)
- Learning path with exercises
- Programming patterns used
- How all pieces fit together


---

### If you want to **understand code line-by-line**
 Read: **[CODE_WALKTHROUGH.md](CODE_WALKTHROUGH.md)**
- Annotated code examples
- Line-by-line explanations
- Why decisions were made
- Common patterns
- Deep technical details



---

### If you want to **do something specific** (copy-paste recipes)
 Read: **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)**
- Load and analyze data
- Create custom crowding measures
- Make visualizations
- Run models
- Export results
- Debug common issues


---

### If you want to **use the tool** (not read code)
 Read: **[README.md](../README.md)**
- Installation instructions
- How to run the CLI
- Example commands
- Project structure overview


---

### If you want to **contribute code**
 Read: **[CONTRIBUTING.md](../CONTRIBUTING.md)**
- Development setup
- Code style guidelines
- Testing requirements
- Pull request process


---

##  Suggested Learning Paths

### Path 1: **Non-Technical User** (Understand research only)
1. [RESULTS_SUMMARY.txt](../RESULTS_SUMMARY.txt) - Quick overview
2. [EXPLANATION.md](../EXPLANATION.md) - Deep understanding
3. [Generated Figures](../outputs/figures/) - Visual results

**Goal**: Understand what we discovered and why it matters
**Time**: 1 hour

---

### Path 2: **User** (Run analysis, modify parameters)
1. [README.md](../README.md) - Setup and installation
2. [EXPLANATION.md](../EXPLANATION.md) - Understand analysis
3. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Common tasks
4. [CLI Commands](#cli-quick-reference) - Run your own analysis

**Goal**: Run analysis with different date ranges, parameters
**Time**: 1.5 hours

---

### Path 3: **Data Scientist** (Modify analysis, add features)
1. [README.md](../README.md) - Setup
2. [EXPLANATION.md](../EXPLANATION.md) - Understand research
3. [CODE_ARCHITECTURE.md](CODE_ARCHITECTURE.md) - High-level design
4. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Recipes for modifications
5. Key modules:
   - [features/crowding.py](../factor_crowding/features/crowding.py) - Add signals
   - [models/predict.py](../factor_crowding/models/predict.py) - Try new models

**Goal**: Extend analysis, try new crowding measures or models
**Time**: 3-4 hours

---

### Path 4: **Software Engineer** (Understand all code, contribute)
1. [README.md](../README.md) - Setup
2. [CODE_ARCHITECTURE.md](CODE_ARCHITECTURE.md) - Complete architecture
3. [CODE_WALKTHROUGH.md](CODE_WALKTHROUGH.md) - Detailed explanations
4. All source files in reading order (see architecture doc)
5. [tests/](../tests/) - Test suite
6. [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines

**Goal**: Full codebase understanding, make improvements
**Time**: 6-8 hours

---

### Path 5: **Student** (Learn financial data science)
1. [EXPLANATION.md](../EXPLANATION.md) - Financial concepts
2. [CODE_ARCHITECTURE.md](CODE_ARCHITECTURE.md) - Section by section
3. [CODE_WALKTHROUGH.md](CODE_WALKTHROUGH.md) - Study examples
4. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Practice exercises
5. Modify code and run experiments

**Goal**: Learn by doing - understand finance + coding
**Time**: 10+ hours (with practice)

---

## Documentation Files Overview

| File | Purpose | Audience | Length |
|------|---------|----------|--------|
| [EXPLANATION.md](../EXPLANATION.md) | What the research means | Everyone | ~8,000 words |
| [RESULTS_SUMMARY.txt](../RESULTS_SUMMARY.txt) | Quick results overview | Everyone | ~1,500 words |
| [CODE_ARCHITECTURE.md](CODE_ARCHITECTURE.md) | Code structure & learning path | Developers | ~12,000 words |
| [CODE_WALKTHROUGH.md](CODE_WALKTHROUGH.md) | Line-by-line code explanations | Developers | ~7,000 words |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Copy-paste recipes | Users/Developers | ~4,000 words |
| [README.md](../README.md) | Getting started | Everyone | ~2,000 words |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | How to contribute | Contributors | ~1,500 words |

---

##  Code Organization

```
factor_crowding/
│
├── config.py                 # Configuration (START HERE for code)
│
├── data/                     # Data acquisition & cleaning
│   ├── download.py          #   - Fetch from APIs (Fama-French, FRED, Yahoo)
│   └── clean.py             #   - Align calendars, compute returns
│
├── features/                 # Feature engineering
│   └── crowding.py          #   - Build crowding indices (MAIN RESEARCH)
│
├── analysis/                 # Risk analysis
│   └── drawdowns.py         #   - Compute drawdowns, identify crashes
│
├── models/                   # Predictive modeling
│   └── predict.py           #   - Logistic regression, forecasting
│
├── report/                   # Visualization
│   └── figures.py           #   - Generate publication-quality plots
│
├── utils/                    # Utilities
│   └── logging_config.py    #   - Logging configuration
│
└── cli.py                    # Command-line interface (ORCHESTRATION)
```

**Complexity Level**:
-  Beginner: config.py, cli.py
-  Intermediate: download.py, clean.py, figures.py
-  Advanced: crowding.py, drawdowns.py, predict.py

---

##  Common Questions & Where to Find Answers

### "What does the crowding index mean?"
→ [EXPLANATION.md](../EXPLANATION.md) - Section "What Is Factor Crowding?"

### "How accurate is the crash prediction?"
→ [RESULTS_SUMMARY.txt](../RESULTS_SUMMARY.txt) - Section "Predictive Model Results"
→ AUC = 0.88 (excellent accuracy)

### "How do I run the analysis with different dates?"
→ [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Section "Quick Command Reference"
→ Command: `factor-crowding run --start YYYY-MM-DD --end YYYY-MM-DD`

### "Which factor is most risky?"
→ [EXPLANATION.md](../EXPLANATION.md) - Section "Understanding the Outputs"
→ Momentum (Mom) has 8 crash episodes, most volatile

### "How is the crowding index calculated?"
→ [CODE_ARCHITECTURE.md](CODE_ARCHITECTURE.md) - Section "features/crowding.py"
→ [CODE_WALKTHROUGH.md](CODE_WALKTHROUGH.md) - Annotated crowding example

### "Can I add a new factor or ETF?"
→ [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Section "Custom Crowding Measures"
→ Modify `config.py` `etf_tickers` list

### "Where are the output files?"
→ [README.md](../README.md) - Section "Project Structure"
→ Location: `outputs/figures/` and `data/processed/`

### "How do I interpret the figures?"
→ [EXPLANATION.md](../EXPLANATION.md) - Section "Understanding the Outputs"
→ Each figure explained in detail

### "What programming patterns are used?"
→ [CODE_ARCHITECTURE.md](CODE_ARCHITECTURE.md) - Section "Key Programming Patterns"
→ [CODE_WALKTHROUGH.md](CODE_WALKTHROUGH.md) - Section "Summary of Key Patterns"

### "How do I test my changes?"
→ [CONTRIBUTING.md](../CONTRIBUTING.md) - Testing section
→ Command: `pytest tests/ -v`

---

##  CLI Quick Reference

```bash
# Full analysis pipeline (most common)
factor-crowding run --start 2013-01-01 --end 2024-12-31

# Download data only
factor-crowding download --start 2013-01-01

# Force re-download (ignore cache)
factor-crowding download --start 2013-01-01 --force

# Clean and align data
factor-crowding clean --start 2013-01-01 --end 2024-12-31

# Show configuration
factor-crowding info

# Get help
factor-crowding --help
factor-crowding run --help
```

---

##  Key Files to Examine

### Input Data (after download):
```
data/raw/
├── ff_daily_factors.csv      # Fama-French 3 factors (26,129 days)
├── ff_daily_momentum.csv     # Momentum factor (26,028 days)
├── vix_daily.csv             # VIX volatility index (3,403 days)
├── MTUM_daily.csv            # Momentum ETF (3,208 days)
├── VLUE_daily.csv            # Value ETF (3,208 days)
└── USMV_daily.csv            # Low volatility ETF (3,281 days)
```

### Processed Data (after analysis):
```
data/processed/
├── master_dataset.csv        # Aligned data (3,174 days × 12 vars)
├── crowding_index_all.csv    # Composite crowding index
├── flow_attention.csv        # ETF-based crowding
├── comovement.csv            # Correlation-based crowding
├── factor_side.csv           # Factor characteristic crowding
├── drawdown_*.csv            # Drawdown series (4 files)
├── episodes_*.csv            # Crash episodes (4 files)
└── model_results.txt         # Statistical output
```

### Generated Figures:
```
outputs/figures/
├── crowding_index_timeseries.png    # Crowding evolution
├── top_drawdown_episodes.png        # Major crashes
├── roc_curve.png                    # Model accuracy
├── model_coefficients.png           # What drives crashes
├── conditional_returns_5d.png       # Returns by crowding (5-day)
├── conditional_returns_20d.png      # Returns by crowding (20-day)
└── correlation_heatmap.png          # Factor correlations
```

---

##  Learning Resources by Topic

### Financial Concepts:
- **Factor Investing**: [EXPLANATION.md](../EXPLANATION.md) - "What Are the Factors?" section
- **Drawdowns**: [EXPLANATION.md](../EXPLANATION.md) - Understanding risk metrics
- **Crowding**: [EXPLANATION.md](../EXPLANATION.md) - "What Is Factor Crowding?" section

### Python/Pandas:
- **DataFrames**: [CODE_WALKTHROUGH.md](CODE_WALKTHROUGH.md) - Data cleaning examples
- **Time Series**: [CODE_ARCHITECTURE.md](CODE_ARCHITECTURE.md) - data/clean.py section
- **Visualization**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Visualization recipes

### Machine Learning:
- **Logistic Regression**: [CODE_WALKTHROUGH.md](CODE_WALKTHROUGH.md) - predict.py section
- **Train/Test Split**: [CODE_ARCHITECTURE.md](CODE_ARCHITECTURE.md) - models section
- **AUC/ROC**: [EXPLANATION.md](../EXPLANATION.md) - "Understanding the Outputs" → ROC Curve

### Software Engineering:
- **Testing**: [tests/](../tests/) directory + [CONTRIBUTING.md](../CONTRIBUTING.md)
- **Configuration**: [CODE_WALKTHROUGH.md](CODE_WALKTHROUGH.md) - config.py section
- **CLI Design**: [CODE_ARCHITECTURE.md](CODE_ARCHITECTURE.md) - cli.py section

---

##  Next Steps After Reading

### If you understood the research:
- Share findings with colleagues
- Cite in your own work (see [LICENSE](../LICENSE))
- Suggest new research directions (open an issue on GitHub)

### If you want to use the tool:
- Install and run on your machine ([README.md](../README.md))
- Try different date ranges
- Experiment with parameters

### If you want to extend the code:
- Add new data sources (ETFs, factors)
- Create new crowding measures
- Try different models (Random Forest, XGBoost)
- Improve visualizations
- Add new features

### If you want to contribute:
- Read [CONTRIBUTING.md](../CONTRIBUTING.md)
- Fix bugs or add features
- Improve documentation
- Submit pull request

---

##  Getting Help

### Issues with installation or running:
- Check [README.md](../README.md) - Installation section
- Check [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - "Common Issues & Solutions"
- Open a GitHub issue with error details

### Questions about the research:
- Read [EXPLANATION.md](../EXPLANATION.md) first
- Check academic references in that document
- For deeper questions, open a discussion on GitHub

### Questions about the code:
- Search [CODE_ARCHITECTURE.md](CODE_ARCHITECTURE.md) and [CODE_WALKTHROUGH.md](CODE_WALKTHROUGH.md)
- Check [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for examples
- Open a GitHub issue for bugs

---

**Happy Learning! **

For the most up-to-date information, always check the GitHub repository.
