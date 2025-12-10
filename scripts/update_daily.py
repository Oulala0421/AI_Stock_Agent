"""
Daily Data Update Script
------------------------
Updates the MongoDB cache with fresh market data and GARP analysis.
Schedule this to run daily (e.g., via Windows Task Scheduler or Cron).

Functionality:
1. Reads stock list from config.yaml
2. runs GARP Analysis for each stock
3. Saves snapshot to MongoDB (Upsert)
"""

import os
import sys

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from garp_strategy import GARPStrategy
from database_manager import DatabaseManager
from logger import logger

def main():
    logger.info("🚀 Starting Daily Data Update...")
    
    # 1. Initialize DB
    db = DatabaseManager()
    if not db.enabled:
        logger.error("❌ Database not configured. Aborting update.")
        return

    # 2. Get Targets
    etfs = Config.get('MARKET', {}).get('etf_watch_list', [])
    stocks = Config.get('MARKET', {}).get('public_showcase_list', [])
    targets = list(set(etfs + stocks)) # Unique list
    
    logger.info(f"📋 Targets: {targets}")
    
    # 3. Process Each
    strategy = GARPStrategy()
    
    success_count = 0
    
    for symbol in targets:
        try:
            logger.info(f"🔄 Processing {symbol}...")
            
            # Analyze (Fetches Live Data)
            # FORCE live fetch is implicit in analyze() unless we modify it to check cache first.
            # But here we WANT fresh data, so analyze() is correct as it calls fetch_and_analyze().
            # Note: analyze() falls back to cache if live fails. 
            # To ensure we *update* the cache, we need fetch_and_analyze to work.
            # If fetch_and_analyze fails, we just re-save the old cache, which is fine (idempotent).
            
            card = strategy.analyze(symbol)
            
            if "Data Fetch Failed" in card.red_flags:
                logger.warning(f"⚠️ Failed to fetch fresh data for {symbol}. Skipping save.")
                continue
            
            # Generate Report Summary (Simple version)
            report = f"Date: {card.generated_at}\nStatus: {card.overall_status}\nPrice: {card.price}\nReason: {card.overall_reason}"
            
            # Save to DB
            db.save_daily_snapshot(card, report)
            success_count += 1
            
        except Exception as e:
            logger.error(f"❌ Error processing {symbol}: {e}")

    logger.info(f"✅ Update Complete. Successfully updated {success_count}/{len(targets)} stocks.")

if __name__ == "__main__":
    main()
