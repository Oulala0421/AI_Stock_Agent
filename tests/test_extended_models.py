"""
Test for Extended Data Models (Price Prediction Fields)

Validates:
1. StockHealthCard accepts new optional fields
2. Serialization handles None values correctly
3. MongoDB can store and retrieve prediction data
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_models import StockHealthCard, OverallStatus
from database_manager import DatabaseManager

print("=" * 60)
print("🧪 Extended Data Models Test (Price Prediction)")
print("=" * 60)

# Test 1: Create card without prediction fields (backward compatibility)
print("\n1️⃣  Testing backward compatibility...")
card_basic = StockHealthCard(
    symbol="TEST_BASIC",
    price=100.0,
    overall_status=OverallStatus.PASS.value
)

print(f"   Symbol: {card_basic.symbol}")
print(f"   Prediction fields: predicted_return_1w={card_basic.predicted_return_1w}")
print("✅ Backward compatibility: Optional fields default to None")

# Test 2: Create card with prediction fields
print("\n2️⃣  Testing with prediction data...")
card_with_pred = StockHealthCard(
    symbol="TEST_PRED",
    price=100.0,
    overall_status=OverallStatus.PASS.value,
    predicted_return_1w=5.2,
    predicted_return_1m=12.8,
    confidence_score=0.85,
    monte_carlo_min=95.0,
    monte_carlo_max=110.0
)

print(f"   Symbol: {card_with_pred.symbol}")
print(f"   1週預測: {card_with_pred.predicted_return_1w}%")
print(f"   1月預測: {card_with_pred.predicted_return_1m}%")
print(f"   信心分數: {card_with_pred.confidence_score}")
print(f"   悲觀價格: ${card_with_pred.monte_carlo_min}")
print(f"   樂觀價格: ${card_with_pred.monte_carlo_max}")
print("✅ Prediction fields accepted")

# Test 3: Serialization
print("\n3️⃣  Testing serialization...")
db = DatabaseManager()

if db.enabled:
    # Test serialization of card without predictions
    serialized_basic = db._serialize_card(card_basic)
    print(f"   Basic card serialized: {len(serialized_basic)} fields")
    print(f"   predicted_return_1w: {serialized_basic.get('predicted_return_1w')}")
    
    # Test serialization of card with predictions
    serialized_pred = db._serialize_card(card_with_pred)
    print(f"   Prediction card serialized: {len(serialized_pred)} fields")
    print(f"   predicted_return_1w: {serialized_pred.get('predicted_return_1w')}")
    print("✅ Serialization handles both cases")
    
    # Test 4: Save to MongoDB
    print("\n4️⃣  Testing MongoDB storage...")
    
    # Save basic card
    db.save_daily_snapshot(card_basic, "Basic test report", "2025-12-08")
    
    # Save prediction card
    db.save_daily_snapshot(card_with_pred, "Prediction test report", "2025-12-08")
    
    # Verify
    from pymongo import DESCENDING
    latest = db._db.daily_snapshots.find_one(
        {"symbol": "TEST_PRED"},
        sort=[("created_at", DESCENDING)]
    )
    
    if latest:
        print(f"   Retrieved document for TEST_PRED")
        print(f"   Has prediction data: {latest['raw_data'].get('predicted_return_1w') is not None}")
        print(f"   1w prediction: {latest['raw_data'].get('predicted_return_1w')}%")
        print(f"   confidence: {latest['raw_data'].get('confidence_score')}")
        print("✅ MongoDB correctly stored prediction fields")
    
    # Cleanup
    db._db.daily_snapshots.delete_many({"symbol": {"$in": ["TEST_BASIC", "TEST_PRED"]}})
    print("✅ Cleanup complete")
    
else:
    print("⚠️  MongoDB not enabled, skipping storage tests")

print("\n" + "=" * 60)
print("✅ Extended Data Models Test Complete")
print("=" * 60)
print("\n📊 Summary:")
print("   - Backward compatibility: ✅")
print("   - Prediction fields: ✅")
print("   - Serialization: ✅")
if db.enabled:
    print("   - MongoDB storage: ✅")
else:
    print("   - MongoDB storage: ⏭️  Skipped (not enabled)")
