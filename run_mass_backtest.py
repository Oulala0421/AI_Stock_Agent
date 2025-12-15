
import sys
import os
import pandas as pd
from datetime import datetime, timedelta
from backtest_engine import BacktestEngine
from sheet_manager import get_stock_lists
from logger import logger

# Suppress excessive logging during mass test
import logging as py_logging
py_logging.getLogger('ai_agent').setLevel(py_logging.WARNING)
py_logging.getLogger('market_data').setLevel(py_logging.WARNING)
py_logging.getLogger('google_news_searcher').setLevel(py_logging.WARNING)
py_logging.getLogger('news_agent').setLevel(py_logging.WARNING)

def run_mass_backtest():
    print("🚀 Starting Mass Backtest (180 Days)...")
    print("Fetching ticker list from Google Sheets...")
    
    try:
        holdings, watchlist, _, _ = get_stock_lists()
        all_tickers = list(set(holdings + watchlist))
        
        if not all_tickers:
            print("⚠️ Sheet returned empty list. Using default list.")
            all_tickers = ["AAPL", "NVDA", "MSFT", "TSLA", "GOOGL", "AMZN", "META", "AMD", "SPY", "QQQ"]
    except Exception as e:
        print(f"⚠️ Failed to fetch from sheets: {e}. Using default list.")
        all_tickers = ["AAPL", "NVDA", "MSFT", "TSLA", "GOOGL", "AMZN", "META", "AMD", "SPY", "QQQ"]
        
    print(f"📋 Testing {len(all_tickers)} Tickers: {all_tickers}")
    
    results = []
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1095) # 3 Years (Academic Scale)
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    for ticker in all_tickers:
        print(f"🔄 Testing {ticker}...", end="", flush=True)
        try:
            engine = BacktestEngine(ticker, start_str, end_str, initial_capital=10000.0)
            engine.run()
            
            # Extract Metrics
            trades_count = len(engine.ledger)
            final_val = engine.capital + (engine.holdings * engine.mock_adapter.get_price_data(ticker)['Close'].iloc[-1])
            return_pct = (final_val - 10000) / 10000
            
            # Check if any BUY signal occurred at all (even if not executed due to cash)
            # Actually ledger tracks executed trades.
            
            results.append({
                "Ticker": ticker,
                "Trades": trades_count,
                "Return": return_pct,
                "Final": final_val,
                "Note": "Active" if trades_count > 0 else "No Action"
            })
            print(f" Done. (Trades: {trades_count}, Ret: {return_pct:.1%})")
            
        except Exception as e:
            print(f" Failed: {e}")
            results.append({
                "Ticker": ticker,
                "Trades": 0,
                "Return": 0.0,
                "Final": 10000.0,
                "Note": f"Error: {str(e)[:20]}"
            })

    # Summary
    print("\n" + "="*50)
    print("📊 MASS BACKTEST RESULTS (Last 180 Days)")
    print("="*50)
    df_res = pd.DataFrame(results)
    if not df_res.empty:
        df_res = df_res.sort_values(by='Return', ascending=False)
        print(df_res.to_string(index=False, float_format=lambda x: "{:.1%}".format(x) if abs(x)<10 else "{:.2f}".format(x)))
        
        total_trades = df_res['Trades'].sum()
        avg_return = df_res['Return'].mean()
        print("-" * 50)
        print(f"Total Trades Logged: {total_trades}")
        print(f"Average Return:      {avg_return:.2%}")
        
    return df_res

if __name__ == "__main__":
    run_mass_backtest()
