from garp_strategy import GARPStrategy
from logger import logger
import sys
import logging

# Configure logger
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)

def test_sprint5():
    print("\n" + "="*50)
    print("🧪 SPRINT 5 VERIFICATION: Sentiment-Adjusted Valuation")
    print("="*50 + "\n")
    
    strategy = GARPStrategy()
    
    # 1. Component Test: Target Price Adjustment
    print("\n[Test 1] Logic Verification")
    
    base_target = 200.0
    # Sensitivity is 0.05 (5%)
    
    scenarios = [
        (0, 200.0, "Neutral"),
        (50, 205.0, "Positive Momentum (+2.5%)"),   # 200 * (1 + 0.05 * 0.5) = 200 * 1.025 = 205
        (100, 210.0, "Extreme Optimism (+5%)"),     # 200 * (1 + 0.05 * 1.0) = 200 * 1.05 = 210
        (-50, 195.0, "Negative Discount (-2.5%)"),  # 200 * (1 + 0.05 * -0.5) = 200 * 0.975 = 195
        (-100, 190.0, "Extreme Fear (-5%)")         # 200 * (1 + 0.05 * -1.0) = 200 * 0.95 = 190
    ]
    
    for score, expected, desc in scenarios:
        adj_target = strategy._calculate_sentiment_adjusted_target(base_target, score)
        print(f"Score: {score:>4} ({desc}) -> Adj Target: {adj_target:.2f} (Base: {base_target})")
        assert abs(adj_target - expected) < 0.1, f"Mismatch for score {score}"
        
    print("✅ Logic Verified")
    
    # 2. Integration Test: TSLA (Volatile/Sentimental)
    print("\n[Test 2] Analyzing TSLA (Live Sentiment Adjusment)")
    card = strategy.analyze("TSLA")
    
    print(f"Stock: TSLA")
    print(f"Base Target:   {card.valuation_check.get('fair_value')}")
    print(f"Adj Target:    {card.valuation_check.get('adjusted_fair_value')}")
    
    news_score = 0
    if 'news_analysis' in card.advanced_metrics:
        news_score = card.advanced_metrics['news_analysis'].get('sentiment_score', 0)
    print(f"Sentiment Score: {news_score}")
    
    print("Valuation Tags:")
    for tag in card.valuation_check['tags']:
        print(f" - {tag}")

    print("\n" + "="*50)
    print("✅ VERIFICATION COMPLETE")
    print("="*50 + "\n")

if __name__ == "__main__":
    test_sprint5()
