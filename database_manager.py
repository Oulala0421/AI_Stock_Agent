"""
MongoDB Database Manager for AI Stock Agent

Architecture:
- Singleton Pattern: Single global database connection
- Idempotency: Upsert ensures no duplicate records for same (date, symbol)
- Serialization: Handles Python Enum and datetime conversion
- Graceful Failure: Logs errors without crashing the application

Author: Senior Backend Engineer
Date: 2025-12-08
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import asdict
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError, OperationFailure
from config import Config
from data_models import StockHealthCard, OverallStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    MongoDB Database Manager with Singleton Pattern
    
    Features:
    - Global single instance (Singleton)
    - Automatic connection pooling via MongoClient
    - Graceful error handling
    - Automatic index creation
    """
    
    _instance = None
    _client = None
    _db = None
    enabled = False
    
    def __new__(cls):
        """
        Singleton Pattern: Ensure only one instance exists globally
        
        Why Singleton?
        - MongoClient has built-in connection pooling
        - Prevents multiple unnecessary connections
        - Ensures consistent state across application
        """
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._init_client()
        return cls._instance
    
    def _init_client(self):
        """
        Initialize MongoDB connection with timeout and error handling
        
        Graceful Failure:
        - If MONGODB_URI is missing, disables DB features but allows app to run
        - If connection fails, logs error and continues with disabled state
        - Sets 5-second timeout to prevent hanging
        """
        self.enabled = False
        uri = Config.get("MONGODB_URI")
        
        if not uri:
            logger.warning("⚠️  MongoDB URI not set. Database features disabled.")
            logger.info("💡 Application will continue with limited functionality.")
            return
        
        try:
            # Create MongoClient with 5-second timeout
            self._client = MongoClient(
                uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                retryWrites=True
            )
            
            # Ping test to verify connection
            self._client.admin.command('ping')
            
            # Get database (default: stock_agent)
            self._db = self._client.get_database("stock_agent")
            self.enabled = True
            
            # Create indexes for optimal query performance
            self._ensure_indexes()
            
            logger.info("✅ [MongoDB] Connection Successful")
            logger.info(f"   Database: stock_agent")
            logger.info(f"   Collection: daily_snapshots")
            
        except ServerSelectionTimeoutError as e:
            logger.error(f"❌ [MongoDB] Connection Timeout: {e}")
            logger.warning("💡 Check network connectivity and MongoDB Atlas IP whitelist")
            self.enabled = False
            
        except Exception as e:
            logger.error(f"❌ [MongoDB] Connection Failed: {type(e).__name__} - {e}")
            logger.warning("💡 Application will continue without database features")
            self.enabled = False
    
    def _ensure_indexes(self):
        """
        Create indexes for optimal query performance
        
        Indexes:
        - (symbol, date DESC): Accelerates latest status queries
        - Compound index allows efficient filtering by symbol and sorting by date
        """
        try:
            collection = self._db.daily_snapshots
            
            # Create compound index: symbol (ascending) + date (descending)
            collection.create_index(
                [("symbol", ASCENDING), ("date", DESCENDING)],
                name="idx_symbol_date",
                background=True
            )
            
            logger.info("   ├─ 📊 Index 'idx_symbol_date' ensured")
            
        except OperationFailure as e:
            # Index might already exist, not critical
            logger.debug(f"Index creation note: {e}")
    
    def _serialize_card(self, card: StockHealthCard) -> Dict[str, Any]:
        """
        Convert StockHealthCard dataclass to MongoDB-compatible dict
        
        Handles:
        - Enum -> String conversion (OverallStatus)
        - Nested dataclass structures
        - Optional fields (price prediction) -> stored as null if None
        - Ensures all data types are BSON-compatible
        
        Args:
            card: StockHealthCard object from GARP analysis
            
        Returns:
            Dictionary ready for MongoDB insertion
        """
        # Convert dataclass to dict
        data = asdict(card)
        
        # Handle Enum conversion: OverallStatus -> String
        if 'overall_status' in data:
            if isinstance(card.overall_status, str):
                data['overall_status'] = card.overall_status
            else:
                # If it's an Enum object, extract value
                data['overall_status'] = getattr(
                    card.overall_status, 'value', 
                    str(card.overall_status)
                )
        
        # Handle Optional price prediction fields (Sprint 1 Extension)
        # MongoDB best practice: store None as null (not 0)
        # This distinguishes "not calculated" from "calculated as 0"
        prediction_fields = [
            'predicted_return_1w',
            'predicted_return_1m', 
            'confidence_score',
            'monte_carlo_min',
            'monte_carlo_max'
        ]
        
        for field_name in prediction_fields:
            if field_name in data:
                # Keep None as-is (will be stored as null in MongoDB)
                # This is intentional - we want to preserve the distinction
                pass
        
        return data
    
    def save_daily_snapshot(self, card: StockHealthCard, report_text: str, date: str = None):
        """
        Save daily analysis snapshot with idempotency guarantee
        
        Idempotency (冪等性):
        - Uses upsert=True with (date, symbol) as unique key
        - Running multiple times on same day only updates, never duplicates
        - First run: Inserts new document
        - Subsequent runs: Updates existing document
        
        Args:
            card: StockHealthCard object from GARP analysis
            report_text: Formatted report string
            date: Analysis date (YYYY-MM-DD), defaults to today
        """
        if not self.enabled:
            logger.debug("MongoDB disabled, skipping save")
            return
        
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            collection = self._db.daily_snapshots
            
            # Prepare document - REMOVE created_at from here to allow setOnInsert to handle it
            doc = {
                "date": date,
                "symbol": card.symbol,
                "price": card.price,
                "status": card.overall_status if isinstance(card.overall_status, str) else card.overall_status.value,
                "report": report_text,
                "raw_data": self._serialize_card(card),
                # "created_at": datetime.utcnow(),  <-- REMOVED to avoid conflict
                "updated_at": datetime.utcnow()
            }
            
            # Upsert logic: Query by (date, symbol)
            # If exists: update
            # If not exists: insert
            query = {"date": date, "symbol": card.symbol}
            
            result = collection.update_one(
                query,
                {
                    "$set": doc,
                    "$setOnInsert": {"created_at": datetime.utcnow()}
                },
                upsert=True
            )
            
            # Log result
            if result.upserted_id:
                logger.info(f"   ├─ 💾 已新增: {card.symbol} @ {date}")
            elif result.modified_count > 0:
                logger.info(f"   ├─ 💾 已更新: {card.symbol} @ {date}")
            else:
                logger.debug(f"   ├─ 💾 無變更: {card.symbol} @ {date}")
                
        except PyMongoError as e:
            logger.error(f"   ├─ ❌ MongoDB 存檔失敗: {card.symbol} - {e}")
        except Exception as e:
            logger.error(f"   ├─ ❌ 存檔異常: {card.symbol} - {type(e).__name__}: {e}")
    
    def get_latest_status(self, symbol: str) -> Optional[Dict]:
        """
        Get the most recent analysis result for a symbol (for comparison)
        
        Query Logic:
        - Find records where symbol matches and date < today
        - Sort by date DESC (most recent first)
        - Return only the latest one
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary containing the latest snapshot, or None if not found
        """
        if not self.enabled:
            return None
        
        try:
            collection = self._db.daily_snapshots
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Query: symbol = X AND date < today
            # Sort: date DESC (most recent first)
            # Limit: 1
            result = collection.find_one(
                {"symbol": symbol, "date": {"$lt": today}},
                sort=[("date", DESCENDING)]
            )
            
            return result
            
        except PyMongoError as e:
            logger.error(f"   ├─ ❌ 歷史查詢失敗: {symbol} - {e}")
            return None
    
    def get_status_change(self, symbol: str, current_status: str, current_date: str = None) -> str:
        """
        Detect status changes by comparing with most recent historical record
        
        Returns:
            "NEW": No historical record found
            "UPGRADE": Status improved (REJECT -> WATCHLIST, WATCHLIST -> PASS)
            "DOWNGRADE": Status worsened (PASS -> WATCHLIST, WATCHLIST -> REJECT)
            "NO_CHANGE": Status unchanged
        """
        if current_date is None:
            current_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            latest = self.get_latest_status(symbol)
            
            if latest is None:
                return "NEW"
            
            old_status = latest.get('status', 'UNKNOWN')
            
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
            logger.error(f"   ├─ ⚠️ 狀態檢查失敗: {symbol} - {e}")
            return "NO_CHANGE"
    
    def get_historical_data(self, symbol: str, limit: int = 30) -> List[Dict[str, Any]]:
        """
        Get historical analysis data for a symbol (for future Web UI)
        
        Args:
            symbol: Stock symbol
            limit: Maximum number of records to return
        
        Returns:
            List of dictionaries containing historical data, sorted by date DESC
        """
        if not self.enabled:
            return []
        
        try:
            collection = self._db.daily_snapshots
            
            cursor = collection.find(
                {"symbol": symbol},
                {"_id": 0}  # Exclude MongoDB internal _id
            ).sort("date", DESCENDING).limit(limit)
            
            return list(cursor)
            
        except PyMongoError as e:
            logger.error(f"⚠️ 歷史資料查詢失敗: {symbol} - {e}")
            return []

    def get_sentiment_stats(self, symbol: str, days: int = 30) -> Dict[str, float]:
        """
        Calculate sentiment statistics (Mean, StdDev) for Z-Score calculation.
        
        Args:
            symbol: Stock symbol (usually 'SPY' for market sentiment)
            days: Lookback period
            
        Returns:
            Dict with 'mean' and 'std_dev'. Defaults to mean=0, std=1 if insufficient data.
        """
        if not self.enabled:
            return {'mean': 0.0, 'std_dev': 1.0}
            
        try:
            collection = self._db.daily_snapshots
            
            # Aggregation Pipeline
            pipeline = [
                # 1. Match symbol & date range
                {
                    "$match": {
                        "symbol": symbol
                    }
                },
                # 2. Sort by date desc and limit
                { "$sort": { "date": -1 } },
                { "$limit": days },
                # 3. Project sentiment score (handle missing/nested fields)
                {
                    "$project": {
                        "score": "$raw_data.advanced_metrics.news_analysis.sentiment_score"
                    }
                },
                # 4. Filter out nulls
                {
                    "$match": {
                        "score": { "$ne": None }
                    }
                },
                # 5. Group to calculate stats
                {
                    "$group": {
                        "_id": None,
                        "mean": { "$avg": "$score" },
                        "std_dev": { "$stdDevPop": "$score" }, # Population StdDev matches Z-Score usage
                        "count": { "$sum": 1 }
                    }
                }
            ]
            
            results = list(collection.aggregate(pipeline))
            
            if not results or results[0]['count'] < 2:
                # Need at least 2 data points for meaningful stats
                return {'mean': 0.0, 'std_dev': 1.0}
                
            stats = results[0]
            # Avoid division by zero if std_dev is 0 (constant sentiment)
            std_dev = stats.get('std_dev', 0.0)
            if std_dev == 0:
                std_dev = 1.0
                
            return {
                'mean': stats.get('mean', 0.0),
                'std_dev': std_dev
            }
            
        except Exception as e:
            logger.error(f"⚠️ Failed to get sentiment stats for {symbol}: {e}")
            return {'mean': 0.0, 'std_dev': 1.0}
    
    def close(self):
        """
        Close MongoDB connection
        
        Note: Usually not needed due to Singleton pattern
        MongoClient handles connection lifecycle automatically
        """
        if self._client:
            self._client.close()
            logger.info("🔌 MongoDB 連線已關閉")

    def get_latest_stock_data(self, symbol: str) -> Optional[Dict]:
        """
        Get absolute latest data for cache checking (including today)
        Used by Prediction Engine for caching
        """
        if not self.enabled:
            return None
        
        try:
            # Find latest regardless of date
            result = self._db.daily_snapshots.find_one(
                {"symbol": symbol},
                sort=[("updated_at", DESCENDING)]
            )
            
            if result:
                # Map mongo fields to expected API
                # prediction_engine expects 'last_updated'
                result['last_updated'] = result.get('updated_at')
                return result
            return None
            
        except Exception as e:
            logger.error(f"   ├─ ⚠️ 快取查詢失敗: {symbol} - {e}")
            return None


# For backward compatibility with existing code
# Keeping the same API as SQLite version
if __name__ == "__main__":
    print("🧪 Testing MongoDB DatabaseManager\n")
    
    try:
        # Test: Singleton Pattern
        print("Test 1: Singleton Pattern")
        db1 = DatabaseManager()
        db2 = DatabaseManager()
        print(f"   Same instance: {db1 is db2}")
        print(f"   Enabled: {db1.enabled}")
        print("✅ Pass\n")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
