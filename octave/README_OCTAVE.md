# GNU Octave Backtesting System for AI Stock Agent

## 📋 Overview

This module extends the AI Stock Agent with professional-grade quantitative backtesting capabilities using GNU Octave. It implements:

- ✅ **Vectorized Backtesting Engine**: No look-ahead bias, proper lag handling
- ✅ **Walk-Forward Analysis**: Out-of-sample validation to detect overfitting
- ✅ **Monte Carlo Simulation**: Statistical significance testing via permutation tests
- ✅ **Core-Satellite Strategy Testing**: Validates both conservative and aggressive approaches

## 🚀 Quick Start

### Prerequisites

1. **Python Dependencies**:
```bash
pip install scipy>=1.11.0
```

2. **GNU Octave Installation**:

**Windows:**
- Download from [https://octave.org/download](https://octave.org/download)
- Install the Windows installer (≥7.0.0)
- Add `octave` to your PATH during installation

**Verify Installation:**
```bash
octave --version
```

3. **Octave Packages** (run in Octave console):
```octave
pkg install -forge financial statistics io
```

### Running Your First Backtest

**Method 1: Python Wrapper (Recommended)**
```bash
cd c:\Users\willy\Documents\分析工具\AI_Stock_Agent
python octave/run_backtest.py
```

This will:
1. Export SPY data for the last 5 years
2. Run Core strategy backtest
3. Perform Monte Carlo validation
4. Display results

**Method 2: Direct Octave Execution**
```bash
cd octave

# Export data first
python -c "from data_exporter import export_for_backtest; export_for_backtest('SPY', 10)"

# Run in Octave
octave --no-gui
>> run_full_backtest('SPY', 'Core', 10, true, true);
```

## 📊 Understanding the Results

### Performance Metrics

| Metric | Description | Good Value |
|--------|-------------|------------|
| **Total Return** | Total % gain/loss over period | > 0% (profitable) |
| **CAGR** | Compound Annual Growth Rate | > 10% (beats inflation) |
| **Sharpe Ratio** | Risk-adjusted returns | > 1.0 (good), > 2.0 (excellent) |
| **Max Drawdown** | Largest peak-to-trough decline | < 20% (manageable) |
| **Alpha** | Excess return vs buy-and-hold | > 0% (outperformance) |

### Statistical Validation

**Permutation Test P-Value:**
- `p < 0.01`: ✅ **Highly significant** - Strategy has very strong edge
- `p < 0.05`: ✅ **Significant** - Strategy has statistical edge
- `p < 0.10`: ⚠️ **Marginally significant** - Weak edge, needs improvement
- `p ≥ 0.10`: ❌ **Not significant** - No evidence of real skill

**WFA Efficiency Ratio** (Out-of-Sample / In-Sample):
- `> 0.7`: ✅ **Excellent** - Strategy is robust and not overfit
- `> 0.5`: ✅ **Good** - Acceptable performance degradation
- `> 0.3`: ⚠️ **Moderate** - Overfitting concerns
- `< 0.3`: ❌ **Poor** - Severely overfit, do NOT trade

## 🔧 Customization

### Testing Different Symbols

```python
# In run_backtest.py or directly:
from octave.run_backtest import run_octave_backtest

run_octave_backtest(
    symbol='NVDA',        # Change symbol
    stock_type='Satellite',  # Core or Satellite
    years_back=10,        # Data period
    run_wfa=True,         # Enable Walk-Forward Analysis
    run_mc=True           # Enable Monte Carlo
)
```

### Batch Testing Multiple Symbols

```python
from octave.run_backtest import batch_backtest

watchlist = ['SPY', 'QQQ', 'VOO', 'AAPL', 'MSFT', 'NVDA']
results = batch_backtest(watchlist, stock_type='Satellite', years_back=5)
print(results)
```

### Adjusting Strategy Parameters

Edit `octave/backtest_engine.m`:

```matlab
% Line ~22-28: Modify default parameters
params.rsi_period = 14;       # RSI calculation period
params.rsi_oversold = 30;     # RSI oversold threshold
params.ma_long = 200;         # Long-term MA period
params.dual_momentum_period = 252;  # 12-month momentum
```

## 📁 File Structure

```
AI_Stock_Agent/
├── octave/
│   ├── data_exporter.py            # Python: Export data to MAT format
│   ├── run_backtest.py             # Python: Main wrapper script
│   ├── backtest_engine.m            # Octave: Core backtest logic
│   ├── monte_carlo_validation.m    # Octave: Statistical testing
│   ├── walk_forward_analysis.m     # Octave: Parameter optimization
│   ├── run_full_backtest.m         # Octave: Master orchestration
│   └── README_OCTAVE.md            # This file
└── strategy.py                     # Updated with bug fixes
```

## 🐛 Troubleshooting

### Issue: "Octave not found"
**Solution**: Ensure Octave is in your PATH. Test with `octave --version`.

### Issue: "Data file not found"
**Solution**: Run data export first:
```python
python -c "from octave.data_exporter import export_for_backtest; export_for_backtest('SPY', 10)"
```

### Issue: "Package 'financial' not found"
**Solution**: Install Octave packages:
```octave
pkg install -forge financial statistics
```

### Issue: Backtest runs forever
**Probable Cause**: Monte Carlo with 1000 simulations can take 10-30 minutes.
**Solution**: Reduce simulations in `monte_carlo_validation.m` line ~11:
```matlab
if nargin < 2
    n_simulations = 100;  % Reduce from 1000 for testing
end
```

## ⚠️ Important Notes

### Data Quality
- Always use `auto_adjust=True` in yfinance to handle splits/dividends
- Validate data quality warnings from `data_exporter.py`
- Cross-check critical periods with alternative data sources

### Look-Ahead Bias Prevention
The engine implements proper lag handling:
- Signal generated at time `t` → Position taken at time `t+1`
- This is enforced in `backtest_engine.m` line ~120: `position = [0; signal(1:end-1)]`

### Transaction Costs
Current implementation does NOT include:
- Brokerage commissions
- Slippage
- Bid-ask spreads

For realistic results with frequent trading, add ~0.1% per trade as cost buffer.

## 📈 Interpreting Your Strategy

### Example Output Interpretation

```
STRATEGY PERFORMANCE:
  Total Return:    +52.34%
  CAGR:            +8.45%
  Sharpe Ratio:    1.23
  Max Drawdown:    18.50%

Permutation Test:
  P-value:         0.0230 ** (Significant)

WFA Efficiency:    0.68 ✅ Good
```

**Analysis:**
- ✅ Positive returns and CAGR above inflation
- ✅ Sharpe > 1.0 indicates good risk-adjusted returns
- ✅ Max DD < 20% is manageable for most investors
- ✅ P-value < 0.05 confirms statistical edge (not luck)
- ✅ WFA efficiency 0.68 shows strategy is robust, not overfit

**Recommendation**: This is a **strong candidate** for paper trading.

## 🔬 Advanced Usage

### Walk-Forward Analysis with Custom Windows

```octave
% In Octave console
config = struct();
config.is_window = 756;    % 3 years in-sample
config.oos_window = 252;   % 1 year out-of-sample
config.step_size = 126;    % Move forward 6 months
config.rsi_thresholds = [25, 30, 35];
config.buy_thresholds = [60, 65, 70];

wfa_results = walk_forward_analysis('SPY_data.mat', 'Core', config);
```

### Exporting Results for Further Analysis

Results are automatically saved as:
- `{SYMBOL}_{STRATEGY}_backtest_Core.mat` - Full backtest results
- `monte_carlo_results.mat` - MC simulation data
- `walk_forward_results.mat` - WFA optimization data
- `{SYMBOL}_{STRATEGY}_summary.txt` - Text summary

Load in Python for visualization:
```python
import scipy.io as sio
results = sio.loadmat('octave/SPY_backtest_Core.mat')
equity_curve = results['results'][0][0]['equity_strategy']
```

## 📚 Further Reading

- **Research Report**: See the comprehensive research document for theoretical background
- **Walk-Forward Analysis**: Pardo, R. (2008). "The Evaluation and Optimization of Trading Strategies"
- **Monte Carlo Methods**: Aronson, D. (2006). "Evidence-Based Technical Analysis"
- **Overfitting Prevention**: Bailey, D.H., et al. (2014). "The Probability of Backtest Overfitting"

---

**Version**: 1.0  
**Last Updated**: 2025-11-20  
**Author**: AI Stock Agent Development Team
