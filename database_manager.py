import sqlite3
import json
from dataclasses import asdict
from datetime import datetime
from typing import Optional, Dict, Any
from data_models import StockHealthCard

class DatabaseManager:
    """
    SQLite Database Manager for AI Stock Agent
    
    Purpose:
    - Store daily analysis snapshots for historical tracking
    - Detect status changes (PASS -> WATCHLIST, etc.)
    - Enable future Web SaaS features (score trends, alerts)
    """
    
    def __init__(self, db_path: str = "stocks.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database and create tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_analysis (
            date TEXT NOT NULL,
            symbol TEXT NOT NULL,
            price REAL,
            score INTEGER DEFAULT 0,
            status TEXT NOT NULL,
            report_summary TEXT,
            raw_data TEXT,
            PRIMARY KEY (date, symbol)
        )
        """)
        
        # Create index for faster status change queries
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_symbol_date 
        ON daily_analysis(symbol, date DESC)
        """)
        
        conn.commit()
        conn.close()
    
    def save_daily_snapshot(self, card: StockHealthCard, report_text: str, date: str = None):
        """
        Save daily analysis snapshot to database
        
        Args:
            card: StockHealthCard object from GARP analysis
            report_text: Formatted report string from format_stock_report()
            date: Analysis date (YYYY-MM-DD), defaults to today
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Convert StockHealthCard to dict, then to JSON
            card_dict = asdict(card)
            raw_data_json = json.dumps(card_dict, ensure_ascii=False)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            INSERT OR REPLACE INTO daily_analysis 
            (date, symbol, price, score, status, report_summary, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                date,
                card.symbol,
                card.price,
                0,  # Future: implement actual score calculation
                card.overall_status,
                report_text,
                raw_data_json
            ))
            
            conn.commit()
            conn.close()
            
            print(f"   ├─ 💾 已存檔: {card.symbol} @ {date}")
            
        except Exception as e:
            print(f"   ├─ ⚠️ 存檔失敗: {card.symbol} - {e}")
    
    def get_status_change(self, symbol: str, current_status: str, current_date: str = None) -> str:
        """
        Detect status changes by comparing current status with most recent historical record
        
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
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find the most recent record before current_date
            cursor.execute("""
            SELECT status FROM daily_analysis
            WHERE symbol = ? AND date < ?
            ORDER BY date DESC
            LIMIT 1
            """, (symbol, current_date))
            
            result = cursor.fetchone()
            conn.close()
            
            if result is None:
                return "NEW"
            
            old_status = result[0]
            
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
    
    def get_historical_data(self, symbol: str, limit: int = 30) -> list:
        """
        Get historical analysis data for a symbol (for future Web UI)
        
        Args:
            symbol: Stock symbol
            limit: Maximum number of records to return
        
        Returns:
            List of dicts containing historical data
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT date, price, status, raw_data
            FROM daily_analysis
            WHERE symbol = ?
            ORDER BY date DESC
            LIMIT ?
            """, (symbol, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            results = []
            for row in rows:
                try:
                    raw_data = json.loads(row[3]) if row[3] else {}
                except:
                    raw_data = {}
                
                results.append({
                    'date': row[0],
                    'price': row[1],
                    'status': row[2],
                    'raw_data': raw_data
                })
            
            return results
        
        except Exception as e:
            print(f"⚠️ 歷史資料查詢失敗: {symbol} - {e}")
            return []

if __name__ == "__main__":
    # Test database creation
    db = DatabaseManager()
    print("✅ Database initialized successfully!")
    print(f"Database path: {db.db_path}")
