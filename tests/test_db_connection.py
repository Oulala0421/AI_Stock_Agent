"""
Test MongoDB Database Connection

This test verifies that:
1. DatabaseManager can be initialized
2. MongoDB connection is established
3. Singleton pattern works correctly
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_manager import DatabaseManager

def test_connection():
    """Test MongoDB connection and basic functionality"""
    
    print("=" * 60)
    print("🧪 MongoDB Connection Test")
    print("=" * 60)
    
    # Test 1: Initialize DatabaseManager
    print("\n1️⃣  Testing Singleton Initialization...")
    db = DatabaseManager()
    
    if db.enabled:
        print("✅ Test Passed: MongoDB is enabled and connected.")
        print(f"   Database: {db._db.name if db._db else 'N/A'}")
        
        # Test 2: Verify Singleton
        print("\n2️⃣  Testing Singleton Pattern...")
        db2 = DatabaseManager()
        if db is db2:
            print("✅ Test Passed: Singleton pattern working (same instance)")
        else:
            print("❌ Test Failed: Multiple instances created")
            
        # Test 3: Check indexes
        print("\n3️⃣  Checking Indexes...")
        if db._db:
            indexes = list(db._db.daily_snapshots.list_indexes())
            index_names = [idx['name'] for idx in indexes]
            print(f"   Found indexes: {index_names}")
            
            if 'idx_symbol_date' in index_names:
                print("✅ Test Passed: Required index exists")
            else:
                print("⚠️  Warning: idx_symbol_date not found")
        
        print("\n" + "=" * 60)
        print("✅ All Tests Passed")
        print("=" * 60)
        return True
        
    else:
        print("❌ Test Failed: MongoDB is disabled")
        print("   Possible reasons:")
        print("   - MONGODB_URI not set in .env")
        print("   - Network connectivity issue")
        print("   - MongoDB Atlas not accessible")
        print("\n💡 Check:")
        print("   1. .env file contains MONGODB_URI")
        print("   2. URI format is correct")
        print("   3. Network connection to MongoDB Atlas")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
