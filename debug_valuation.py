
from garp_strategy import GARPStrategy
from advanced_metrics import AdvancedFinancials
import yfinance as yf
from logger import logger
import logging

# Setup Logging to Console
logging.basicConfig(level=logging.INFO)

symbol = "NVDA" # Use one of the symbols user mentioned
print(f"🔬 Debugging Valuation for {symbol}...")

# 1. Init Strategy (loads thresholds)
strategy = GARPStrategy()

# 2. Fetch Data Manually like in analyze()
ticker = yf.Ticker(symbol)
print("   Ticker fetched.")

# 3. Init AdvancedFinancials
adv = None
try:
    adv = AdvancedFinancials(ticker)
    print("   AdvancedFinancials initialized.")
    if adv.has_data:
        print("   Has Financial Data: YES")
        # Check specific fields needed for DCF
        print(f"   BS Columns: {adv.bs.shape}")
        print(f"   CF Columns: {adv.cf.shape}")
        
    else:
        print("   Has Financial Data: NO")
except Exception as e:
    print(f"   ❌ AdvancedFinancials Init Failed: {e}")

# 4. Run DCF Calc
if adv:
    z_score = 0.5 # Mock market z-score
    dcf_res = adv.calculate_sentiment_adjusted_dcf(z_score)
    print("\n🧮 DCF Result Direct Call:")
    print(dcf_res)
    
    intrinsic_val = dcf_res.get('intrinsic_value')
    if intrinsic_val:
        print(f"   Intrinsic Value: {intrinsic_val}")
    else:
        print("   Intrinsic Value is None/Empty.")

# 5. Run Full Strategy Analyze
print("\n🔄 Running Full Strategy Analysis...")
card = strategy.analyze(symbol)

print(f"\n📝 Card Results for {symbol}:")
print(f"   Overall Status: {card.overall_status}")
print(f"   Price: {card.price}")
dcf_in_card = card.valuation_check.get('dcf')
print(f"   Valuation Check DCF: {dcf_in_card}")

if dcf_in_card:
    print(f"   Intrinsic Value in Card: {dcf_in_card.get('intrinsic_value')}")
else:
    print("   ❌ DCF Check missing in card!")
