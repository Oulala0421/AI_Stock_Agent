
from report_formatter import format_minimal_report
from data_models import StockHealthCard, OverallStatus
from types import SimpleNamespace

# Mock Market Status
market_status = {
    'vix': 14.5,
    'is_bullish': True,
    'stage': 'Confirmed Uptrend'
}

# Mock Stock Cards
card1 = StockHealthCard(
    symbol="NVDA",
    price=120.0,
    overall_status=OverallStatus.PASS.value,
    quality_check={'roe': 0.45},
    valuation_check={'margin_of_safety_dcf': 0.20}, # Deep Value
    solvency_check={},
    technical_setup={}
)
card1.predicted_return_1w = 3.5
card1.confidence_score = 0.85
card1.news_summary_str = "💡 AI: 😃 Positive\n💬 營收超預期，數據中心需求強勁，機構上調目標價。"

card2 = StockHealthCard(
    symbol="AMD",
    price=88.5,
    overall_status=OverallStatus.WATCHLIST.value,
    quality_check={'roe': 0.15},
    valuation_check={'margin_of_safety_dcf': -0.05},
    solvency_check={},
    technical_setup={}
)
card2.predicted_return_1w = 0.8
card2.confidence_score = 0.6
card2.news_summary_str = "💡 AI: 😐 Neutral\n💬 新發布的晶片效能符合預期，但市場反應冷淡。"

card3 = StockHealthCard(
    symbol="INTC",
    price=30.0,
    overall_status=OverallStatus.REJECT.value,
    quality_check={},
    valuation_check={},
    solvency_check={},
    technical_setup={}
)

stock_cards = [card1, card2, card3]

print("="*40)
print("TESTING NEW FORMAT OUTPUT")
print("="*40)
print(format_minimal_report(market_status, stock_cards))
print("="*40)
