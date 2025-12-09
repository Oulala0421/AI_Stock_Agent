from garp_strategy import GARPStrategy
from data_models import StockHealthCard, OverallStatus
from logger import logger
import sys
import logging

# Configure logger
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)

def test_sprint2():
    strategy = GARPStrategy()
    
    # Test Candidates:
    # TSLA: Often volatile, check prediction confidence and trend.
    # INTC: Known downtrend (2024), check SMA200 filter.
    # MSFT: Steady uptrend, check positive prediction.
    
    tickers = ["TSLA", "INTC", "MSFT"]
    
    print("\n" + "="*50)
    print("🧪 SPRINT 2 VERIFICATION: Trend & Monte Carlo")
    print("="*50 + "\n")

    for symbol in tickers:
        print(f"\nProcessing {symbol}...")
        card = strategy.analyze(symbol)
        
        print(f"\n--- Result for {symbol} ---")
        print(f"Status: {card.overall_status}")
        print(f"Reason: {card.overall_reason}")
        print(f"Price: {card.price}")
        
        print("\n[Technical tags]")
        for tag in card.technical_setup['tags']:
            print(f" - {tag}")

        print("\n[Prediction (Monte Carlo)]")
        if card.predicted_return_1w is not None:
            direction = "🔺 UP" if card.predicted_return_1w > 0 else "🔻 DOWN"
            print(f"Forecast (1W): {direction} {card.predicted_return_1w:.2f}%")
            print(f"Confidence:  {card.confidence_score:.0%}")
            if card.monte_carlo_min is not None:
                print(f"VaR 95 (Min): {card.monte_carlo_min:.2f}% (Pessimistic Scenario)")
            else:
                print("VaR 95 (Min): N/A (Cache may be stale)")
        else:
            print("❌ No Prediction Data")

        print("\n[Advanced Metrics]")
        print(f"Altman Z-Score: {card.advanced_metrics.get('altman_z_score')}")
        print("Tags:")
        for tag in card.advanced_metrics.get('tags', []):
             print(f" - {tag}")

        print("\n[News Analysis]")
        news = card.advanced_metrics.get('news_analysis')
        if news:
            print(f"Sentiment: {news.get('sentiment')} (Conf: {news.get('confidence',0):.0%})")
            print(f"Summary: {news.get('summary_reason')}")
        else:
             print("No News Analysis")
        
    print("\n" + "="*50)
    print("✅ VERIFICATION COMPLETE")
    print("="*50 + "\n")

if __name__ == "__main__":
    test_sprint2()
