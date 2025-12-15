
import logging
from garp_strategy import GARPStrategy
from report_formatter import format_stock_report
from data_models import OverallStatus
import pandas as pd

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_report_logic():
    print("🚀 Starting Manual Report Logic Verification (Phase 16.5)...")
    
    # Initialize Strategy
    strategy = GARPStrategy()
    # formatter = ReportFormatter() # Removed class init
    
    # Test Cases: High Growth (TSLA), Strong Cash Cow (GOOG), High Momentum (NVDA)
    tickers = ["TSLA", "NVDA", "GOOG"]
    
    for symbol in tickers:
        print(f"\n🔄 Analyzing {symbol}...")
        try:
            # 1. Run Strategy Analysis (Live Data)
            # This uses the real logic we just patched
            card = strategy.analyze(symbol)
            
            # 2. Print Key Metrics verified in Phase 16.5
            print(f"--- 📊 Analysis Result: {symbol} ---")
            print(f"Status: {card.overall_status}")
            print(f"Reason: {card.overall_reason}")
            
            # Valuation Tags
            print(f"Valuation Tags: {card.valuation_check.get('tags', [])}")
            
            # DCF Details
            dcf = card.valuation_check.get('dcf')
            if dcf:
                print(f"DCF Value: ${dcf.get('intrinsic_value', 0):.2f}")
                print(f"Growth Use: {dcf.get('growth_rate', 0):.1%}")
                print(f"Discount Rate: {dcf.get('discount_rate', 0):.1%}")
            else:
                print("DCF: N/A")
                
            # Advanced Metrics Tags (Review Z-Score)
            adv_tags = card.advanced_metrics.get('tags', [])
            print(f"Advanced Tags: {adv_tags}")
            
            # News Logic Check
            news = card.advanced_metrics.get('news_analysis')
            if news:
                print(f"News Sentiment: {news.get('sentiment')} (Score: {news.get('sentiment_score')})")
                print(f"Prediction: {news.get('prediction')}")
            else:
                print("News: None")

            # 3. Generate Report (Dry Run)
            report = format_stock_report(card)
            print("\n📝 Report Preview (Snippet):")
            lines = report.split('\n')
            for line in lines[:20]: # Show header and first few lines
                 print(line)
                 
        except Exception as e:
            logger.error(f"Failed to analyze {symbol}: {e}")

if __name__ == "__main__":
    verify_report_logic()
