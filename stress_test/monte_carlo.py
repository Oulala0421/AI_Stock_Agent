import numpy as np
import pandas as pd
import time

# Try to import CuPy for GPU acceleration
try:
    import cupy as cp
    HAS_GPU = True
    print("🚀 GPU 加速已啟用 (CuPy detected)")
except ImportError:
    HAS_GPU = False
    print("⚠️ 未檢測到 CuPy，將使用 CPU (NumPy) 進行模擬")

def run_monte_carlo_simulation(portfolio_value, daily_returns, num_simulations=100000, days=252):
    """
    Run Monte Carlo Simulation to predict future portfolio value distribution.
    
    portfolio_value: Current total portfolio value
    daily_returns: Series of historical daily returns of the portfolio
    num_simulations: Number of paths to simulate (default: 100,000 per academic literature)
    days: Number of days to simulate (e.g., 252 for 1 year)
    
    Literature Standard:
    - Jorion (2007) "Value at Risk": 10,000-50,000 for VaR
    - Hull (2018) "Options, Futures": 100,000+ for robust estimates
    - Glasserman (2004) "Monte Carlo Methods": 100,000-1,000,000 for high precision
    """
    print(f"🎲 開始 Monte Carlo 模擬 ({num_simulations:,} 條路徑, {days} 天) - 符合學術標準...")
    start_time = time.time()
    
    # Calculate stats from history
    mu = daily_returns.mean()
    sigma = daily_returns.std()
    
    # Use GPU if available
    if HAS_GPU:
        xp = cp
    else:
        xp = np
        
    # Generate random paths
    # Formula: P_t = P_{t-1} * exp((mu - 0.5 * sigma^2) + sigma * Z)
    # Z ~ N(0, 1)
    
    # Create random shocks (days, simulations)
    # We simulate 'days' steps for 'num_simulations' paths
    dt = 1 # daily step
    
    # Drift and Diffusion terms
    drift = (mu - 0.5 * sigma**2)
    diffusion = sigma
    
    # Generate random numbers
    Z = xp.random.normal(0, 1, (days, num_simulations))
    
    # Calculate daily returns for all paths
    daily_log_returns = drift + diffusion * Z
    
    # Accumulate returns to get cumulative return path
    cumulative_log_returns = xp.cumsum(daily_log_returns, axis=0)
    
    # Convert to price paths
    price_paths = portfolio_value * xp.exp(cumulative_log_returns)
    
    # Get final values
    final_values = price_paths[-1]
    
    # Calculate VaR (Value at Risk)
    # 95% VaR = 5th percentile price
    percentile_5 = xp.percentile(final_values, 5)
    percentile_95 = xp.percentile(final_values, 95)
    
    var_95_value = portfolio_value - percentile_5
    
    # Transfer back to CPU if needed
    if HAS_GPU:
        final_values = cp.asnumpy(final_values)
        percentile_5 = float(percentile_5)
        percentile_95 = float(percentile_95)
        var_95_value = float(var_95_value)
        
    end_time = time.time()
    print(f"✅ 模擬完成 (耗時: {end_time - start_time:.2f} 秒)")
    
    # Financial Logic Correction:
    # Removed "Predicited" Mean/Median/Max/Min
    # Added "Volatility Range" (5th-95th percentile)
    
    results = {
        "Current_Value": portfolio_value,
        # Risk Metrics
        "VaR_95": var_95_value,
        "risk_downside_5pct": var_95_value / portfolio_value, # Percentage loss
        
        # Volatility Range (Price)
        "volatility_range_low": percentile_5,
        "volatility_range_high": percentile_95,
        
        # Removed Prediction Keys (Mean_Final_Value, etc.)
        # but keeping 'var_95' lowercase alias if needed by legacy
        "var_95": var_95_value 
    }
    
    return results
