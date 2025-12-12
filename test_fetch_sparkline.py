from market_data import fetch_and_analyze
import logging

logging.basicConfig(level=logging.INFO)

def test_fetch(symbol):
    print(f"\n{'='*60}")
    print(f"Testing fetch_and_analyze for {symbol}")
    print('='*60)
    
    data = fetch_and_analyze(symbol)
    
    if not data:
        print(f"❌ fetch_and_analyze returned None for {symbol}")
        return
    
    sparkline = data.get('sparkline', [])
    price = data.get('price')
    
    print(f"Price: ${price}")
    print(f"Sparkline length: {len(sparkline)}")
    
    if len(sparkline) > 0:
        print(f"First 3: {sparkline[:3]}")
        print(f"Last 3: {sparkline[-3:]}")
        print(f"✅ Sparkline exists and has {len(sparkline)} days")
    else:
        print(f"❌ Sparkline is EMPTY!")
        print(f"All keys in data: {list(data.keys())}")

if __name__ == "__main__":
    symbols = ["GOOG", "TSLA", "NVDA"]
    
    for symbol in symbols:
        test_fetch(symbol)
