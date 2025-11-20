"""
Data Exporter Module for GNU Octave Integration
Fetches US stock data with proper adjustments and exports to MAT format
"""

import yfinance as yf
import pandas as pd
import numpy as np
import scipy.io as sio
from datetime import datetime, timedelta
import os
import warnings
warnings.filterwarnings('ignore')


def python_datetime_to_matlab_datenum(dt):
    """
    Convert Python datetime to MATLAB serial date number
    MATLAB: Days since January 0, 0000 (proleptic Gregorian calendar)
    Python: Uses datetime.toordinal() which is days since 0001-01-01
    
    Formula: MATLAB datenum = Python ordinal + 366
    (366 accounts for year 0 in MATLAB convention)
    """
    if isinstance(dt, pd.Timestamp):
        dt = dt.to_pydatetime()
    return dt.toordinal() + 366


def validate_data_quality(df, symbol):
    """
    Validate data for common issues:
    - Large price gaps (potential missing splits)
    - Missing data
    - Volume anomalies
    
    Returns: (is_valid, warnings_list)
    """
    warnings_list = []
    
    # Check for missing data
    if df.isnull().any().any():
        null_counts = df.isnull().sum()
        warnings_list.append(f"Missing data detected: {null_counts[null_counts > 0].to_dict()}")
    
    # Check for large price gaps (>20% in one day, might indicate missing split adjustment)
    returns = df['Close'].pct_change()
    large_gaps = returns[abs(returns) > 0.20]
    if not large_gaps.empty:
        warnings_list.append(f"Large price gaps detected on dates: {large_gaps.index.tolist()}")
    
    # Check volume consistency post-split (should increase, not disappear)
    volume_changes = df['Volume'].pct_change()
    volume_drops = volume_changes[volume_changes < -0.90]
    if not volume_drops.empty:
        warnings_list.append(f"Suspicious volume drops on: {volume_drops.index.tolist()[:5]}")
    
    is_valid = len(warnings_list) == 0
    return is_valid, warnings_list


def export_symbol(symbol, start_date, end_date, output_path=None, validate=True):
    """
    Export single symbol to MAT format for Octave
    
    Parameters:
    -----------
    symbol : str
        Stock ticker symbol
    start_date : str
        Start date in 'YYYY-MM-DD' format
    end_date : str
        End date in 'YYYY-MM-DD' format
    output_path : str, optional
        Output MAT file path. If None, auto-generated as 'octave/{symbol}_data.mat'
    validate : bool
        Whether to perform data quality validation
    
    Returns:
    --------
    dict : Export metadata (file_path, data_points, date_range, warnings)
    """
    
    print(f"📥 Fetching {symbol} data ({start_date} to {end_date})...")
    
    try:
        # Download with auto_adjust=True for split/dividend adjustment
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date, auto_adjust=True)
        
        if df.empty:
            raise ValueError(f"No data returned for {symbol}")
        
        # Validation
        warnings_list = []
        if validate:
            is_valid, warnings_list = validate_data_quality(df, symbol)
            if not is_valid:
                print(f"⚠️ Data quality warnings for {symbol}:")
                for warning in warnings_list:
                    print(f"  - {warning}")
        
        # Convert datetime index to MATLAB serial date numbers
        dates_matlab = np.array([python_datetime_to_matlab_datenum(dt) for dt in df.index])
        
        # Prepare data structure for MAT export
        # Note: Octave expects column vectors (N×1), so we reshape
        data_dict = {
            'symbol': symbol,
            'dates': dates_matlab.reshape(-1, 1),
            'open': df['Open'].values.reshape(-1, 1),
            'high': df['High'].values.reshape(-1, 1),
            'low': df['Low'].values.reshape(-1, 1),
            'close': df['Close'].values.reshape(-1, 1),  # This is adjusted close
            'volume': df['Volume'].values.reshape(-1, 1)
        }
        
        # Generate output path
        if output_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            output_path = os.path.join(script_dir, f"{symbol}_data.mat")
        
        # Export to MAT format (MATLAB v7.3 compatible with Octave)
        sio.savemat(output_path, data_dict, format='5', do_compression=True)
        
        metadata = {
            'symbol': symbol,
            'file_path': output_path,
            'data_points': len(df),
            'date_range': f"{df.index[0].date()} to {df.index[-1].date()}",
            'warnings': warnings_list,
            'columns': list(df.columns)
        }
        
        print(f"✅ Exported {len(df)} data points to: {output_path}")
        
        return metadata
        
    except Exception as e:
        print(f"❌ Export failed for {symbol}: {e}")
        raise


def export_batch(symbols, start_date, end_date, output_dir=None):
    """
    Export multiple symbols in batch
    
    Parameters:
    -----------
    symbols : list
        List of ticker symbols
    start_date, end_date : str
        Date range
    output_dir : str, optional
        Output directory for MAT files
    
    Returns:
    --------
    dict : Summary of exports {symbol: metadata}
    """
    
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(__file__))
    
    results = {}
    
    for symbol in symbols:
        try:
            output_path = os.path.join(output_dir, f"{symbol}_data.mat")
            metadata = export_symbol(symbol, start_date, end_date, output_path)
            results[symbol] = metadata
        except Exception as e:
            results[symbol] = {'error': str(e)}
    
    # Summary report
    success_count = sum(1 for r in results.values() if 'error' not in r)
    print(f"\n📊 Batch Export Summary: {success_count}/{len(symbols)} successful")
    
    return results


def export_for_backtest(symbols, years_back=10):
    """
    Convenience function for backtesting
    Exports symbols with reasonable defaults
    
    Parameters:
    -----------
    symbols : str or list
        Single symbol or list of symbols
    years_back : int
        Number of years of historical data
    
    Returns:
    --------
    dict : Export results
    """
    
    if isinstance(symbols, str):
        symbols = [symbols]
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=years_back*365)).strftime('%Y-%m-%d')
    
    print(f"🔬 Backtesting Data Export: {start_date} to {end_date}")
    print(f"Symbols: {', '.join(symbols)}\n")
    
    return export_batch(symbols, start_date, end_date)


if __name__ == "__main__":
    """
    Usage examples:
    
    # Single symbol export
    python data_exporter.py
    
    # This will export SPY for last 10 years
    """
    
    # Default: Export SPY for backtesting
    print("=" * 60)
    print("Data Exporter for GNU Octave Backtesting")
    print("=" * 60)
    
    # Example 1: Single symbol
    metadata = export_for_backtest('SPY', years_back=10)
    
    # Example 2: Multiple symbols (Core-Satellite example)
    # core_symbols = ['VOO', 'QQQ', 'SMH']
    # satellite_symbols = ['NVDA', 'TSLA', 'AAPL']
    # all_symbols = core_symbols + satellite_symbols
    # results = export_for_backtest(all_symbols, years_back=5)
    
    print("\n🎯 Export complete! Ready for Octave backtesting.")
