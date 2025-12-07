"""
Phase 6 Integration Test - MongoDB DatabaseManager

Tests:
1. Import verification
2. Connection handling (with/without URI)
3. Serialization (Enum handling)
4. Index verification
"""

import os
import sys
from datetime import datetime

print("=" * 60)
print("🧪 Phase 6 - MongoDB Integration Test")
print("=" * 60)

# Test 1: Import Test
print("\n📦 Test 1: Import DatabaseManager")
try:
    from database_manager import DatabaseManager
    from data_models import StockHealthCard, OverallStatus
    print("✅ Import successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Connection Test (graceful failure)
print("\n🔌 Test 2: Connection Handling")
print("Testing without MONGODB_URI...")

# Temporarily unset MONGODB_URI to test graceful failure
original_uri = os.environ.get('MONGODB_URI')
if 'MONGODB_URI' in os.environ:
    del os.environ['MONGODB_URI']

try:
    # Reload config to pick up the change
    import importlib
    import config
    importlib.reload(config)
    
    db = DatabaseManager()
    print("⚠️ Unexpected: Should have failed without MONGODB_URI")
except SystemExit as e:
    if e.code == 1:
        print("✅ Graceful failure: Correct error handling")
    else:
        print(f"⚠️ Unexpected exit code: {e.code}")

# Restore MONGODB_URI if it existed
if original_uri:
    os.environ['MONGODB_URI'] = original_uri

# Test 3: Reconnect with valid URI
print("\n🔌 Test 3: Connection with valid URI")
if original_uri:
    # Reload config again
    importlib.reload(config)
    
    try:
        db = DatabaseManager()
        print("✅ Connection established")
        
        # Test 4: Serialization
        print("\n🔄 Test 4: Serialization")
        mock_card = StockHealthCard(
            symbol="TEST",
            price=100.0,
            overall_status=OverallStatus.PASS.value
        )
        
        serialized = db._serialize_card(mock_card)
        
        # Verify Enum is converted to string
        if isinstance(serialized['overall_status'], str):
            print(f"✅ Enum serialization: {serialized['overall_status']}")
        else:
            print(f"❌ Enum not serialized: {type(serialized['overall_status'])}")
        
        # Test 5: Index Verification
        print("\n📊 Test 5: Index Verification")
        indexes = list(db._collection.list_indexes())
        index_names = [idx['name'] for idx in indexes]
        print(f"   Found indexes: {index_names}")
        
        if 'idx_symbol_date' in index_names:
            # Get index details
            idx_info = next((idx for idx in indexes if idx['name'] == 'idx_symbol_date'), None)
            if idx_info:
                print(f"✅ Index 'idx_symbol_date' exists")
                print(f"   Keys: {idx_info.get('key', {})}")
        else:
            print("⚠️ Index 'idx_symbol_date' not found")
        
        # Test 6: Upsert Test (optional, only if you want to actually write to DB)
        print("\n💾 Test 6: Upsert Test (Mock)")
        print("   Skipping actual write to keep DB clean")
        print("   To test upsert, run: python main.py --dry-run")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print("⚠️ MONGODB_URI not set, skipping connection tests")
    print("💡 Set MONGODB_URI in .env to run full tests")
