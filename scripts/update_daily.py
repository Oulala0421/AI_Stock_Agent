"""
Daily Data Update Script (Optimized)
------------------------------------
Updates the MongoDB cache with fresh market data and GARP analysis.
Schedule this to run daily (e.g., via Windows Task Scheduler or Cron).

Optimization: Incremental Sparkline Updates
- First run: Fetches 14 days of historical data
- Subsequent runs: Only appends the latest day's price
- Maintains rolling 14-day window (removes oldest day)
- Reduces API calls and processing time significantly
"""

import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from garp_strategy import GARPStrategy
from database_manager import DatabaseManager
from market_data import fetch_and_analyze
from logger import logger
import yfinance as yf

def get_latest_price(symbol):
    """Fetch only today's closing price efficiently"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        if hist.empty:
            return None
        return float(hist['Close'].iloc[-1])
    except Exception as e:
        logger.warning(f"Failed to get latest price for {symbol}: {e}")
        return None

def update_stock_incremental(symbol, db, strategy, force_full=False):
    """
    Incrementally update a stock's data
    
    Args:
        symbol: Stock ticker
        db: DatabaseManager instance
        strategy: GARPStrategy instance
        force_full: If True, performs full 14-day analysis (for first run or weekly refresh)
    """
    existing_data = db.get_latest_stock_data(symbol)
    today = datetime.now().date()
    
    # Determine if we need a full refresh
    needs_full_refresh = force_full or not existing_data
    
    if existing_data:
        last_update = existing_data.get('date')
        if isinstance(last_update, str):
            last_update = datetime.fromisoformat(last_update).date()
        
        # Force full refresh if data is older than 7 days (safety check)
        days_since_update = (today - last_update).days
        if days_since_update > 7:
            logger.info(f"⚠️ {symbol}: Data is {days_since_update} days old. Forcing full refresh.")
            needs_full_refresh = True
    
    if needs_full_refresh:
        # Full analysis (includes 14-day sparkline fetch)
        logger.info(f"🔄 {symbol}: Full analysis (14 days)")
        card = strategy.analyze(symbol)
        
        if "Data Fetch Failed" in card.red_flags:
            logger.warning(f"⚠️ {symbol}: Failed to fetch data. Skipping.")
            return False
    else:
        # Incremental update: Only append today's price
        logger.info(f"📈 {symbol}: Incremental update (today only)")
        
        # Get today's latest price
        latest_price = get_latest_price(symbol)
        if not latest_price:
            logger.warning(f"⚠️ {symbol}: Could not fetch latest price. Falling back to full refresh.")
            return update_stock_incremental(symbol, db, strategy, force_full=True)
        
        # Perform full analysis but reuse existing sparkline + append new day
        card = strategy.analyze(symbol)
        
        if "Data Fetch Failed" in card.red_flags:
            logger.warning(f"⚠️ {symbol}: Analysis failed. Skipping.")
            return False
        
        # Update sparkline incrementally
        raw_data = existing_data.get('raw_data', {})
        old_sparkline = raw_data.get('sparkline', [])
        
        if old_sparkline and len(old_sparkline) > 0:
            # Append new price and keep only last 14 days
            new_sparkline = old_sparkline + [latest_price]
            card.sparkline = new_sparkline[-14:]  # Rolling window
            logger.info(f"✅ {symbol}: Sparkline updated ({len(old_sparkline)} → {len(card.sparkline)} days)")
        else:
            # If no existing sparkline, card.sparkline from analyze() is already populated
            logger.info(f"ℹ️ {symbol}: Using freshly fetched sparkline ({len(card.sparkline)} days)")
    
    # Generate report
    report = f"Date: {card.generated_at}\nStatus: {card.overall_status}\nPrice: {card.price}\nReason: {card.overall_reason}"
    
    # Save to DB
    db.save_daily_snapshot(card, report)
    return True

def main(force_full=False):
    """
    Main update routine
    
    Args:
        force_full: If True, forces full 14-day analysis for all stocks
    """
    logger.info("🚀 Starting Daily Data Update (Optimized)...")
    
    if force_full:
        logger.info("🔄 FULL REFRESH MODE: Fetching 14 days for all stocks")
    
    # 1. Initialize DB
    db = DatabaseManager()
    if not db.enabled:
        logger.error("❌ Database not configured. Aborting update.")
        return
    
    # 2. Get Targets
    etfs = Config.get('MARKET', {}).get('etf_watch_list', [])
    stocks = Config.get('MARKET', {}).get('public_showcase_list', [])
    targets = list(set(etfs + stocks))  # Unique list
    
    logger.info(f"📋 Targets: {targets}")
    
    # 3. Process Each
    strategy = GARPStrategy()
    success_count = 0
    
    for symbol in targets:
        try:
            if update_stock_incremental(symbol, db, strategy, force_full=force_full):
                success_count += 1
        except Exception as e:
            logger.error(f"❌ Error processing {symbol}: {e}")
    
    logger.info(f"✅ Update Complete. Successfully updated {success_count}/{len(targets)} stocks.")

if __name__ == "__main__":
    # Check if --force-full flag is passed
    import sys
    force_full = '--force-full' in sys.argv
    main(force_full=force_full)

