from garp_strategy import GARPStrategy
from logger import logger
import sys

# Configure logger to stdout
import logging
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)

def test_strategy():
    strategy = GARPStrategy()
    
    # Test cases: 
    # AAPL: Expect High Score, Safe Z-Score
    # NVDA: Expect High Score, Strong Growth
    # PTON: Expect Distress? (Peloton)
    # AAL: American Airlines (High Debt typically)
    
    tickers = ["AAPL", "NVDA", "PTON", "AAL"]
    
    print("\n" + "="*50)
    print("🧪 STARTING STRATEGY VERIFICATION")
    print("="*50 + "\n")

    for symbol in tickers:
        print(f"\nProcessing {symbol}...")
        card = strategy.analyze(symbol)
        
        print(f"\n--- Result for {symbol} ---")
        print(f"Status: {card.overall_status}")
        print(f"Reason: {card.overall_reason}")
        print(f"Price: {card.price}")
        
        print("\n[Advanced Metrics]")
        print(f"Piotroski F-Score: {card.advanced_metrics.get('piotroski_score')} / 9")
        print(f"Altman Z-Score: {card.advanced_metrics.get('altman_z_score')} ({'Safe' if card.advanced_metrics.get('altman_z_score') and card.advanced_metrics.get('altman_z_score') > 3 else 'Distress/Grey'})")
        print(f"FCF Yield: {card.advanced_metrics.get('fcf_yield')}")
        
        print("\n[Tags]")
        for tag in card.advanced_metrics.get('tags', []):
            print(f" - {tag}")
            
        print("\n[Red Flags]")
        for flag in card.red_flags:
            print(f" 🚩 {flag}")

    print("\n" + "="*50)
    print("✅ VERIFICATION COMPLETE")
    print("="*50 + "\n")

if __name__ == "__main__":
    test_strategy()
