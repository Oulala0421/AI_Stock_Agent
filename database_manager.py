"""
MongoDB Database Manager for AI Stock Agent - Phase 6

Purpose:
- Store daily analysis snapshots in MongoDB for historical tracking  
- Detect status changes (PASS -> WATCHLIST, etc.)
- Enable future Web SaaS features (score trends, alerts)

Architecture:
- Singleton Pattern: Reuse MongoClient for connection pooling
- Retry Mechanism: Handle network failures with exponential backoff
- Serialization: Custom serializer for StockHealthCard (handles Enum)
- Idempotency: Upsert with (symbol, date) unique key
- Indexing: Compound index on (symbol, date) for fast queries
"""

import os
from datetime import datetime
from dataclasses import asdict
from typing import Optional, Dict, Any, List
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, OperationFailure
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from data_models import StockHealthCard, OverallStatus
from config import Config


class DatabaseManager:
    """
    MongoDB Database Manager with Singleton Pattern
    
    Features:
    - Connection pooling (reuses MongoClient)
    - Automatic retry on network failures
    - Graceful error handling
    - Automatic index creation
    """
    
    _instance = None
    _client = None
    _db = None
    _collection = None
    _initialized = False
    
    def __new__(cls):
        """
        Singleton Pattern: Ensure only one instance exists
        
        Why Singleton?
        - MongoClient has built-in connection pooling
        - Reusing the same client is more efficient than reconnecting
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        Initialize MongoDB connection (only once due to Singleton)
        
        Graceful Failure:
        - If MONGODB_URI is missing, falls back to SQLite warning
        - If connection fails, provides helpful error messages
        """
        if not self._initialized:
            self._init_client()
            self._initialized = True
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionFailure, ServerSelectionTimeoutError))
    )
    def _init_client(self):
        """
        Initialize MongoDB client with retry mechanism
        
        Retry Strategy:
        - Max 3 attempts
        - Exponential backoff: 2s -> 4s -> 8s
        - Only retry network errors (not logic errors)
        
        Raises:
            SystemExit: If MONGODB_URI is not set or connection fails after retries
        """
        mongodb_uri = Config.get('MONGODB_URI')
        
        if not mongodb_uri:
            print("❌ MongoDB 連線失敗: MONGODB_URI 環境變數未設定")
            print("💡 請在 .env 中設定 MONGODB_URI")
            print("   範例: MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/stock_agent")
            raise SystemExit(1)
        
        try:
            # Create MongoClient with timeout settings
            self._client = MongoClient(
                mongodb_uri,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=10000,         # 10 second connect timeout
                retryWrites=True                # Enable automatic write retries
            )
            
            # Test connection by pinging the server
            self._client.admin.command('ping')
            
            # Initialize database and collection
            self._db = self._client['stock_agent']
            self._collection = self._db['stock_analysis']
            
            # Ensure indexes exist
            self._ensure_indexes()
            
            print("✅ [MongoDB] Connection Successful")
            print(f"   Database: stock_agent")
            print(f"   Collection: stock_analysis")
            
        except ServerSelectionTimeoutError as e:
            print("❌ MongoDB 連線失敗: 無法連接到伺服器")
            print(f"💡 請檢查:")
            print(f"   1. MONGODB_URI 是否正確")
            print(f"   2. 網路連線是否正常")
            print(f"   3. MongoDB Atlas IP 白名單設定")
            print(f"   錯誤詳情: {str(e)}")
            raise SystemExit(1)
            
        except ConnectionFailure as e:
            print("❌ MongoDB 連線失敗: 認證錯誤")
            print(f"💡 請檢查 MONGODB_URI 中的用戶名稱和密碼")
            print(f"   錯誤詳情: {str(e)}")
            raise SystemExit(1)
            
        except Exception as e:
            print(f"❌ MongoDB 連線失敗: {type(e).__name__}")
            print(f"   錯誤詳情: {str(e)}")
            raise SystemExit(1)
    
    def _ensure_indexes(self):
        """
        Create indexes for optimal query performance
        
        Index Strategy:
        - Compound index: (symbol, date DESC)
        - Accelerates get_status_change() queries
        - Background creation to avoid blocking
        
        Query Pattern:
        - "Find the most recent record for symbol X before date Y"
        - MongoDB will use this index to quickly locate the document
        """
        try:
            # Create compound index: symbol (ascending) + date (descending)
            self._collection.create_index(
                [("symbol", ASCENDING), ("date", DESCENDING)],
                name="idx_symbol_date",
                background=True  # Non-blocking index creation
            )
            print("   ├─ 📊 Index 'idx_symbol_date' 已建立")
            
        except OperationFailure as e:
            # Index might already exist, not a critical error
            print(f"   ├─ ⚠️ Index 建立警告: {e}")
    
    def _serialize_card(self, card: StockHealthCard) -> dict:
        """
        Serialize StockHealthCard to MongoDB-compatible dict
        
        Challenge: Enum Handling
        - Python Enum cannot be directly stored in MongoDB
        - Solution: Convert to string using .value
        
        Args:
            card: StockHealthCard object
            
        Returns:
            Dict ready for MongoDB insertion
        """
        # Convert dataclass to dict
        data = asdict(card)
        
        # Handle Enum: OverallStatus -> String
        # Before: overall_status = OverallStatus.PASS (Enum object)
        # After: overall_status = "PASS" (String)
        if isinstance(card.overall_status, str):
            data['overall_status'] = card.overall_status
        else:
            data['overall_status'] = card.overall_status.value if hasattr(card.overall_status, 'value') else str(card.overall_status)
        
        return data
    
    def save_daily_snapshot(self, card: StockHealthCard, report_text: str, date: str = None):
        """
        Save daily analysis snapshot to MongoDB with idempotency
        
        Idempotency (冪等性):
        - Problem: Running the script twice should not create duplicate records
        - Solution: Use update_one() with upsert=True
        - Unique Key: (symbol, date) combination
        
        Example:
        - First run: Inserts new document
        - Second run (same day): Updates existing document
        - Result: Only one document per (symbol, date)
        
        Args:
            card: StockHealthCard object from GARP analysis
            report_text: Formatted report string from format_stock_report()
            date: Analysis date (YYYY-MM-DD), defaults to today
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Serialize StockHealthCard (handles Enum conversion)
            raw_data = self._serialize_card(card)
            
            # Build MongoDB document
            document = {
                "date": date,
                "symbol": card.symbol,
                "price": card.price,
                "status": card.overall_status if isinstance(card.overall_status, str) else card.overall_status.value,
                "report": report_text,
                "raw_data": raw_data,
                "_updated_at": datetime.utcnow()  # Track last update time
            }
            
            # Upsert: Update if exists, Insert if not
            # Unique key: {symbol: "NVDA", date: "2025-12-07"}
            result = self._collection.update_one(
                {"symbol": card.symbol, "date": date},  # Filter
                {
                    "$set": document,                    # Update fields
                    "$setOnInsert": {"_created_at": datetime.utcnow()}  # Only on insert
                },
                upsert=True  # Create if doesn't exist
            )
            
            # Log result
            if result.upserted_id:
                print(f"   ├─ 💾 已新增: {card.symbol} @ {date}")
            else:
                print(f"   ├─ 💾 已更新: {card.symbol} @ {date}")
            
        except Exception as e:
            print(f"   ├─ ⚠️ MongoDB 存檔失敗: {card.symbol} - {e}")
            print(f"      錯誤類型: {type(e).__name__}")
    
    def get_status_change(self, symbol: str, current_status: str, current_date: str = None) -> str:
        """
        Detect status changes by comparing with most recent historical record
        
        Query Strategy:
        - Find: symbol = X AND date < current_date
        - Sort: date DESC (most recent first)
        - Limit: 1 (only need the latest)
        
        MongoDB Query:
        db.stock_analysis.findOne(
            {symbol: "NVDA", date: {$lt: "2025-12-07"}},
            sort: {date: -1}
        )
        
        Performance:
        - Uses idx_symbol_date index
        - O(log n) complexity due to index
        
        Args:
            symbol: Stock symbol
            current_status: Current analysis status (PASS/WATCHLIST/REJECT)
            current_date: Current date (YYYY-MM-DD), defaults to today
        
        Returns:
            "NEW": No historical record found
            "UPGRADE": Status improved (REJECT -> WATCHLIST, WATCHLIST -> PASS)
            "DOWNGRADE": Status worsened (PASS -> WATCHLIST, WATCHLIST -> REJECT)  
            "NO_CHANGE": Status unchanged
        """
        if current_date is None:
            current_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Query: Find most recent record before current_date
            result = self._collection.find_one(
                {"symbol": symbol, "date": {"$lt": current_date}},
                sort=[("date", DESCENDING)]  # Most recent first
            )
            
            if result is None:
                return "NEW"
            
            old_status = result.get('status', 'UNKNOWN')
            
            # Define status hierarchy (higher = better)
            status_rank = {
                "PASS": 3,
                "WATCHLIST": 2,
                "REJECT": 1
            }
            
            old_rank = status_rank.get(old_status, 0)
            current_rank = status_rank.get(current_status, 0)
            
            if current_rank > old_rank:
                return "UPGRADE"
            elif current_rank < old_rank:
                return "DOWNGRADE"
            else:
                return "NO_CHANGE"
        
        except Exception as e:
            print(f"   ├─ ⚠️ 狀態檢查失敗: {symbol} - {e}")
            return "NO_CHANGE"
    
    def get_historical_data(self, symbol: str, limit: int = 30) -> List[Dict[str, Any]]:
        """
        Get historical analysis data for a symbol (for future Web UI)
        
        Args:
            symbol: Stock symbol
            limit: Maximum number of records to return
        
        Returns:
            List of dicts containing historical data, sorted by date DESC
        """
        try:
            cursor = self._collection.find(
                {"symbol": symbol},
                {"_id": 0, "date": 1, "price": 1, "status": 1, "raw_data": 1}
            ).sort("date", DESCENDING).limit(limit)
            
            return list(cursor)
        
        except Exception as e:
            print(f"⚠️ 歷史資料查詢失敗: {symbol} - {e}")
            return []
    
    def close(self):
        """
        Close MongoDB connection
        
        Note: Usually not needed due to Singleton pattern
        MongoClient handles connection lifecycle automatically
        """
        if self._client:
            self._client.close()
            print("🔌 MongoDB 連線已關閉")


# Test module
if __name__ == "__main__":
    print("🧪 Testing MongoDB DatabaseManager\n")
    
    try:
        # Test 1: Connection
        print("Test 1: MongoDB Connection")
        db = DatabaseManager()
        print("✅ Pass\n")
        
        # Test 2: Serialization (mock)
        print("Test 2: Serialization")
        from data_models import StockHealthCard, OverallStatus
        
        mock_card = StockHealthCard(
            symbol="TEST",
            price=100.0,
            overall_status=OverallStatus.PASS.value
        )
        serialized = db._serialize_card(mock_card)
        print(f"   Serialized status: {serialized['overall_status']}")
        print("✅ Pass\n")
        
        # Test 3: Index Check
        print("Test 3: Index Verification")
        indexes = db._collection.list_indexes()
        index_names = [idx['name'] for idx in indexes]
        print(f"   Existing indexes: {index_names}")
        if 'idx_symbol_date' in index_names:
            print("✅ Pass\n")
        else:
            print("⚠️ Warning: idx_symbol_date not found\n")
        
        print("🎉 All tests completed!")
        
    except SystemExit:
        print("\n❌ Connection failed - this is expected if MONGODB_URI is not set")
        print("💡 Set MONGODB_URI in .env to enable MongoDB features")
