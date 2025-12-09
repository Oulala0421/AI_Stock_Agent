from garp_strategy import GARPStrategy
from logger import logger
import sys
import logging

# Configure logger
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)

def test_sprint4():
    print("\n" + "="*50)
    print("🧪 SPRINT 4 VERIFICATION: Quantitative Sentiment & Dynamic PEG")
    print("="*50 + "\n")
    
    strategy = GARPStrategy()
    
    # 1. Component Test: Dynamic PEG Calculation
    print("\n[Test 1] Logic Verification")
    test_cases = [0, 50, -50, 100, -100]
    base_peg = 1.5
    
    for score in test_cases:
        peg_limit = strategy._calculate_dynamic_peg(score)
        expected_adjustment = 1 + (0.2 * (score/100.0))
        expected_peg = max(1.0, min(2.0, base_peg * expected_adjustment))
        print(f"Sentiment Score: {score:>4} -> Dynamic PEG: {peg_limit:.2f} (Expected: {expected_peg:.2f})")
        assert abs(peg_limit - expected_peg) < 0.01, "Calculation Mismatch"
        
    print("✅ Logic Verified")
    
    # 2. Integration Test: Live Market Sentiment
    print("\n[Test 2] Live Market Check (SPY)")
    
    # Force cache clear if needed, but new instance covers it
    market_score = strategy.get_market_sentiment()
    print(f"Live SPY Sentiment Score: {market_score}")
    
    # 3. Strategy Application
    print("\n[Test 3] Analyzing AAPL with Dynamic PEG")
    # AAPL usually has PEG around 2-3, let's see what limit it gets
    card = strategy.analyze("AAPL")
    
    print(f"Status: {card.overall_status}")
    print("Valuation Tags:")
    for tag in card.valuation_check['tags']:
        print(f" - {tag}")

    print("\n" + "="*50)
    print("✅ VERIFICATION COMPLETE")
    print("="*50 + "\n")

if __name__ == "__main__":
    test_sprint4()
