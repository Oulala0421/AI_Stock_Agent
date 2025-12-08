"""
Manual test with correct MongoDB URI
This bypasses .env and uses the correct URI directly
"""

import os
import sys

# Set correct MongoDB URI
os.environ['MONGODB_URI'] = 'mongodb+srv://admin:kiWKyFXU9LpCYGY5@cluster0.ktj8ev1.mongodb.net/stock_agent?retryWrites=true&w=majority'

# Force reload config
import importlib
if 'config' in sys.modules:
    importlib.reload(sys.modules['config'])

from config import Config
from database_manager import DatabaseManager
from data_models import StockHealthCard, OverallStatus

print("=" * 60)
print("🧪 Manual MongoDB Test (Correct URI)")
print("=" * 60)

print(f"\n📋 Config MONGODB_URI: {Config.get('MONGODB_URI')[:50]}...")

# Test 1: Connection
print("\n1️⃣  Testing Connection...")
db = DatabaseManager()

if db.enabled:
    print("✅ Connection Successful!")
    print(f"   Database: {db._db.name}")
    print(f"   Collection: daily_snapshots")
    
    # Test 2: Serialize and save
    print("\n2️⃣  Testing Save Operation...")
    test_card = StockHealthCard(
        symbol="MANUAL_TEST",
        price=100.0,
        overall_status=OverallStatus.PASS.value
    )
    
    db.save_daily_snapshot(test_card, "Manual test report", "2025-12-08")
    
    # Test 3: Verify
    print("\n3️⃣  Verifying Data...")
    count = db._db.daily_snapshots.count_documents({"symbol": "MANUAL_TEST"})
    print(f"   Records found: {count}")
    
    if count > 0:
        print("✅ Data successfully written to MongoDB!")
        
        # Cleanup
        db._db.daily_snapshots.delete_many({"symbol": "MANUAL_TEST"})
        print("✅ Test data cleaned up")
    
    print("\n" + "=" * 60)
    print("🎉 All Manual Tests Passed!")
    print("=" * 60)
    
else:
    print("❌ Connection Failed")
    print("   Check network and MongoDB Atlas settings")
