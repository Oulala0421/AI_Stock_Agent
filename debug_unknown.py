from database_manager import DatabaseManager
from garp_strategy import GARPStrategy
from logger import logger
import json

def debug_stock(symbol="NVDA"):
    print(f"=== Debugging {symbol} ===")
    
    # 1. Check DB
    db = DatabaseManager()
    latest = db.get_latest_stock_data(symbol)
    if latest:
        print(f"\n[MongoDB Data]")
        print(f"Date: {latest.get('date')}")
        print(f"Status in Root: {latest.get('status')}")
        raw = latest.get('raw_data', {})
        print(f"Status in Raw: {raw.get('overall_status')}")
        print(f"Raw Keys: {list(raw.keys())}")
    else:
        print("\n[MongoDB] No data found.")

    # 2. Run Analysis
    print(f"\n[Live Analysis]")
    strategy = GARPStrategy()
    card = strategy.analyze(symbol)
    print(f"Result Status: {card.overall_status}")
    print(f"Result Reason: {card.overall_reason}")
    print(f"Red Flags: {card.red_flags}")

if __name__ == "__main__":
    debug_stock("NVDA")
    print("-" * 20)
    debug_stock("PLTR")
