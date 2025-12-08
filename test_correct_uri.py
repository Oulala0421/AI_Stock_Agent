"""
Test MongoDB connection with correct URI
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Construct correct URI
password = "kiWKyFXU9LpCYGY5"
uri = f"mongodb+srv://admin:{password}@cluster0.ktj8ev1.mongodb.net/stock_agent?retryWrites=true&w=majority"

print("🔌 測試 MongoDB 連線...")
print(f"Cluster: cluster0.ktj8ev1.mongodb.net")
print(f"Database: stock_agent\n")

try:
    client = MongoClient(uri, serverSelectionTimeoutMS=10000)
    client.admin.command('ping')
    
    print("✅ MongoDB 連線成功！\n")
    
    # List databases
    dbs = client.list_database_names()
    print(f"可用資料庫: {dbs}")
    
    # Access stock_agent database
    db = client['stock_agent']
    collections = db.list_collection_names()
    print(f"stock_agent collections: {collections if collections else '(空 - 將自動創建)'}\n")
    
    # Test creating collection
    if 'stock_analysis' not in collections:
        print("📝 創建 stock_analysis collection...")
        db.create_collection('stock_analysis')
        print("✅ Collection 創建成功")
    
    client.close()
    print("\n✅ 所有連線測試通過！")
    
except Exception as e:
    print(f"❌ 連線失敗: {type(e).__name__}")
    print(f"   {str(e)}")
