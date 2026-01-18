# Detailed Code Walkthrough - Annotated Examples

This document provides **line-by-line explanations** of key code sections with detailed annotations.

---

## 1. Configuration System (`config.py`)

### Complete Annotated Example:

```python
"""Configuration module for the factor crowding analysis project.

This module defines all configuration parameters using Python dataclasses.
Dataclasses provide:
- Automatic __init__ generation
- Type hints for validation
- Immutability (frozen=True)
- Default values
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

@dataclass(frozen=True)  # frozen=True makes this immutable (like a const)
class DataConfig:
    """Configuration for data sources and file paths.

    Why use a dataclass?
    - Single source of truth for all paths
    - Easy to modify without changing code everywhere
    - Type-safe (IDE can check types)
    """

    # DATA DIRECTORIES
    # Path is better than str - handles OS differences automatically
    raw_data_dir: Path = Path("data/raw")
    processed_data_dir: Path = Path("data/processed")
    output_dir: Path = Path("outputs")

    # DATA SOURCES
    # ETF tickers we track - list allows easy addition
    etf_tickers: List[str] = field(default_factory=lambda: ["MTUM", "VLUE", "USMV"])

    # Why default_factory instead of just = ["MTUM", ...]?
    # Mutable defaults are shared across instances (dangerous!)
    # default_factory creates a NEW list each time

    # Factor definitions - what we're analyzing
    factor_names: List[str] = field(default_factory=lambda: ["Mkt-RF", "SMB", "HML", "Mom"])

    # URLs for data sources - centralized and easy to update
    ff_factors_url: str = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_daily_CSV.zip"
    ff_momentum_url: str = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Momentum_Factor_daily_CSV.zip"

    # FRED ticker for VIX
    vix_ticker: str = "VIXCLS"


@dataclass(frozen=True)
class AnalysisConfig:
    """Configuration for analysis parameters.

    These control HOW we do the analysis, not WHERE data comes from.
    Separating concerns makes code more maintainable.
    """

    # CROWDING INDEX PARAMETERS
    # Window for rolling calculations (e.g., rolling mean, std)
    crowding_window: int = 20  # 20 trading days ≈ 1 month

    # Percentile for winsorization (capping outliers)
    winsorize_limit: float = 0.01  # Cap at 1st and 99th percentile

    # DRAWDOWN ANALYSIS PARAMETERS
    # What constitutes a "crash"? Bottom 1% of returns
    crash_threshold_pct: float = 0.01  # 1st percentile

    # How many days forward should we look for crashes?
    crash_window: int = 5  # 5 trading days ≈ 1 week

    # MODELING PARAMETERS
    # Train/test split ratio
    test_size: float = 0.2  # 80% train, 20% test

    # Random seed for reproducibility
    # Same seed = same train/test split every time
    random_state: int = 42  # Why 42? Hitchhiker's Guide reference 😊

    # Forward-looking window for prediction
    forward_window: int = 5  # Predict crashes 5 days ahead


@dataclass(frozen=True)
class LoggingConfig:
    """Configuration for logging behavior.

    Logging levels:
    - DEBUG: Very detailed, for development
    - INFO: Confirmation that things are working
    - WARNING: Something unexpected, but we can continue
    - ERROR: Something failed
    - CRITICAL: Application may crash
    """

    # Default level for most messages
    level: str = "INFO"

    # Where to write logs
    log_dir: Path = Path("logs")

    # Log format template
    # %(asctime)s = timestamp
    # %(name)s = logger name (usually module name)
    # %(levelname)s = DEBUG, INFO, etc.
    # %(message)s = the actual log message
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Timestamp format
    date_format: str = "%Y-%m-%d %H:%M:%S"


# USAGE EXAMPLE:
# In any other module, just do:
#   from factor_crowding.config import DataConfig
#   config = DataConfig()
#   print(config.raw_data_dir)  # Path('data/raw')
#
# To override defaults:
#   config = DataConfig(raw_data_dir=Path("my_data"))
#
# Why this is better than global variables:
# - Type checking
# - Immutability (can't accidentally modify)
# - Easy to test (create test config)
# - Self-documenting (type hints + docstrings)
```

---

## 2. Data Download (`data/download.py`)

### Complete Annotated Example - Fama-French Parser:

```python
def _download_ff_zip(
    self,
    url: str,
    output_file: Path,
    dataset_name: str
) -> pd.DataFrame:
    """Download and parse Fama-French CSV files from ZIP archives.

    CHALLENGE: Ken French's data files have:
    1. Copyright notice at top
    2. Multiple blank lines
    3. Copyright notice at bottom
    4. Inconsistent headers

    We need to:
    - Skip copyright text
    - Find where data starts
    - Stop where data ends
    - Handle different file formats

    Args:
        url: ZIP file URL from Ken French's website
        output_file: Where to save the cleaned CSV
        dataset_name: Human-readable name for logging

    Returns:
        pandas DataFrame with cleaned data

    Raises:
        URLError: If download fails
        ValueError: If data format is unexpected
    """

    # STEP 1: Download the ZIP file
    logger.info(f"Fetching {dataset_name} from {url}")

    try:
        # urlopen opens a URL like open() opens a file
        response = urlopen(url)

        # Read binary content into memory
        zip_data = BytesIO(response.read())

    except URLError as e:
        logger.error(f"Failed to download {dataset_name}: {e}")
        raise

    # STEP 2: Extract CSV from ZIP
    with zipfile.ZipFile(zip_data) as zf:
        # Usually just one file in the ZIP
        csv_filename = zf.namelist()[0]

        # Extract and decode (CSV files are text, not binary)
        with zf.open(csv_filename) as f:
            content = f.read().decode('utf-8')  # Convert bytes to string

    # STEP 3: Parse the messy content
    lines = content.split('\n')  # Split into individual lines

    # STRATEGY: Find first line that looks like a date (8 digits YYYYMMDD)
    # Everything before that is headers/copyright
    # Everything after empty lines is copyright

    # Regex pattern for 8-digit dates (e.g., 19260701 = July 1, 1926)
    date_pattern = re.compile(r'^\d{8}$')

    data_start = None  # Will hold index where data starts
    header_line = None  # Will hold index where column names are

    # STEP 4: Find data start
    for i, line in enumerate(lines):
        # Split by comma to get first column
        parts = line.strip().split(',')

        if len(parts) > 0 and date_pattern.match(parts[0]):
            # Found first data line!
            data_start = i
            # Column names should be the line BEFORE first data
            header_line = i - 1
            break

    # Validation: Did we find data?
    if data_start is None:
        raise ValueError(f"Could not find data start in {dataset_name}")

    # STEP 5: Find data end
    # Read from data_start until we hit:
    # - Empty line
    # - Line that doesn't start with 8 digits
    data_lines = []

    for line in lines[data_start:]:
        parts = line.strip().split(',')

        # Stop at empty line or non-date line
        if not line.strip() or not date_pattern.match(parts[0]):
            break

        data_lines.append(line)

    # STEP 6: Get column names
    # The line before data has column names
    header = lines[header_line].strip()
    column_names = [col.strip() for col in header.split(',')]

    logger.info(f"Found {len(data_lines)} data rows with columns: {column_names}")

    # STEP 7: Create DataFrame
    # StringIO lets us treat a string like a file (needed for read_csv)
    from io import StringIO

    # Reconstruct clean CSV: header + data only
    clean_csv = header + '\n' + '\n'.join(data_lines)

    # Parse into DataFrame
    df = pd.read_csv(
        StringIO(clean_csv),
        parse_dates=['Date'],  # Convert date column to datetime
        index_col='Date'  # Use dates as row index
    )

    # STEP 8: Convert date format
    # Input: 19260701 (integer)
    # Output: 1926-07-01 (datetime)
    df.index = pd.to_datetime(df.index, format='%Y%m%d')

    # STEP 9: Convert returns from percent to decimal
    # Input: 0.10 (meaning 0.10%)
    # Output: 0.0010 (meaning 0.10%)
    # We divide by 100 to convert percentage to decimal
    for col in df.columns:
        if col != 'RF':  # Don't convert if it's the risk-free rate column
            df[col] = pd.to_numeric(df[col], errors='coerce') / 100.0

    # STEP 10: Save to CSV
    df.to_csv(output_file)
    logger.info(f"Downloaded {len(df)} rows for {dataset_name}")
    logger.info(f"Saved {dataset_name} to {output_file}")

    return df


# WHY THIS IS COMPLEX:
# - Real-world data is messy (copyright notices, blank lines)
# - No standard format (different files, different structures)
# - Need robust parsing (regex for dates, careful line-by-line)
# - Need validation (what if format changes?)
# - Need good error messages (help users debug)
#
# LESSONS:
# 1. Always validate assumptions (data_start is not None)
# 2. Use logging extensively (users want to know what's happening)
# 3. Handle errors gracefully (try/except with clear messages)
# 4. Document edge cases (copyright footers, blank lines)
# 5. Make code maintainable (break into logical steps)
```

---

## 3. Data Cleaning (`data/clean.py`)

### Complete Annotated Example - Calendar Alignment:

```python
def align_calendars(
    self,
    dataframes: List[pd.DataFrame],
    method: str = "inner"
) -> List[pd.DataFrame]:
    """Align multiple time series to common calendar.

    PROBLEM: Different data sources have different calendars:
    - Fama-French: Daily since 1926, includes weekends/holidays up to ~1960
    - VIX: Daily since 1990, only trading days
    - ETFs: Since 2013, only trading days

    SOLUTION: Find common dates and reindex all dataframes.

    Args:
        dataframes: List of DataFrames with DatetimeIndex
        method: 'inner' (intersection) or 'outer' (union)

    Returns:
        List of aligned DataFrames (same length, same dates)

    Example:
        df1.index = [2020-01-01, 2020-01-02, 2020-01-03]
        df2.index = [2020-01-02, 2020-01-03, 2020-01-04]

        inner: [2020-01-02, 2020-01-03] (only common)
        outer: [2020-01-01, 2020-01-02, 2020-01-03, 2020-01-04] (all dates)
    """

    if not dataframes:
        return []  # Edge case: empty list

    # STEP 1: Collect all unique dates from all dataframes
    all_indices = [df.index for df in dataframes]

    # STEP 2: Compute common calendar
    if method == "inner":
        # Intersection: Only dates present in ALL dataframes
        # Start with first dataframe's index
        common_index = all_indices[0]

        # Intersect with each subsequent dataframe
        for idx in all_indices[1:]:
            # intersection() keeps only dates in both
            common_index = common_index.intersection(idx)

    elif method == "outer":
        # Union: All dates from ANY dataframe
        # Start with first dataframe's index
        common_index = all_indices[0]

        # Union with each subsequent dataframe
        for idx in all_indices[1:]:
            # union() combines all unique dates
            common_index = common_index.union(idx)

    else:
        raise ValueError(f"Invalid method: {method}. Use 'inner' or 'outer'.")

    # STEP 3: Sort chronologically (important!)
    # Union/intersection don't guarantee order
    common_index = common_index.sort_values()

    logger.info(f"Aligning {len(dataframes)} dataframes with method '{method}'...")
    logger.info(f"Aligned to {len(common_index)} common dates")

    # STEP 4: Reindex each dataframe to common calendar
    aligned = []

    for df in dataframes:
        # reindex() aligns the dataframe to new index
        # Missing dates get NaN values
        aligned_df = df.reindex(common_index)

        # For 'inner', there should be no NaN (all dates exist)
        # For 'outer', there will be NaN where data doesn't exist

        aligned.append(aligned_df)

    return aligned


# USAGE EXAMPLE:
# cleaner = DataCleaner()
# ff_factors = pd.read_csv('ff_daily_factors.csv', index_col=0, parse_dates=True)
# vix = pd.read_csv('vix_daily.csv', index_col=0, parse_dates=True)
# etf = pd.read_csv('MTUM_daily.csv', index_col=0, parse_dates=True)
#
# # Before alignment:
# print(len(ff_factors))  # 26,129 days
# print(len(vix))         # 3,403 days
# print(len(etf))         # 3,208 days
#
# # Align with inner join (intersection)
# aligned = cleaner.align_calendars([ff_factors, vix, etf], method='inner')
#
# # After alignment:
# print(len(aligned[0]))  # 3,174 days (all same length!)
# print(len(aligned[1]))  # 3,174 days
# print(len(aligned[2]))  # 3,174 days
#
# WHY WE LOSE DATA:
# - ETF started trading in 2013 → can't use data before 2013
# - VIX not available on some holidays → can't use those days
# - Final dataset: Intersection of all available dates
```

---

## 4. Crowding Index (`features/crowding.py`)

### Complete Annotated Example - Z-Score Computation:

```python
def compute_zscore(
    self,
    series: pd.Series,
    window: Optional[int] = None
) -> pd.Series:
    """Compute z-score normalization of a time series.

    Z-score transforms data to have:
    - Mean = 0
    - Standard deviation = 1

    WHY USE Z-SCORES?
    - Makes different units comparable
    - Example: Can't directly compare volume (millions) vs returns (%)
    - Z-score puts everything on same scale

    FORMULA:
    z = (x - μ) / σ

    Where:
    - x = observation
    - μ = mean
    - σ = standard deviation

    INTERPRETATION:
    - z = 0: At the mean
    - z = 1: One standard deviation above mean
    - z = -1: One standard deviation below mean
    - z > 2: Unusually high (97.5th percentile if normal)
    - z < -2: Unusually low (2.5th percentile if normal)

    Args:
        series: Time series to normalize
        window: If None, use full-sample mean/std
                If int, use rolling mean/std (more adaptive)

    Returns:
        Z-scored series (same length as input)

    Example:
        Input:  [10, 20, 30, 40, 50]
        Mean:   30
        Std:    15.81
        Output: [-1.26, -0.63, 0, 0.63, 1.26]
    """

    # Handle missing data
    if series.isna().all():
        # If all NaN, return NaN series
        return pd.Series(np.nan, index=series.index)

    if window is None:
        # FULL-SAMPLE Z-SCORE (static)
        # Calculate mean and std once, for entire series

        mean = series.mean()  # Average of all observations
        std = series.std()    # Standard deviation of all observations

        if std == 0:
            # Edge case: If no variation, can't normalize
            # Example: series = [5, 5, 5, 5] → std = 0
            logger.warning("Zero standard deviation - returning zeros")
            return pd.Series(0, index=series.index)

        # Vectorized computation (fast!)
        # (series - mean) subtracts mean from each value
        # / std divides each value by standard deviation
        zscore = (series - mean) / std

    else:
        # ROLLING Z-SCORE (adaptive)
        # Use only recent data for mean/std calculation
        # More responsive to regime changes

        # Rolling mean: average of last 'window' values
        # Example with window=3:
        # [10, 20, 30, 40, 50]
        #       ^^^^^ mean = 20 (first 3)
        #          ^^^^^ mean = 30 (next 3)
        #             ^^^^^ mean = 40 (last 3)
        rolling_mean = series.rolling(window=window, min_periods=1).mean()

        # Rolling std: standard deviation of last 'window' values
        rolling_std = series.rolling(window=window, min_periods=1).std()

        # Avoid division by zero
        # Replace std=0 with NaN (will be handled later)
        rolling_std = rolling_std.replace(0, np.nan)

        # Compute z-score for each point using its local mean/std
        zscore = (series - rolling_mean) / rolling_std

    # Fill any remaining NaN (from division by zero or insufficient data)
    zscore = zscore.fillna(0)

    return zscore


# WHEN TO USE EACH METHOD:
#
# Full-sample (window=None):
# - Pro: Stable, doesn't change if you add more data
# - Pro: Uses all available information
# - Con: Assumes constant mean/std over time (unrealistic for markets)
# - Use when: Creating a fixed index for publication
#
# Rolling (window=20):
# - Pro: Adapts to changing market conditions
# - Pro: Recent high volume more meaningful than historical high
# - Con: Changes as new data arrives
# - Con: Less data for early observations
# - Use when: Real-time monitoring, regime changes expected
#
# EXAMPLE:
# series = pd.Series([100, 200, 300, 150, 250])
#
# z_full = compute_zscore(series, window=None)
# # Uses mean=200, std=79.06
# # Result: [-1.26, 0, 1.26, -0.63, 0.63]
#
# z_roll = compute_zscore(series, window=3)
# # First point: mean=100, std=0 → z=0
# # Second: mean=150, std=70.7 → z=0.71
# # Third: mean=200, std=100 → z=1.0
# # Etc.
```

---

## 5. Drawdown Analysis (`analysis/drawdowns.py`)

### Complete Annotated Example - Drawdown Computation:

```python
def compute_drawdown(self, returns: pd.Series) -> pd.DataFrame:
    """Compute drawdown series from returns.

    DRAWDOWN: Decline from peak value

    INTUITION:
    - You invest $100
    - Grows to $150 (new peak!)
    - Falls to $120
    - Drawdown = (120 - 150) / 150 = -20%
    - You're 20% below your peak

    IMPORTANT PROPERTIES:
    - Drawdown ≤ 0 always (0 = at peak, negative = below peak)
    - Resets to 0 when new peak reached
    - Measures unrealized loss from peak

    Args:
        returns: Series of returns (e.g., daily returns)

    Returns:
        DataFrame with:
        - 'cumulative': Cumulative returns (growth of $1)
        - 'running_max': Peak value so far
        - 'drawdown': Current drawdown (≤ 0)

    Example:
        returns = [0.10, 0.05, -0.15, 0.20, -0.05]

        cumulative = [1.10, 1.155, 0.981, 1.177, 1.118]
        running_max = [1.10, 1.155, 1.155, 1.177, 1.177]
        drawdown = [0%, 0%, -15.1%, 0%, -5.0%]
    """

    # STEP 1: Compute cumulative returns
    # This is like tracking $1 invested at the start
    # (1 + r1) * (1 + r2) * (1 + r3) * ...

    cumulative = (1 + returns).cumprod()
    # Example:
    # returns = [0.10, -0.05, 0.02]
    # cumulative = [1.10, 1.045, 1.066]
    # Interpretation: $1 → $1.10 → $1.045 → $1.066

    # STEP 2: Compute running maximum
    # This tracks the highest value reached so far

    running_max = cumulative.cummax()
    # Example:
    # cumulative = [1.10, 1.045, 1.20, 1.15]
    # running_max = [1.10, 1.10, 1.20, 1.20]
    #                 ^^^   ^^^   ^^^   ^^^
    #                peak  same  new   same

    # STEP 3: Compute drawdown
    # Drawdown = (current value - peak) / peak

    drawdown = (cumulative / running_max) - 1
    # Example:
    # cumulative = [1.10, 1.045, 1.20, 1.15]
    # running_max = [1.10, 1.10, 1.20, 1.20]
    # drawdown = [0%, -5%, 0%, -4.2%]
    #
    # Interpretation:
    # - Day 1: At peak (0% drawdown)
    # - Day 2: 5% below peak
    # - Day 3: New peak! (0% drawdown)
    # - Day 4: 4.2% below new peak

    # STEP 4: Package into DataFrame
    result = pd.DataFrame({
        'cumulative': cumulative,
        'running_max': running_max,
        'drawdown': drawdown
    }, index=returns.index)

    return result


# USAGE EXAMPLE:
# analyzer = DrawdownAnalyzer()
#
# # Load momentum factor returns
# mom_returns = pd.read_csv('data/processed/master_dataset.csv')['Mom']
#
# # Compute drawdowns
# dd = analyzer.compute_drawdown(mom_returns)
#
# # Find worst drawdown
# worst_dd = dd['drawdown'].min()
# worst_date = dd['drawdown'].idxmin()
# print(f"Worst drawdown: {worst_dd:.2%} on {worst_date}")
#
# # Plot drawdown over time
# import matplotlib.pyplot as plt
# dd['drawdown'].plot(title='Momentum Drawdowns')
# plt.ylabel('Drawdown (%)')
# plt.axhline(y=0, color='r', linestyle='--')  # Reference line at 0
# plt.fill_between(dd.index, dd['drawdown'], 0, alpha=0.3, color='red')
# plt.show()
```

---

## 6. Predictive Modeling (`models/predict.py`)

### Complete Annotated Example - Feature Engineering:

```python
def prepare_predictive_dataset(
    self,
    master_data: pd.DataFrame,
    crowding_index: pd.Series,
    crash_flags: pd.Series,
    forward_window: int = 5
) -> pd.DataFrame:
    """Prepare dataset for crash prediction.

    MACHINE LEARNING SETUP:
    - X (features): What we observe today
    - Y (target): Whether crash happens in next N days

    CRITICAL: We're FORECASTING, not fitting!
    - Use today's crowding to predict tomorrow's crash
    - This is harder than explaining today's crash with today's crowding

    Args:
        master_data: All features (factors, VIX, etc.)
        crowding_index: Our main predictor
        crash_flags: Binary crash indicators from drawdown analysis
        forward_window: How many days ahead to predict

    Returns:
        DataFrame with features (X) and target (Y)
    """

    # Initialize empty DataFrame with same index as master_data
    df = pd.DataFrame(index=master_data.index)

    # ============================================
    # FEATURE 1: Crowding Index (main predictor)
    # ============================================
    df["crowding_index"] = crowding_index
    # Today's crowding level

    # ============================================
    # FEATURE 2-4: VIX (market stress)
    # ============================================
    vix = master_data["VIX"]

    # Raw VIX level
    df["vix"] = vix

    # Binary indicator: Is stress HIGH?
    # High = above 75th percentile of historical VIX
    vix_75 = vix.quantile(0.75)
    df["vix_high_stress"] = (vix > vix_75).astype(int)
    # Returns 1 if True, 0 if False

    # Binary indicator: Is stress LOW?
    # Low = below 25th percentile
    vix_25 = vix.quantile(0.25)
    df["vix_low_stress"] = (vix < vix_25).astype(int)

    # WHY BINARY INDICATORS?
    # - Captures non-linear effects
    # - "VIX > 30" might matter more than exact VIX level
    # - Model can learn: "High VIX + high crowding = extra dangerous"

    # ============================================
    # FEATURE 5-6: Momentum Behavior (control)
    # ============================================
    if "Mom" in master_data.columns:
        mom = master_data["Mom"]

        # Recent momentum volatility (20-day rolling std)
        df["mom_vol_20d"] = mom.rolling(20).std()
        # High volatility = turbulent momentum = potential danger

        # Recent momentum returns (20-day cumulative)
        df["mom_ret_20d"] = mom.rolling(20).sum()
        # Recent gains/losses in momentum
        # "Buy the top" effect: Big gains → potential reversal

    # ============================================
    # FEATURE 7: Market Behavior (control)
    # ============================================
    if "Mkt-RF" in master_data.columns:
        mkt = master_data["Mkt-RF"]

        # Recent market returns (20-day cumulative)
        df["mkt_ret_20d"] = mkt.rolling(20).sum()
        # Strong recent gains often precede corrections

    # ============================================
    # TARGET VARIABLE (Y) - THE CRUCIAL PART!
    # ============================================
    # shift(-forward_window) looks FORWARD in time
    # This is PREDICTION, not explanation!

    df["crash_target"] = crash_flags.shift(-forward_window).fillna(0).astype(int)

    # Example with forward_window=5:
    # Date       Crowding  crash_flags  crash_target
    # 2020-01-01    0.5        0            0  ← crash_flags[2020-01-06]
    # 2020-01-02    0.7        0            0  ← crash_flags[2020-01-07]
    # 2020-01-03    0.9        0            1  ← crash_flags[2020-01-08] = crash!
    # 2020-01-04    1.2        0            1
    # 2020-01-05    1.5        0            1
    # 2020-01-06    1.3        1            0
    # 2020-01-07    0.8        1            0
    # 2020-01-08    0.4        1            NaN ← No future data

    # Question: Can we predict 2020-01-08 crash using 2020-01-03 crowding?
    # Answer: Look at row 2020-01-03, crash_target = 1 → YES!

    # ============================================
    # FEATURE 8: Interaction Term
    # ============================================
    if "vix_high_stress" in df.columns:
        df["crowding_x_stress"] = df["crowding_index"] * df["vix_high_stress"]
    # Captures: "Is crowding MORE dangerous when stress is already high?"
    # Or: "Is crowding LESS dangerous because everyone's already scared?"

    # ============================================
    # DATA CLEANING
    # ============================================
    # Drop rows with missing values
    # Why? Most ML models can't handle NaN
    initial_len = len(df)
    df = df.dropna()
    dropped = initial_len - len(df)

    logger.info(f"Dataset prepared: {len(df)} observations ({dropped} dropped)")

    # Final dataset structure:
    # - Rows: Daily observations
    # - Columns: Features (X) + target (Y)
    # - Each row: "Given X today, does Y happen in 5 days?"

    return df


# KEY INSIGHTS:
#
# 1. Time-series forecasting is HARD:
#    - Must use past to predict future
#    - Can't use future information (data leakage!)
#    - shift(-5) creates forward-looking target
#
# 2. Feature engineering matters:
#    - Raw features (crowding, VIX)
#    - Derived features (volatility, cumulative returns)
#    - Binary indicators (high/low stress)
#    - Interactions (crowding × stress)
#
# 3. Control variables important:
#    - Momentum volatility controls for market turbulence
#    - Recent returns control for "buy the top" effect
#    - Without controls, might confuse crowding with other effects
#
# 4. Forward window choice:
#    - Longer window (20 days): Easier to predict, less actionable
#    - Shorter window (1 day): Harder to predict, more actionable
#    - 5 days: Good balance (1 trading week)
```

---

## Summary of Key Patterns

### 1. **Data Validation Pattern**
```python
if data is None or data.empty:
    logger.warning("No data to process")
    return empty_result

if not isinstance(data, pd.DataFrame):
    raise TypeError(f"Expected DataFrame, got {type(data)}")
```

### 2. **Error Handling Pattern**
```python
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    # Attempt recovery or raise
    raise
finally:
    cleanup()
```

### 3. **Logging Pattern**
```python
logger.info("Starting operation...")
logger.debug(f"Processing {len(data)} rows")
# ... operation ...
logger.info(f"Completed: {result}")
```

### 4. **Configuration Pattern**
```python
# Don't hardcode values
threshold = 0.01  # BAD

# Use configuration
threshold = config.crash_threshold_pct  # GOOD
```

### 5. **Defensive Programming**
```python
# Check assumptions
assert len(aligned) == len(original), "Length mismatch!"

# Validate inputs
if window <= 0:
    raise ValueError("Window must be positive")

# Handle edge cases
if std == 0:
    return default_value
```

---

This walkthrough provides the deep technical understanding needed to confidently modify and extend the codebase. Each section builds on the previous, creating a complete mental model of how the system works.
