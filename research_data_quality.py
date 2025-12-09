import yfinance as yf
import pandas as pd
from logger import logger

def research_data_quality(symbol: str):
    print(f"Analyzing data availability for {symbol}...")
    ticker = yf.Ticker(symbol)
    
    # 1. Balance Sheet
    print("\n--- Balance Sheet Keys ---")
    try:
        bs = ticker.balance_sheet
        if not bs.empty:
            print(list(bs.index))
        else:
            print("❌ Balance Sheet is empty")
    except Exception as e:
        print(f"❌ Error fetching Balance Sheet: {e}")

    # 2. Financials
    print("\n--- Income Statement Keys ---")
    try:
        inc = ticker.financials
        if not inc.empty:
            print(list(inc.index))
        else:
            print("❌ Income Statement is empty")
    except Exception as e:
        print(f"❌ Error fetching Income Statement: {e}")

    # 3. Cash Flow
    print("\n--- Cash Flow Keys ---")
    try:
        cf = ticker.cashflow
        if not cf.empty:
            print(list(cf.index))
        else:
            print("❌ Cash Flow Keys is empty")
    except Exception as e:
        print(f"❌ Error fetching Cash Flow: {e}")

if __name__ == "__main__":
    research_data_quality("AAPL")
    research_data_quality("NVDA")
