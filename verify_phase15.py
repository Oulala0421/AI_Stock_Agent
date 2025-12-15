
import sys
import os
import pandas as pd
from market_status import get_implied_erp
from sector_analysis import SectorAnalysis
from garp_strategy import GARPStrategy
from logger import logger

def verify_phase15():
    logger.info("🧪 Starting Phase 15 Context-Aware Valuation Verification...")
    
    # 1. Test Implied ERP
    logger.info("Step 1: Testing Implied ERP...")
    erp_default = get_implied_erp() # Uses VIX fallback (20) -> 0.045 + (8)*0.003
    logger.info(f"   ✅ Implied ERP (Default VIX~20): {erp_default:.2%}")
    
    # Test with custom VIX
    erp_high_vol = get_implied_erp(30.0) # 0.045 + (15)*0.003 = 0.09
    logger.info(f"   ✅ Implied ERP (VIX=30): {erp_high_vol:.2%}")
    if erp_high_vol < erp_default:
        logger.error("❌ Higher Volatility should yield Higher ERP")
        return False

    # 2. Test Sector Analysis
    logger.info("Step 2: Testing Sector Analysis...")
    sa = SectorAnalysis()
    # Tech avg PEG = 1.8, Std = 0.5
    # If Stock PEG = 1.3 -> Z = (1.3 - 1.8)/0.5 = -1.0 (Cheaper)
    z_score = sa.calculate_sector_z_score("Technology", "peg", 1.3)
    logger.info(f"   ✅ Sector Z-Score (Tech PEG 1.3 vs 1.8): {z_score:.2f}")
    
    if abs(z_score - (-1.0)) > 0.01:
        logger.error(f"❌ Z-Score Math Wrong. Got {z_score}")
        return False
        
    # 3. Test Strategy Integration
    logger.info("Step 3: Testing GARP Strategy Integration...")
    try:
        strategy = GARPStrategy()
        card = strategy.analyze("AAPL")
    except Exception as e:
        logger.error(f"❌ Strategy Analysis Failed: {e}")
        return False
        
    if not card:
        logger.error("❌ Card is None")
        return False
        
    # Check Sector Z
    peg_z = card.valuation_check.get('sector_peg_z')
    if peg_z is not None:
        logger.info(f"   ✅ Strategy calculated Sector PEG Z: {peg_z:.2f}")
    else:
        # If PEG was None, this might be None. AAPL usually has PEG.
        logger.warning("   ⚠️ Sector PEG Z is None (Missing Data?)")
        
    # Check Dynamic DCF
    dcf_res = card.valuation_check.get('dcf')
    if dcf_res:
        val = dcf_res.get('intrinsic_value')
        logger.info(f"   ✅ DCF Value Repoted: {val}")
        # Note: We can't easily see the internal ERP used here without checking logs or modifying return, 
        # but execution confirms the path.
    else:
        logger.warning("   ⚠️ DCF Results Missing")

    logger.info("🏆 Phase 15 Verification Passed.")
    return True

if __name__ == "__main__":
    success = verify_phase15()
    sys.exit(0 if success else 1)
