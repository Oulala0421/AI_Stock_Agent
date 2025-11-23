from garp_strategy import GARPStrategy
from report_formatter import format_stock_report
import time

def run_analysis(symbols):
    strategy = GARPStrategy()
    print(f"🚀 Starting GARP Analysis for: {', '.join(symbols)}\n")
    
    for symbol in symbols:
        try:
            # Analyze
            card = strategy.analyze(symbol)
            
            # Format Report
            report = format_stock_report(card)
            
            # Print Result
            print("-" * 30)
            print(report)
            print("-" * 30)
            print("\n")
            
            # Respect API limits
            time.sleep(1) 
            
        except Exception as e:
            print(f"❌ Failed to analyze {symbol}: {e}")

if __name__ == "__main__":
    # Test with a mix of likely Pass, Watch, and Fail stocks
    test_symbols = ["AAPL", "NVDA", "TSLA", "INTC", "AMC"]
    run_analysis(test_symbols)
