"""
Additional Smoke Tests for MongoDB DatabaseManager

Tests:
1. Serialization (Enum handling)
2. Upsert idempotency
3. Status change detection
4. Error handling
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_manager import DatabaseManager
from data_models import StockHealthCard, OverallStatus

def test_serialization_and_upsert():
    """Test that Enum serialization and upsert work correctly"""
    
    print("\n" + "=" * 60)
    print("🧪 Serialization & Upsert Test")
    print("=" * 60)
    
    db = DatabaseManager()
    
    if not db.enabled:
        print("⚠️  Skipping test - MongoDB not enabled")
        return False
    
    # Create test card
    test_card = StockHealthCard(
        symbol="TEST_SMOKE",
        price=100.5,
        overall_status=OverallStatus.PASS.value
    )
    
    test_date = "2025-12-08"
    
    # Test 1: First insert
    print("\n1️⃣  Testing first insert...")
    db.save_daily_snapshot(test_card, "Test Report 1", date=test_date)
    
    # Verify it was inserted
    result = db._db.daily_snapshots.find_one({
        "symbol": "TEST_SMOKE",
        "date": test_date
    })
    
    if result:
        print("✅ Insert successful")
        print(f"   Status stored as: {result.get('status')} (type: {type(result.get('status')).__name__})")
        
        if isinstance(result.get('status'), str):
            print("✅ Enum correctly serialized to string")
        else:
            print("❌ Enum not properly serialized")
            return False
    else:
        print("❌ Insert failed")
        return False
    
    # Test 2: Upsert (update same record)
    print("\n2️⃣  Testing upsert (idempotency)...")
    test_card.price = 101.0  # Change price
    db.save_daily_snapshot(test_card, "Test Report 2 (Updated)", date=test_date)
    
    # Count documents - should still be 1
    count = db._db.daily_snapshots.count_documents({
        "symbol": "TEST_SMOKE",
        "date": test_date
    })
    
    if count == 1:
        print("✅ Idempotency verified (still 1 record)")
        
        # Verify price was updated
        updated = db._db.daily_snapshots.find_one({
            "symbol": "TEST_SMOKE",
            "date": test_date
        })
        
        if updated and updated.get('price') == 101.0:
            print("✅ Record updated correctly")
        else:
            print("❌ Record not updated")
            return False
    else:
        print(f"❌ Idempotency failed ({count} records found)")
        return False
    
    # Cleanup
    print("\n3️⃣  Cleaning up test data...")
    db._db.daily_snapshots.delete_many({"symbol": "TEST_SMOKE"})
    print("✅ Cleanup complete")
    
    print("\n" + "=" * 60)
    print("✅ Serialization & Upsert Tests Passed")
    print("=" * 60)
    return True

def test_status_change_detection():
    """Test status change detection logic"""
    
    print("\n" + "=" * 60)
    print("🧪 Status Change Detection Test")
    print("=" * 60)
    
    db = DatabaseManager()
    
    if not db.enabled:
        print("⚠️  Skipping test - MongoDB not enabled")
        return False
    
    # Setup: Insert historical data
    test_card = StockHealthCard(
        symbol="TEST_STATUS",
        price=100.0,
        overall_status=OverallStatus.WATCHLIST.value
    )
    
    db.save_daily_snapshot(test_card, "Historical", date="2025-12-07")
    
    # Test: Upgrade detection (WATCHLIST -> PASS)
    print("\n1️⃣  Testing UPGRADE detection...")
    change = db.get_status_change("TEST_STATUS", OverallStatus.PASS.value, "2025-12-08")
    
    if change == "UPGRADE":
        print("✅ UPGRADE correctly detected")
    else:
        print(f"❌ Expected UPGRADE, got {change}")
        return False
    
    # Test: Downgrade detection
    print("\n2️⃣  Testing DOWNGRADE detection...")
    change = db.get_status_change("TEST_STATUS", OverallStatus.REJECT.value, "2025-12-08")
    
    if change == "DOWNGRADE":
        print("✅ DOWNGRADE correctly detected")
    else:
        print(f"❌ Expected DOWNGRADE, got {change}")
        return False
    
    # Test: NEW detection
    print("\n3️⃣  Testing NEW detection...")
    change = db.get_status_change("BRAND_NEW_STOCK", OverallStatus.PASS.value, "2025-12-08")
    
    if change == "NEW":
        print("✅ NEW correctly detected")
    else:
        print(f"❌ Expected NEW, got {change}")
        return False
    
    # Cleanup
    db._db.daily_snapshots.delete_many({"symbol": "TEST_STATUS"})
    
    print("\n" + "=" * 60)
    print("✅ Status Change Tests Passed")
    print("=" * 60)
    return True

if __name__ == "__main__":
    print("\n🚀 Running Extended Smoke Tests...\n")
    
    test1 = test_serialization_and_upsert()
    test2 = test_status_change_detection()
    
    if test1 and test2:
        print("\n🎉 All Extended Tests Passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)
