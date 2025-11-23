import yfinance as yf
import pandas as pd
import os
import sys

# Add parent directory to path to import sheet_manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sheet_manager import get_stock_lists

def fetch_all_data(start_date, end_date):
    """
    Fetch historical data for all stocks in Google Sheets + Benchmark + VIX
    """
    print("📥 正在讀取 Google Sheets 獲取股票清單...")
    my_holdings, my_watchlist, _, stock_types = get_stock_lists()
    
    # Combine unique symbols
    all_symbols = list(set(my_holdings + my_watchlist))
    
    # Add benchmarks
    tickers = all_symbols + ["SPY", "^VIX"]
    
    print(f"🌍 準備下載 {len(tickers)} 檔標的數據: {tickers}")
    print(f"📅 區間: {start_date} ~ {end_date}")
    
    # Download in bulk
    data = yf.download(tickers, start=start_date, end=end_date, group_by='ticker', auto_adjust=True)
    
    # Reformat to dictionary of DataFrames for easier access
    data_dict = {}
    
    # Handle single ticker case (yf.download returns different structure)
    if len(tickers) == 1:
        data_dict[tickers[0]] = data
    else:
        for ticker in tickers:
            try:
                df = data[ticker].copy()
                # Drop rows where all columns are NaN
                df.dropna(how='all', inplace=True)
                if not df.empty:
                    data_dict[ticker] = df
            except KeyError:
                print(f"⚠️ 無法獲取 {ticker} 數據")
                
    print(f"✅ 成功下載 {len(data_dict)} 檔標的歷史數據")
    return data_dict, all_symbols, stock_types
