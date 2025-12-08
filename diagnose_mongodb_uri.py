"""
MongoDB URI Diagnostic Tool
Checks if MONGODB_URI is correctly formatted and accessible
"""

import os
import re
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConfigurationError, ServerSelectionTimeoutError

print("=" * 60)
print("🔍 MongoDB URI 診斷工具")
print("=" * 60)

# Load environment variables
load_dotenv()
uri = os.getenv('MONGODB_URI')

print("\n1️⃣ 檢查環境變數...")
if not uri:
    print("❌ MONGODB_URI 未設定")
    print("💡 請在 .env 文件中添加 MONGODB_URI")
    exit(1)

print(f"✅ MONGODB_URI 已設定 ({len(uri)} 字元)")

# Check URI format
print("\n2️⃣ 檢查 URI 格式...")
if uri.startswith('mongodb+srv://'):
    print("✅ 使用 SRV 格式 (推薦)")
elif uri.startswith('mongodb://'):
    print("✅ 使用標準格式")
else:
    print("❌ URI 格式錯誤")
    print(f"   開頭: {uri[:20]}")
    print("   應為: mongodb+srv:// 或 mongodb://")
    exit(1)

# Extract components
print("\n3️⃣ 解析 URI 組件...")
try:
    # Basic regex to extract parts
    pattern = r'mongodb(?:\+srv)?://([^:]+):([^@]+)@([^/]+)/(.+?)(?:\?.*)?$'
    match = re.match(pattern, uri)
    
    if match:
        username, password, host, database = match.groups()
        print(f"   用戶名: {username}")
        print(f"   密碼: {'*' * len(password)} ({len(password)} chars)")
        print(f"   主機: {host}")
        print(f"   資料庫: {database}")
    else:
        print("⚠️ 無法解析 URI（可能包含特殊字元）")
        print(f"   URI 前50字元: {uri[:50]}...")
except Exception as e:
    print(f"⚠️ URI 解析失敗: {e}")

# Test connection
print("\n4️⃣ 測試連線...")
try:
    print("   嘗試連接...")
    client = MongoClient(
        uri,
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000
    )
    
    # Ping server
    client.admin.command('ping')
    print("✅ 連線成功！")
    
    # List databases
    dbs = client.list_database_names()
    print(f"\n   可用資料庫: {dbs}")
    
    # Check target database
    db = client['stock_agent']
    collections = db.list_collection_names()
    print(f"   stock_agent collections: {collections if collections else '(空)'}")
    
    client.close()
    
except ConfigurationError as e:
    print(f"❌ 配置錯誤: {e}")
    print("\n💡 可能原因:")
    print("   1. URI 格式錯誤")
    print("   2. 主機名稱錯誤")
    print("   3. dnspython 未安裝 (執行: pip install dnspython)")
    
except ServerSelectionTimeoutError as e:
    print(f"❌ 連線超時: {e}")
    print("\n💡 可能原因:")
    print("   1. 網路連線問題")
    print("   2. IP 白名單未設定 (MongoDB Atlas → Network Access)")
    print("   3. Cluster 暫停或刪除")
    
except Exception as e:
    print(f"❌ 連線失敗: {type(e).__name__}")
    print(f"   錯誤詳情: {e}")

print("\n" + "=" * 60)
print("診斷完成")
print("=" * 60)
