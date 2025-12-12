from database_manager import DatabaseManager
from logger import logger

def audit_stock(symbol):
    print(f"\n{'='*60}")
    print(f"🔍 Auditing {symbol}")
    print('='*60)
    
    db = DatabaseManager()
    data = db.get_latest_stock_data(symbol)
    
    if not data:
        print(f"❌ No data found in MongoDB for {symbol}")
        return False

    # 1. Status Check
    db_status = data.get('status')
    raw_data = data.get('raw_data', {})
    raw_status = raw_data.get('overall_status')
    
    print(f"\n📊 STATUS:")
    print(f"   Root Level: {db_status}")
    print(f"   Raw Data:   {raw_status}")
    
    if db_status == raw_status:
        print(f"   ✅ Status Consistent")
    else:
        print(f"   ⚠️ Status Mismatch")

    # 2. Sparkline Check
    root_sparkline = data.get('sparkline', [])
    raw_sparkline = raw_data.get('sparkline', [])
    
    print(f"\n📈 SPARKLINE:")
    print(f"   Root Level Length: {len(root_sparkline)}")
    print(f"   Raw Data Length:   {len(raw_sparkline)}")
    
    if len(raw_sparkline) > 0:
        print(f"   First 3 values: {raw_sparkline[:3]}")
        print(f"   Last 3 values:  {raw_sparkline[-3:]}")
        print(f"   ✅ Sparkline exists in raw_data")
    else:
        print(f"   ❌ Sparkline EMPTY in raw_data")
    
    if len(root_sparkline) > 0:
        print(f"   ✅ Sparkline exists at root level")
    else:
        print(f"   ❌ Sparkline EMPTY at root level")

    # 3. Date Check
    last_update = data.get('date')
    print(f"\n📅 LAST UPDATE: {last_update}")
    
    # 4. Other metadata
    price = data.get('price', 'N/A')
    print(f"💰 PRICE: ${price}")
    
    return len(raw_sparkline) > 0 or len(root_sparkline) > 0

if __name__ == "__main__":
    symbols = ["GOOG", "TSLA", "VXUS", "SMH", "VOO"]
    
    print("\n" + "="*60)
    print("🔬 DATABASE INTEGRITY AUDIT")
    print("="*60)
    
    results = {}
    for symbol in symbols:
        has_data = audit_stock(symbol)
        results[symbol] = has_data
    
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    for symbol, has_data in results.items():
        status = "✅ HAS DATA" if has_data else "❌ NO DATA"
        print(f"{symbol:6s} - {status}")
    
    total = len(results)
    success = sum(results.values())
    print(f"\nTotal: {success}/{total} stocks have sparkline data")
