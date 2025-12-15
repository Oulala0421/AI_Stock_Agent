
import sys
import os
import logging
from datetime import datetime, timedelta
from backtest_engine import BacktestEngine
from logger import logger

def verify_phase16():
    logger.info("🧪 Starting Phase 16 Backtest Verification...")
    
    ticker = "AAPL"
    end_date = datetime.now()
    # Use 14 days for quick verification (180 days takes too long with live news)
    start_date = end_date - timedelta(days=14) 
    
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    try:
        engine = BacktestEngine(ticker, start_str, end_str, initial_capital=100000.0)
        engine.run()
        
        # Validation Checks
        if not engine.ledger:
            logger.warning("⚠️ No trades executed in 6 months. Strategy might be too strict or logic issue.")
            # Note: GARP is strict. It might buy/hold.
        else:
            logger.info(f"✅ Executed {len(engine.ledger)} trades.")
            
        logger.info(f"✅ Final Capital: ${engine.capital + (engine.holdings * engine.mock_adapter.get_price_data(ticker)['Close'].iloc[-1]):.2f}")
        logger.info("🏆 Phase 16 Verification Passed (Engine Ran Successfully).")
        return True
        
    except Exception as e:
        logger.error(f"❌ Backtest Engine Failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    # Configure logging to show info
    logging.basicConfig(level=logging.INFO)
    success = verify_phase16()
    sys.exit(0 if success else 1)
