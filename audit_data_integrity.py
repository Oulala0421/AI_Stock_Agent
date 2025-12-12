from database_manager import DatabaseManager
from logger import logger

def audit_stock(symbol):
    print(f"\n🔍 Auditing {symbol}...")
    db = DatabaseManager()
    data = db.get_latest_stock_data(symbol)
    
    if not data:
        print("❌ No data found.")
        return

    # 1. Status Check
    db_status = data.get('status')
    raw_status = data.get('raw_data', {}).get('overall_status')
    print(f"Status (Root): {db_status}")
    print(f"Status (Raw):  {raw_status}")
    
    if db_status == raw_status:
        print("✅ Status Consistency: OK")
    else:
        print("⚠️ Status Mismatch (Fix applied in app.py handles this, but good to note)")

    # 2. Sparkline Check
    sparkline = data.get('sparkline', [])
    print(f"Sparkline Length: {len(sparkline)}")
    print(f"Sparkline Data (First 3): {sparkline[:3]}")
    print(f"Sparkline Data (Last 3):  {sparkline[-3:]}")
    
    if len(sparkline) == 14:
        print("✅ Sparkline Duration: 14 Days (Correct)")
    elif len(sparkline) > 0:
        print(f"⚠️ Sparkline Duration: {len(sparkline)} Days (Expected 14)")
    else:
        print("❌ Sparkline Empty")

if __name__ == "__main__":
    # Test a few unlikely to be empty
    audit_stock("VOO")   # ETF (Likely PASS/WATCHLIST)
    audit_stock("NVDA")  # Stock
    audit_stock("PLTR")  # Stock
