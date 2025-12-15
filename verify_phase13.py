
import sys
import os
import pandas as pd
from garp_strategy import GARPStrategy
from logger import logger

def verify_integration():
    logger.info("🧪 Starting Phase 13 Integration Verification...")
    
    # Initialize Strategy
    try:
        strategy = GARPStrategy()
    except Exception as e:
        logger.error(f"❌ Failed to init GARPStrategy: {e}")
        return False
        
    symbol = "AAPL"
    logger.info(f"🔄 Running Analysis on {symbol}...")
    
    # Run Analysis
    card = strategy.analyze(symbol)
    
    if not card or card.price == 0:
        logger.error("❌ Analysis returned empty/invalid card!")
        return False
        
    logger.info(f"✅ Analysis Complete.")
    logger.info(f"   Price: ${card.price:.2f}")
    logger.info(f"   Status: {card.overall_status}")
    logger.info(f"   Reason: {card.overall_reason}")
    
    # Check Advanced Metrics (Proof that DataAdapter -> AdvancedFinancials worked)
    adv_metrics = card.advanced_metrics
    logger.info("📊 Checking Advanced Metrics...")
    
    f_score = adv_metrics.get('piotroski_score')
    z_score = adv_metrics.get('altman_z_score')
    
    if f_score is not None:
        logger.info(f"   ✅ Piotroski F-Score: {f_score}")
    else:
        logger.error("❌ Piotroski F-Score is None!")
        return False
        
    if z_score is not None:
        logger.info(f"   ✅ Altman Z-Score: {z_score:.2f}")
    else:
        logger.error("❌ Altman Z-Score is None!")
        return False
        
    logger.info("🏆 Phase 13 Integration Verification Passed.")
    return True

if __name__ == "__main__":
    success = verify_integration()
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
