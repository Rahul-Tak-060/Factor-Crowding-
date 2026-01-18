# Quick Reference Guide - Common Tasks & Recipes

This guide provides **copy-paste ready code** for common tasks you might want to do.

---

## 📖 Reading Data

### Load Master Dataset
```python
import pandas as pd

# Load the aligned dataset
df = pd.read_csv('data/processed/master_dataset.csv',
                 index_col=0,
                 parse_dates=True)

# Check what's in it
print(df.head())
print(df.columns)
print(f"Date range: {df.index[0]} to {df.index[-1]}")
print(f"Observations: {len(df):,}")
```

### Load Crowding Index
```python
# Load composite crowding index
crowding = pd.read_csv('data/processed/crowding_index_all.csv',
                       index_col=0,
                       parse_dates=True)

# Get the crowding series
crowding_series = crowding['CrowdingIndex_All']

# Find highest crowding days
top_5 = crowding.nlargest(5, 'CrowdingIndex_All')
print("Highest crowding periods:")
print(top_5)
```

### Load Drawdown Data
```python
# Load drawdowns for momentum factor
dd_mom = pd.read_csv('data/processed/drawdown_Mom.csv',
                     index_col=0,
                     parse_dates=True)

# Find worst drawdown
worst = dd_mom['drawdown'].min()
worst_date = dd_mom['drawdown'].idxmin()
print(f"Worst drawdown: {worst:.2%} on {worst_date}")

# Load crash episodes
episodes = pd.read_csv('data/processed/episodes_Mom.csv')
print(f"Number of crash episodes: {len(episodes)}")
```

---

## 📊 Basic Analysis

### Compute Summary Statistics
```python
import pandas as pd

df = pd.read_csv('data/processed/master_dataset.csv', index_col=0, parse_dates=True)

# Factor returns statistics
factors = ['Mkt-RF', 'SMB', 'HML', 'Mom']
stats = df[factors].describe()
print(stats)

# Annualized returns (252 trading days per year)
annual_returns = df[factors].mean() * 252
print("\nAnnualized Returns:")
print(annual_returns)

# Annualized volatility
annual_vol = df[factors].std() * (252 ** 0.5)
print("\nAnnualized Volatility:")
print(annual_vol)

# Sharpe ratio (assuming RF = 0)
sharpe = annual_returns / annual_vol
print("\nSharpe Ratio:")
print(sharpe)
```

### Correlation Analysis
```python
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

df = pd.read_csv('data/processed/master_dataset.csv', index_col=0, parse_dates=True)

# Compute correlation matrix
factors = ['Mkt-RF', 'SMB', 'HML', 'Mom']
corr = df[factors].corr()

# Plot heatmap
plt.figure(figsize=(8, 6))
sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm', center=0)
plt.title('Factor Correlations')
plt.tight_layout()
plt.savefig('my_correlation.png', dpi=300)
plt.show()
```

### Find Specific Events
```python
import pandas as pd

df = pd.read_csv('data/processed/master_dataset.csv', index_col=0, parse_dates=True)

# COVID crash (March 2020)
covid_period = df.loc['2020-02-01':'2020-04-01']
print("COVID period returns:")
print(covid_period[['Mkt-RF', 'Mom']].describe())

# Largest daily drops
largest_drops = df.nsmallest(10, 'Mkt-RF')[['Mkt-RF', 'VIX']]
print("\nLargest market drops:")
print(largest_drops)

# Days with VIX > 30
high_vix = df[df['VIX'] > 30]
print(f"\nDays with VIX > 30: {len(high_vix)} ({len(high_vix)/len(df)*100:.1f}%)")
```

---

## 🔧 Custom Crowding Measures

### Create Your Own Crowding Signal
```python
import pandas as pd
import numpy as np
from factor_crowding.features.crowding import CrowdingIndexBuilder

# Load data
df = pd.read_csv('data/processed/master_dataset.csv', index_col=0, parse_dates=True)

# Initialize builder
builder = CrowdingIndexBuilder()

# Example 1: Simple volume-based crowding
volumes = df[['MTUM_vol', 'VLUE_vol', 'USMV_vol']]

# Z-score each volume series
z_scores = []
for col in volumes.columns:
    z = builder.compute_zscore(volumes[col], window=20)
    z_scores.append(z)

# Average across ETFs
my_volume_crowding = pd.concat(z_scores, axis=1).mean(axis=1)

# Save it
result = pd.DataFrame({'My_Volume_Crowding': my_volume_crowding})
result.to_csv('my_crowding_measure.csv')

print(f"Created crowding measure with {len(result)} observations")
print(result.describe())
```

### Combine Multiple Signals
```python
import pandas as pd
from factor_crowding.features.crowding import CrowdingIndexBuilder

df = pd.read_csv('data/processed/master_dataset.csv', index_col=0, parse_dates=True)
builder = CrowdingIndexBuilder()

# Load existing crowding measures
flow = pd.read_csv('data/processed/flow_attention.csv', index_col=0, parse_dates=True)
comov = pd.read_csv('data/processed/comovement.csv', index_col=0, parse_dates=True)

# Create custom combination (70% flow, 30% comovement)
custom_index = (0.7 * flow.iloc[:, 0] + 0.3 * comov.iloc[:, 0])

# Smooth with moving average
smoothed = custom_index.rolling(window=10).mean()

result = pd.DataFrame({'Custom_Index': smoothed})
result.to_csv('custom_crowding.csv')
```

---

## 📈 Visualization Recipes

### Plot Time Series
```python
import pandas as pd
import matplotlib.pyplot as plt

# Load crowding index
crowding = pd.read_csv('data/processed/crowding_index_all.csv',
                       index_col=0, parse_dates=True)

# Create figure
fig, ax = plt.subplots(figsize=(12, 6))

# Plot crowding
ax.plot(crowding.index, crowding.iloc[:, 0], label='Crowding Index', linewidth=1.5)

# Add horizontal lines
ax.axhline(y=1, color='r', linestyle='--', alpha=0.5, label='High Crowding')
ax.axhline(y=-1, color='g', linestyle='--', alpha=0.5, label='Low Crowding')
ax.axhline(y=0, color='k', linestyle='-', alpha=0.3)

# Shade extreme periods
high_crowding = crowding.iloc[:, 0] > 1
ax.fill_between(crowding.index, 0, 1, where=high_crowding,
                alpha=0.2, color='red', label='Extreme High')

# Labels
ax.set_xlabel('Date', fontsize=12)
ax.set_ylabel('Crowding Index', fontsize=12)
ax.set_title('Factor Crowding Over Time', fontsize=14)
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('crowding_timeseries.png', dpi=300)
plt.show()
```

### Scatter Plot: Crowding vs Returns
```python
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load data
df = pd.read_csv('data/processed/master_dataset.csv', index_col=0, parse_dates=True)
crowding = pd.read_csv('data/processed/crowding_index_all.csv',
                       index_col=0, parse_dates=True)

# Merge
merged = pd.concat([crowding, df['Mom']], axis=1).dropna()
merged.columns = ['Crowding', 'Mom_Return']

# Compute forward return (5 days ahead)
merged['Forward_Return'] = merged['Mom_Return'].shift(-5)
merged = merged.dropna()

# Create scatter plot
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(merged['Crowding'], merged['Forward_Return'],
           alpha=0.3, s=10)

# Add trendline
z = np.polyfit(merged['Crowding'], merged['Forward_Return'], 1)
p = np.poly1d(z)
ax.plot(merged['Crowding'], p(merged['Crowding']),
        "r--", linewidth=2, label=f'Trendline: y={z[0]:.4f}x+{z[1]:.4f}')

# Labels
ax.set_xlabel('Crowding Index', fontsize=12)
ax.set_ylabel('5-Day Forward Momentum Return', fontsize=12)
ax.set_title('Crowding vs Future Returns', fontsize=14)
ax.axhline(y=0, color='k', linestyle='-', alpha=0.3)
ax.axvline(x=0, color='k', linestyle='-', alpha=0.3)
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('crowding_scatter.png', dpi=300)
plt.show()
```

### Distribution Plot
```python
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

crowding = pd.read_csv('data/processed/crowding_index_all.csv',
                       index_col=0, parse_dates=True)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Histogram
ax1.hist(crowding.iloc[:, 0], bins=50, alpha=0.7, edgecolor='black')
ax1.axvline(x=crowding.iloc[:, 0].mean(), color='r',
            linestyle='--', label=f'Mean: {crowding.iloc[:, 0].mean():.2f}')
ax1.set_xlabel('Crowding Index')
ax1.set_ylabel('Frequency')
ax1.set_title('Crowding Distribution')
ax1.legend()
ax1.grid(True, alpha=0.3)

# Box plot
ax2.boxplot(crowding.iloc[:, 0].dropna())
ax2.set_ylabel('Crowding Index')
ax2.set_title('Crowding Box Plot')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('crowding_distribution.png', dpi=300)
plt.show()
```

---

## 🤖 Running Models

### Predict Crashes with Custom Features
```python
from factor_crowding.models.predict import CrashPredictor
from factor_crowding.analysis.drawdowns import DrawdownAnalyzer
import pandas as pd

# Load data
df = pd.read_csv('data/processed/master_dataset.csv', index_col=0, parse_dates=True)
crowding = pd.read_csv('data/processed/crowding_index_all.csv',
                       index_col=0, parse_dates=True)

# Identify crashes
analyzer = DrawdownAnalyzer()
mom_returns = df['Mom']
crash_flags = analyzer.identify_crash_events(
    mom_returns,
    window=1,
    threshold=0.01,
    method='historical'
)

# Prepare dataset
predictor = CrashPredictor()
pred_data = predictor.prepare_predictive_dataset(
    master_data=df,
    crowding_index=crowding.iloc[:, 0],
    crash_flags=crash_flags,
    forward_window=10  # Predict 10 days ahead instead of 5
)

print(f"Prediction dataset: {len(pred_data)} observations")
print(f"Features: {[col for col in pred_data.columns if col != 'crash_target']}")
print(f"Crash rate: {pred_data['crash_target'].mean():.2%}")

# Fit model
results = predictor.fit_logistic_model(pred_data)
print(f"\nModel AUC: {results['test_auc']:.3f}")
```

### Backtest a Trading Strategy
```python
import pandas as pd
import numpy as np

# Load data
df = pd.read_csv('data/processed/master_dataset.csv', index_col=0, parse_dates=True)
crowding = pd.read_csv('data/processed/crowding_index_all.csv',
                       index_col=0, parse_dates=True)

# Merge
merged = pd.concat([crowding, df['Mom']], axis=1).dropna()
merged.columns = ['Crowding', 'Mom_Return']

# Strategy: Go long when crowding < 0, stay out when crowding > 1
merged['Position'] = np.where(merged['Crowding'] < 0, 1.0,
                     np.where(merged['Crowding'] > 1, 0.0, 0.5))

# Compute strategy returns
merged['Strategy_Return'] = merged['Position'].shift(1) * merged['Mom_Return']

# Performance metrics
total_return = (1 + merged['Strategy_Return']).cumprod()[-1] - 1
buy_hold_return = (1 + merged['Mom_Return']).cumprod()[-1] - 1

print(f"Strategy Return: {total_return:.2%}")
print(f"Buy & Hold Return: {buy_hold_return:.2%}")
print(f"Outperformance: {total_return - buy_hold_return:.2%}")

# Plot cumulative returns
import matplotlib.pyplot as plt

cumulative_strategy = (1 + merged['Strategy_Return']).cumprod()
cumulative_buyhold = (1 + merged['Mom_Return']).cumprod()

plt.figure(figsize=(12, 6))
plt.plot(merged.index, cumulative_strategy, label='Strategy', linewidth=2)
plt.plot(merged.index, cumulative_buyhold, label='Buy & Hold', linewidth=2)
plt.xlabel('Date')
plt.ylabel('Cumulative Return')
plt.title('Strategy Performance')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('backtest_results.png', dpi=300)
plt.show()
```

---

## 🔍 Debugging & Inspection

### Check Data Quality
```python
import pandas as pd

df = pd.read_csv('data/processed/master_dataset.csv', index_col=0, parse_dates=True)

print("=== DATA QUALITY REPORT ===\n")

# Missing values
print("Missing Values:")
print(df.isnull().sum())
print()

# Data types
print("Data Types:")
print(df.dtypes)
print()

# Date range
print(f"Date Range: {df.index.min()} to {df.index.max()}")
print(f"Total Days: {len(df)}")
print(f"Expected Days (approx): {(df.index.max() - df.index.min()).days}")
print()

# Check for duplicates
duplicates = df.index.duplicated().sum()
print(f"Duplicate Dates: {duplicates}")
print()

# Value ranges
print("Value Ranges (min/max):")
for col in df.columns:
    print(f"{col:12s}: [{df[col].min():8.4f}, {df[col].max():8.4f}]")
print()

# Outliers (values beyond 5 std devs)
print("Potential Outliers (>5 std):")
for col in df.select_dtypes(include='number').columns:
    mean = df[col].mean()
    std = df[col].std()
    outliers = df[(df[col] > mean + 5*std) | (df[col] < mean - 5*std)]
    if len(outliers) > 0:
        print(f"{col}: {len(outliers)} outliers")
```

### Profile Code Performance
```python
import time
import pandas as pd
from factor_crowding.features.crowding import CrowdingIndexBuilder

df = pd.read_csv('data/processed/master_dataset.csv', index_col=0, parse_dates=True)
builder = CrowdingIndexBuilder()

# Time different operations
print("=== PERFORMANCE PROFILING ===\n")

# Test 1: Z-score with different windows
series = df['MTUM_vol']

start = time.time()
z_full = builder.compute_zscore(series, window=None)
time_full = time.time() - start

start = time.time()
z_roll = builder.compute_zscore(series, window=20)
time_roll = time.time() - start

print(f"Z-score (full sample): {time_full*1000:.2f} ms")
print(f"Z-score (rolling 20):  {time_roll*1000:.2f} ms")
print()

# Test 2: Build crowding indices
start = time.time()
flow = builder.build_flow_attention_proxy(df)
time_flow = time.time() - start

start = time.time()
comov = builder.build_comovement_proxy(df)
time_comov = time.time() - start

print(f"Flow-attention proxy:  {time_flow:.2f} s")
print(f"Co-movement proxy:     {time_comov:.2f} s")
```

---

## 📤 Export Results

### Create Summary Report
```python
import pandas as pd
from datetime import datetime

# Load data
df = pd.read_csv('data/processed/master_dataset.csv', index_col=0, parse_dates=True)
crowding = pd.read_csv('data/processed/crowding_index_all.csv',
                       index_col=0, parse_dates=True)

# Create report
report = []
report.append("=" * 60)
report.append("FACTOR CROWDING ANALYSIS SUMMARY REPORT")
report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
report.append("=" * 60)
report.append("")

# Data summary
report.append("DATA SUMMARY:")
report.append(f"  Date Range: {df.index[0].date()} to {df.index[-1].date()}")
report.append(f"  Trading Days: {len(df):,}")
report.append("")

# Factor statistics
report.append("FACTOR RETURNS (Annualized):")
factors = ['Mkt-RF', 'SMB', 'HML', 'Mom']
for factor in factors:
    ann_ret = df[factor].mean() * 252 * 100
    ann_vol = df[factor].std() * (252**0.5) * 100
    sharpe = (df[factor].mean() / df[factor].std()) * (252**0.5) if df[factor].std() > 0 else 0
    report.append(f"  {factor:8s}: Return={ann_ret:6.2f}%  Vol={ann_vol:6.2f}%  Sharpe={sharpe:5.2f}")
report.append("")

# Crowding summary
crowding_vals = crowding.iloc[:, 0]
report.append("CROWDING INDEX SUMMARY:")
report.append(f"  Mean: {crowding_vals.mean():6.2f}")
report.append(f"  Std:  {crowding_vals.std():6.2f}")
report.append(f"  Min:  {crowding_vals.min():6.2f} on {crowding_vals.idxmin().date()}")
report.append(f"  Max:  {crowding_vals.max():6.2f} on {crowding_vals.idxmax().date()}")
report.append(f"  High Crowding Days (>1): {(crowding_vals > 1).sum()} ({(crowding_vals > 1).sum()/len(crowding_vals)*100:.1f}%)")
report.append("")

report.append("=" * 60)

# Write to file
with open('analysis_summary.txt', 'w') as f:
    f.write('\n'.join(report))

print("Report saved to analysis_summary.txt")
print('\n'.join(report))
```

### Export to Excel
```python
import pandas as pd

# Load data
df = pd.read_csv('data/processed/master_dataset.csv', index_col=0, parse_dates=True)
crowding = pd.read_csv('data/processed/crowding_index_all.csv',
                       index_col=0, parse_dates=True)
episodes = pd.read_csv('data/processed/episodes_Mom.csv')

# Create Excel writer
with pd.ExcelWriter('factor_crowding_results.xlsx', engine='openpyxl') as writer:
    # Sheet 1: Master data
    df.to_excel(writer, sheet_name='Master_Data')

    # Sheet 2: Crowding index
    crowding.to_excel(writer, sheet_name='Crowding_Index')

    # Sheet 3: Crash episodes
    episodes.to_excel(writer, sheet_name='Crash_Episodes', index=False)

    # Sheet 4: Summary statistics
    summary = pd.DataFrame({
        'Mean': df.mean(),
        'Std': df.std(),
        'Min': df.min(),
        'Max': df.max()
    })
    summary.to_excel(writer, sheet_name='Summary_Stats')

print("Excel file saved: factor_crowding_results.xlsx")
```

---

## 🎯 Quick Command Reference

```bash
# Run full analysis pipeline
factor-crowding run --start 2013-01-01 --end 2024-12-31

# Download data only
factor-crowding download --start 2013-01-01

# Force re-download (ignore cache)
factor-crowding download --start 2013-01-01 --force

# Clean and align data
factor-crowding clean --start 2013-01-01

# Show project info
factor-crowding info

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=factor_crowding --cov-report=html

# Format code
black factor_crowding/

# Lint code
ruff check factor_crowding/

# Type check
mypy factor_crowding/
```

---

## 🐛 Common Issues & Solutions

### Issue: "No module named 'factor_crowding'"
**Solution:**
```bash
# Install in development mode
pip install -e .

# Or activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux
```

### Issue: "DateParseError when loading data"
**Solution:**
```python
# Specify date format explicitly
df = pd.read_csv('file.csv',
                 index_col=0,
                 parse_dates=True,
                 date_format='%Y-%m-%d')  # Or '%Y%m%d' for YYYYMMDD
```

### Issue: "Memory error with large datasets"
**Solution:**
```python
# Read data in chunks
chunks = []
for chunk in pd.read_csv('large_file.csv', chunksize=10000):
    # Process chunk
    processed = process(chunk)
    chunks.append(processed)

df = pd.concat(chunks, ignore_index=True)
```

### Issue: "Figures not displaying"
**Solution:**
```python
# Add this before plotting
import matplotlib
matplotlib.use('TkAgg')  # Or 'Qt5Agg'
import matplotlib.pyplot as plt

# Or just save without showing
plt.savefig('figure.png')
# Don't call plt.show()
```

---

This quick reference should cover 90% of common tasks. For deeper understanding, refer to CODE_ARCHITECTURE.md and CODE_WALKTHROUGH.md.
