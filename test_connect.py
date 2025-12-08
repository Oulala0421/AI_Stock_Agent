"""
Simple MongoDB Connection Test
Just tries to connect and reports success/failure
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
uri = os.getenv('MONGODB_URI')

print("🔌 測試 MongoDB 連線...")
print(f"URI 長度: {len(uri) if uri else 0} 字元")
print(f"URI 開頭: {uri[:30] if uri else 'N/A'}...")

if not uri:
    print("❌ MONGODB_URI 未設定")
    exit(1)

try:
    client =MongoClient(uri, serverSelectionTimeoutMS=10000)
    client.admin.command('ping')
    print("\n✅ MongoDB 連線成功！")
    
    # List databases
    dbs = client.list_database_names()
    print(f"   資料庫: {dbs}")
    
    client.close()
    
except Exception as e:
    print(f"\n❌ 連線失敗: {type(e).__name__}")
    print(f"   {str(e)}")
    print("\n💡 請檢查:")
    print("   1. MONGODB_URI 是否完整（應該是完整的連線字串）")
    print("   2. MongoDB Atlas IP 白名單設定")
    print("   3. 用戶名密碼是否正確")
