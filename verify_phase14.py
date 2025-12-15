
import sys
import os
import pandas as pd
from data_adapter import DataAdapter
from advanced_metrics import AdvancedFinancials
from logger import logger

def verify_phase14():
    logger.info("🧪 Starting Phase 14 Model Modernization Verification...")
    
    ticker = "AAPL"
    
    # 1. Fetch Data via Adapter
    try:
        adapter = DataAdapter()
        bs, inc, cf = adapter.get_financials(ticker)
        info = adapter.get_ticker_info(ticker)
        
        # Determine Check Price (Close)
        price_df = adapter.get_price_data(ticker, period="1d")
        if price_df.empty:
            logger.error("Price fetch failed")
            return False
        price = price_df['Close'].iloc[-1]
        
    except Exception as e:
        logger.error(f"Failed to fetch setup data: {e}")
        return False
        
    # 2. Init Metrics
    try:
        adv = AdvancedFinancials(ticker, bs, inc, cf, info)
    except Exception as e:
        logger.error(f"Failed to init AdvancedFinancials: {e}")
        return False

    # 3. Test Altman Z'' (Double Prime)
    logger.info("🧪 Testing Altman Z'' (Double Prime)...")
    z_prime = adv.calculate_altman_z_double_prime(price)
    
    if z_prime.get('score') is not None:
        score = z_prime['score']
        status = z_prime['status']
        logger.info(f"   ✅ Z'' Score: {score:.2f} ({status})")
        
        # Check components
        comps = z_prime.get('components', {})
        logger.info(f"      X1 (Liquidity): {comps.get('X1_Liquidity', 0):.2f}")
        logger.info(f"      X4 (Mkt Leverage): {comps.get('X4_MarketLeverage', 0):.2f}")
        
        # Sanity check: Z'' is usually different from Z
        # Z'' uses Market Cap, Z (Manu) uses Book Equity in original, but our prev impl used Mkt Cap too.
        # Main diff: weights (Z'' has 6.56, 3.26...) vs Z (1.2, 1.4...).
        # Just ensure it calculated.
    else:
        logger.error(f"❌ Z'' calculation failed: {z_prime.get('details')}")
        return False

    # 4. Test Continuous F-Score
    logger.info("🧪 Testing Continuous F-Score (Sigmoid)...")
    f_cont = adv.calculate_continuous_f_score()
    
    if f_cont.get('score') is not None:
        score = f_cont['score']
        logger.info(f"   ✅ Continuous F-Score: {score:.4f} / 9.0")
        
        # Sanity Check Range
        if 0.0 <= score <= 9.0:
            logger.info("      Range Check Passed [0.0 - 9.0]")
        else:
            logger.error(f"      ❌ Score Out of Range: {score}")
            return False
            
        # Is it a float?
        if isinstance(score, float):
            logger.info("      Type Check Passed (Float)")
        else:
             logger.error("      ❌ Score is not float")
             return False
    else:
        logger.error(f"❌ Continuous F-Score calculation failed: {f_cont.get('details')}")
        return False

    logger.info("🏆 Phase 14 Verification Passed.")
    return True

if __name__ == "__main__":
    success = verify_phase14()
    sys.exit(0 if success else 1)
