
import sys
import os
import pandas as pd
from data_adapter import DataAdapter
from logger import logger

def verify_adapter():
    logger.info("🧪 Starting DataAdapter Verification...")
    
    adapter = DataAdapter()
    ticker = "AAPL"
    
    # Test 1: Financials
    logger.info(f"Step 1: Fetching Financials for {ticker}...")
    bs, inc, cf = adapter.get_financials(ticker)
    
    if bs.empty or inc.empty or cf.empty:
        logger.error("❌ Stats are empty!")
        return False
        
    logger.info("✅ Financials Fetched.")
    logger.info(f"   Balance Sheet Shape: {bs.shape}")
    logger.info(f"   Income Stmt Shape: {inc.shape}")
    logger.info(f"   Cash Flow Shape: {cf.shape}")

    # Check Critical Keys for Compatibility
    required_keys = {
        'bs': ['Total Assets', 'Total Liabilities Net Minority Interest'],
        'inc': ['Net Income', 'Total Revenue'],
        'cf': ['Operating Cash Flow'] # YF usually has this, or 'Total Cash From Operating Activities'
    }
    
    # Normalize index for checking (sometimes YFindices differ slightly by version)
    # But usually exact match is needed for advanced_metrics.
    
    # Specific check for advanced_metrics compatibility
    logger.info("Step 2: Checking Schema Compatibility...")
    
    # BS
    for k in required_keys['bs']:
        if k not in bs.index:
            logger.warning(f"⚠️ Missing '{k}' in Balance Sheet Index. Partial/Different index?")
            # Don't fail immediately, YF keys change often. Just log warnings.
        else:
            logger.info(f"   ✅ Found '{k}' in BS")
            
    # INC
    for k in required_keys['inc']:
        if k not in inc.index:
            logger.warning(f"⚠️ Missing '{k}' in Income Stmt Index.")
        else:
            logger.info(f"   ✅ Found '{k}' in INC")
            
    # CF
    # CF key is tricky 'Operating Cash Flow' or 'Total Cash From Operating Activities'
    found_ocf = False
    for candidate in ['Operating Cash Flow', 'Total Cash From Operating Activities']:
        if candidate in cf.index:
            found_ocf = True
            logger.info(f"   ✅ Found OCF key: '{candidate}'")
            break
    if not found_ocf:
        logger.warning("⚠️ Missing Operating Cash Flow key in CF.")

    # Test 2: Price Data
    logger.info(f"Step 3: Fetching Price Data for {ticker}...")
    df = adapter.get_price_data(ticker, period="1mo")
    if df.empty:
        logger.error("❌ Price data is empty")
        return False
        
    logger.info(f"✅ Price Data Fetched. Rows: {len(df)}")
    
    logger.info("🏆 DataAdapter Verification Complete.")
    return True

if __name__ == "__main__":
    success = verify_adapter()
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
