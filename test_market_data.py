from market_data import fetch_and_analyze
import logging

logging.basicConfig(level=logging.INFO)

def test_fetch(symbol="VOO"):
    print(f"Testing {symbol}...")
    data = fetch_and_analyze(symbol)
    if not data:
        print("Fetch failed.")
        return
        
    sparkline = data.get('sparkline')
    print(f"Sparkline Type: {type(sparkline)}")
    print(f"Sparkline: {sparkline}")
    print(f"Length: {len(sparkline) if sparkline else 0}")

if __name__ == "__main__":
    test_fetch("VOO")
