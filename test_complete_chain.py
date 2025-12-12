"""
Complete Chain Test - Sparkline Persistence
Tests the entire data flow from fetch to database save
"""
from market_data import fetch_and_analyze
from garp_strategy import GARPStrategy
from database_manager import DatabaseManager
from logger import logger
import logging

logging.basicConfig(level=logging.INFO)

def test_complete_chain(symbol):
    print(f"\n{'='*70}")
    print(f"🧪 COMPLETE CHAIN TEST FOR: {symbol}")
    print('='*70)
    
    # Step 1: Test fetch_and_analyze
    print(f"\n📥 Step 1: Testing fetch_and_analyze...")
    market_data = fetch_and_analyze(symbol)
    
    if not market_data:
        print(f"❌ FAIL: fetch_and_analyze returned None")
        return False
    
    fetch_sparkline = market_data.get('sparkline', [])
    print(f"✓ fetch_and_analyze returned data")
    print(f"  - Price: ${market_data.get('price')}")
    print(f"  - Sparkline length: {len(fetch_sparkline)}")
    
    if len(fetch_sparkline) == 0:
        print(f"❌ FAIL: Sparkline is empty from fetch_and_analyze")
        return False
    
    print(f"✅ PASS: fetch_and_analyze has sparkline ({len(fetch_sparkline)} days)")
    print(f"  - First 3: {fetch_sparkline[:3]}")
    
    # Step 2: Test GARPStrategy.analyze
    print(f"\n🔬 Step 2: Testing GARPStrategy.analyze...")
    strategy = GARPStrategy()
    card = strategy.analyze(symbol)
    
    if not card:
        print(f"❌ FAIL: GARPStrategy.analyze returned None")
        return False
    
    print(f"✓ GARPStrategy.analyze returned card")
    print(f"  - Symbol: {card.symbol}")
    print(f"  - Price: ${card.price}")
    print(f"  - Status: {card.overall_status}")
    print(f"  - Card.sparkline length: {len(card.sparkline)}")
    
    if len(card.sparkline) == 0:
        print(f"❌ FAIL: Card.sparkline is EMPTY!")
        print(f"  This means garp_strategy.py didn't transfer sparkline from market_data")
        return False
    
    print(f"✅ PASS: Card has sparkline ({len(card.sparkline)} days)")
    print(f"  - First 3: {card.sparkline[:3]}")
    
    # Step 3: Test DatabaseManager.save_daily_snapshot
    print(f"\n💾 Step 3: Testing DatabaseManager.save_daily_snapshot...")
    db = DatabaseManager()
    report = f"Test Report for {symbol}"
    
    try:
        db.save_daily_snapshot(card, report)
        print(f"✓ save_daily_snapshot executed without error")
    except Exception as e:
        print(f"❌ FAIL: save_daily_snapshot raised exception: {e}")
        return False
    
    # Step 4: Verify data in MongoDB
    print(f"\n🔍 Step 4: Verifying data in MongoDB...")
    saved_data = db.get_latest_stock_data(symbol)
    
    if not saved_data:
        print(f"❌ FAIL: No data found in MongoDB")
        return False
    
    raw_data = saved_data.get('raw_data', {})
    saved_sparkline = raw_data.get('sparkline', [])
    
    print(f"✓ Data retrieved from MongoDB")
    print(f"  - Saved sparkline length: {len(saved_sparkline)}")
    
    if len(saved_sparkline) == 0:
        print(f"❌ FAIL: Sparkline is EMPTY in MongoDB!")
        print(f"  This means save_daily_snapshot or _serialize_card has a bug")
        print(f"  Raw data keys: {list(raw_data.keys())}")
        return False
    
    print(f"✅ PASS: MongoDB has sparkline ({len(saved_sparkline)} days)")
    print(f"  - First 3: {saved_sparkline[:3]}")
    
    # Final comparison
    print(f"\n📊 COMPARISON:")
    print(f"  fetch_and_analyze: {len(fetch_sparkline)} days")
    print(f"  Card.sparkline:    {len(card.sparkline)} days")
    print(f"  MongoDB sparkline: {len(saved_sparkline)} days")
    
    if (len(fetch_sparkline) == len(card.sparkline) == len(saved_sparkline)):
        print(f"\n✅✅✅ ALL STEPS PASSED! Data flow is CORRECT for {symbol}")
        return True
    else:
        print(f"\n❌ MISMATCH detected in chain")
        return False

if __name__ == "__main__":
    # Test with a stock that currently has NO sparkline
    test_symbol = "GOOG"
    
    print("="*70)
    print(f"Running complete chain test for {test_symbol}")
    print("This will test: fetch → analyze → card → save → MongoDB")
    print("="*70)
    
    result = test_complete_chain(test_symbol)
    
    if result:
        print(f"\n🎉 SUCCESS: {test_symbol} now has sparkline in database")
        print(f"   Refresh your dashboard to see it!")
    else:
        print(f"\n💥 FAILURE: Issue identified in the chain")
        print(f"   Check the error messages above to see where it failed")
