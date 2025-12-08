"""
Quick MongoDB Verification Script
Tests core functionality: serialization, upsert, and query
"""

from datetime import datetime
from database_manager import DatabaseManager
from data_models import StockHealthCard, OverallStatus

print("=" * 60)
print("🧪 MongoDB 功能驗證測試")
print("=" * 60)

# Initialize
print("\n1️⃣ 初始化連線...")
db = DatabaseManager()

# Test 1: Serialization
print("\n2️⃣ 測試序列化...")
test_card = StockHealthCard(
    symbol="TEST_MONGO",
    price=100.5,
    overall_status=OverallStatus.PASS.value
)
test_card.solvency_check = {
    "debt_to_equity": 0.5,
    "current_ratio": 2.0,
    "is_passing": True,
    "tags": ["Low Debt"]
}

print(f"   Symbol: {test_card.symbol}")
print(f"   Status: {test_card.overall_status}")

# Test 2: Upsert (First Insert)
print("\n3️⃣ 測試 Upsert (首次插入)...")
test_report = "📊 TEST_MONGO Analysis\nStatus: PASS\nThis is a test report."
db.save_daily_snapshot(test_card, test_report, date="2025-12-07")

# Test 3: Upsert (Update - Idempotency)
print("\n4️⃣ 測試 Upsert (重複插入 - 冪等性)...")
test_card.price = 101.0  # Update price
db.save_daily_snapshot(test_card, test_report, date="2025-12-07")

# Test 4: Query - Status Change
print("\n5️⃣ 測試狀態變化檢測...")
# Insert historical data
test_card.overall_status = OverallStatus.WATCHLIST.value
db.save_daily_snapshot(test_card, test_report, date="2025-12-06")

# Check status change
status_change = db.get_status_change("TEST_MONGO", OverallStatus.PASS.value, "2025-12-07")
print(f"   狀態變化: {status_change}")
if status_change == "UPGRADE":
    print("   ✅ 正確檢測到 WATCHLIST → PASS (升級)")
else:
    print(f"   ⚠️ 預期 UPGRADE，實際 {status_change}")

# Test 5: Historical Data Query
print("\n6️⃣ 測試歷史資料查詢...")
history = db.get_historical_data("TEST_MONGO", limit=5)
print(f"   查詢到 {len(history)} 筆記錄")
if history:
    latest = history[0]
    print(f"   最新記錄: {latest.get('date')} - {latest.get('status')}")

# Test 6: Verify in Database
print("\n7️⃣ 驗證資料庫記錄...")
count = db._collection.count_documents({"symbol": "TEST_MONGO"})
print(f"   TEST_MONGO 總記錄數: {count}")
if count == 2:
    print("   ✅ 冪等性驗證通過 (2筆不同日期)")
else:
    print(f"   ⚠️ 預期 2 筆，實際 {count} 筆")

print("\n" + "=" * 60)
print("✅ MongoDB 功能測試完成")
print("=" * 60)
print("\n💡 下一步：")
print("   - 登入 MongoDB Atlas 查看資料")
print("   - 執行: python main.py --dry-run")
print("   - 設定 GitHub Secrets: MONGODB_URI")
