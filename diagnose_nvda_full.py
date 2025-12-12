
from garp_strategy import GARPStrategy
from report_formatter import format_minimal_report
from market_data import get_market_regime
# Mock logging to avoid clutter
import logging
logging.basicConfig(level=logging.INFO)

print("🚀 Starting Diagnosis for NVDA...")

# 1. Strategy Analysis
strategy = GARPStrategy()
print("🔍 Analyzing NVDA...")
card = strategy.analyze("NVDA")

print(f"\n✅ Card Generated for {card.symbol}")
print(f"Price: {card.price}")
print(f"Status: {card.overall_status}")
print(f"Valuation Check: {card.valuation_check}")
dcf = card.valuation_check.get('dcf')
if dcf:
    print(f"DCF Intrinsic Value: {dcf.get('intrinsic_value')}")
else:
    print("❌ DCF Missing in Card")

if hasattr(card, 'monte_carlo_min'):
    print(f"Risk Range: {card.monte_carlo_min} - {card.monte_carlo_max}")
else:
    print("❌ Risk Range Missing in Card")

# 2. Add Dummy News Summary (Simulate main.py)
card.news_summary_str = "💡 AI: Positive\n💬 營收超預期，機構看好。"

# 3. Format Report
market_status = {
    'vix': 15.0,
    'is_bullish': True,
    'stage': 'Bull'
}

print("\n📝 Formatting Report...")
report = format_minimal_report(market_status, [card])

print("\n" + "="*50)
print("FINAL REPORT OUTPUT:")
print("="*50)
print(report)
print("="*50)

# Check specifically for the line
if "AI估值" in report:
    print("\n✅ SUCCESS: 'AI估值' line found.")
else:
    if "波動區間" in report:
        print("\n⚠️ PARTIAL: '波動區間' found (Fallback active).")
    else:
        print("\n❌ FAILURE: Neither AI Value nor Risk Range found.")
