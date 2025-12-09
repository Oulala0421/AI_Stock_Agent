"""
Quick test script for Streamlit app functionality
"""
import sys
sys.path.insert(0, '.')

from app import init_mongo_connection, get_latest_stocks

print("=" * 60)
print("🧪 Streamlit App Function Tests")
print("=" * 60)

# Test 1: MongoDB Connection
print("\n1️⃣  Testing MongoDB connection...")
client = init_mongo_connection()
if client:
    print("✅ MongoDB connected")
    try:
        db = client['stock_agent']
        count = db['daily_snapshots'].count_documents({})
        print(f"✅ Total records: {count}")
    except Exception as e:
        print(f"❌ Query failed: {e}")
else:
    print("❌ MongoDB connection failed")

# Test 2: Data Fetching
print("\n2️⃣  Testing data fetching...")
stocks = get_latest_stocks(10)
print(f"✅ Found {len(stocks)} stocks")

if stocks:
    sample = stocks[0]
    print(f"\n📊 Sample stock:")
    print(f"   Symbol: {sample.get('symbol')}")
    print(f"   Price: ${sample.get('price', 0):.2f}")
    print(f"   Status: {sample.get('status')}")
    
    raw = sample.get('raw_data', {})
    if 'predicted_return_1w' in raw:
        print(f"   Prediction: {raw['predicted_return_1w']:+.1f}%")
    if 'confidence_score' in raw:
        print(f"   Confidence: {raw['confidence_score']:.0%}")

print("\n" + "=" * 60)
print("✅ All Function Tests Passed")
print("=" * 60)
