"""
run_backtest.py
Python Wrapper for GNU Octave Backtesting System
Automates data export, Octave execution, and result visualization
"""

import subprocess
import os
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from octave.data_exporter import export_for_backtest


def check_octave_installed():
    """Check if GNU Octave is installed and accessible"""
    try:
        result = subprocess.run(['octave', '--version'], 
                                capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"✅ {version}")
            return True
        else:
            print("❌ Octave is installed but returned an error")
            return False
    except FileNotFoundError:
        print("❌ GNU Octave not found in PATH")
        print("Please install Octave from: https://octave.org/download")
        return False
    except Exception as e:
        print(f"❌ Error checking Octave: {e}")
        return False


def run_octave_backtest(symbol, stock_type='Satellite', years_back=10, 
                        run_wfa=True, run_mc=True):
    """
    Complete backtesting pipeline
    
    Parameters:
    -----------
    symbol : str
        Stock ticker symbol (e.g., 'SPY', 'QQQ')
    stock_type : str
        'Core' or 'Satellite' strategy type
    years_back : int
        Number of years of historical data
    run_wfa : bool
        Run Walk-Forward Analysis (slower but more rigorous)
    run_mc : bool
        Run Monte Carlo simulation (slower but validates significance)
    
    Returns:
    --------
    dict : Results summary
    """
    
    print("=" * 60)
    print("GNU OCTAVE BACKTESTING SYSTEM")
    print("=" * 60)
    print(f"\n📊 Symbol: {symbol}")
    print(f"🎯 Strategy: {stock_type}")
    print(f"📅 Period: {years_back} years")
    print(f"🔄 Walk-Forward: {'Yes' if run_wfa else 'No'}")
    print(f"🎲 Monte Carlo: {'Yes' if run_mc else 'No'}\n")
    
    # Step 1: Check Octave installation
    print("🔍 Checking Octave installation...")
    if not check_octave_installed():
        return None
    
    # Step 2: Export data
    print(f"\n📥 Exporting {symbol} data ({years_back} years)...")
    
    octave_dir = Path(__file__).parent
    try:
        metadata = export_for_backtest(symbol, years_back)
        if symbol not in metadata or 'error' in metadata[symbol]:
            print(f"❌ Data export failed for {symbol}")
            return None
        print(f"✅ Data exported: {metadata[symbol]['data_points']} bars")
    except Exception as e:
        print(f"❌ Export error: {e}")
        return None
    
    # Step 3: Run Octave backtest
    print(f"\n🚀 Running Octave backtest...")
    print("This may take several minutes, especially with Monte Carlo enabled...\n")
    
    # Build Octave command
    octave_cmd = (
        f"cd('{octave_dir}'); "
        f"run_full_backtest('{symbol}', '{stock_type}', {years_back}, "
        f"{str(run_wfa).lower()}, {str(run_mc).lower()})"
    )
    
    try:
        # Run Octave
        result = subprocess.run(
            ['octave', '--no-gui', '--eval', octave_cmd],
            capture_output=True,
            text=True,
            timeout=1800,  # 30 minute timeout
            cwd=octave_dir
        )
        
        # Display output
        if result.stdout:
            print(result.stdout)
        
        if result.returncode != 0:
            print(f"\n❌ Octave execution failed (exit code {result.returncode})")
            if result.stderr:
                print(f"Error details:\n{result.stderr}")
            return None
        
        print("\n✅ Octave backtest completed successfully!")
        
    except subprocess.TimeoutExpired:
        print("\n❌ Backtest timed out (>30 minutes)")
        return None
    except Exception as e:
        print(f"\n❌ Execution error: {e}")
        return None
    
    # Step 4: Parse results
    summary_file = octave_dir / f"{symbol}_{stock_type}_summary.txt"
    
    if summary_file.exists():
        print(f"\n📊 Results saved to: {summary_file}")
        with open(summary_file, 'r') as f:
            print("\n" + "=" * 60)
            print(f.read())
            print("=" * 60)
    
    return {
        'symbol': symbol,
        'stock_type': stock_type,
        'summary_file': str(summary_file)
    }


def batch_backtest(symbols, stock_type='Satellite', years_back=10):
    """
    Run backtests for multiple symbols
    
    Parameters:
    -----------
    symbols : list
        List of ticker symbols
    stock_type : str
        'Core' or 'Satellite'
    years_back : int
        Years of data
    
    Returns:
    --------
    pd.DataFrame : Summary table of all results
    """
    
    print("\n" + "=" * 60)
    print(f"BATCH BACKTESTING: {len(symbols)} symbols")
    print("=" * 60 + "\n")
    
    results = []
    
    for i, symbol in enumerate(symbols):
        print(f"\n[{i+1}/{len(symbols)}] Processing {symbol}...")
        print("-" * 60)
        
        result = run_octave_backtest(
            symbol, 
            stock_type=stock_type, 
            years_back=years_back,
            run_wfa=False,  # Disable WFA for faster batch processing
            run_mc=True     # Keep Monte Carlo for significance testing
        )
        
        if result:
            results.append(result)
    
    print("\n" + "=" * 60)
    print(f"✅ Batch complete: {len(results)}/{len(symbols)} successful")
    print("=" * 60 + "\n")
    
    return pd.DataFrame(results)


if __name__ == "__main__":
    """
    Usage Examples:
    
    1. Single symbol backtest:
       python run_backtest.py
    
    2. Custom parameters:
       Open this file and modify the examples below
    """
    
    # Example 1: Quick backtest (SPY, 5 years, no WFA)
    print("\n🎯 Example 1: Quick SPY Backtest (5 years)\n")
    run_octave_backtest(
        symbol='SPY',
        stock_type='Core',
        years_back=5,
        run_wfa=False,
        run_mc=True
    )
    
    # Example 2: Comprehensive backtest (with WFA)
    # print("\n🎯 Example 2: Comprehensive NVDA Backtest (10 years with WFA)\n")
    # run_octave_backtest(
    #     symbol='NVDA',
    #     stock_type='Satellite',
    #     years_back=10,
    #     run_wfa=True,
    #     run_mc=True
    # )
    
    # Example 3: Batch testing
    # watchlist = ['SPY', 'QQQ', 'AAPL', 'MSFT']
    # results_df = batch_backtest(watchlist, stock_type='Satellite', years_back=5)
    # print("\nBatch Results:")
    # print(results_df)
    
    print("\n🎉 All backtests complete!")
