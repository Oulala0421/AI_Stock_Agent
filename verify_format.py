from report_formatter import format_minimal_report
from data_models import StockHealthCard, OverallStatus

def create_mock_card(symbol, price, intrinsic, z_score, rating=OverallStatus.PASS):
    card = StockHealthCard(symbol=symbol)
    card.price = price
    card.overall_status = rating.value
    
    # Mock Valuation Check
    card.valuation_check = {
        'dcf': {'intrinsic_value': intrinsic},
        'margin_of_safety_dcf': (intrinsic - price) / price if intrinsic else 0,
        'fair_value': intrinsic,
        'tags': [f"Z={z_score:.2f}"]
    }
    
    # Mock Monte Carlo risk range
    card.monte_carlo_min = price * 0.95
    card.monte_carlo_max = price * 1.05
    
    # Mock AI Analysis
    card.advanced_metrics = {
        'news_analysis': {
            'summary_reason': '這是AI生成的分析建議，不含條列式，主要測試格式顯示是否完整且正確。'
        }
    }
    
    return card

def verify_report_logic():
    print("🚀 Verifying Report Format Logic...\n")
    
    # Case 1: Serious Premium + Euphoria
    # Price 200, Intrinsic 100 (Premium 100%), Z=2.5
    card1 = create_mock_card("TSLA", 200.0, 100.0, 2.5, OverallStatus.REJECT)
    print("--- Case 1: High Premium / Euphoria ---")
    print(format_minimal_report({}, [card1]))
    
    # Case 2: Deep Value + Panic
    # Price 100, Intrinsic 150 (Discount 50%), Z=-2.0
    card2 = create_mock_card("NVDA", 100.0, 150.0, -2.0, OverallStatus.PASS)
    print("\n--- Case 2: Deep Value / Panic ---")
    print(format_minimal_report({}, [card2]))
    
    # Case 3: Neutral
    # Price 100, Intrinsic 110 (Discount 10%), Z=0.5
    card3 = create_mock_card("AAPL", 100.0, 110.0, 0.5, OverallStatus.WATCHLIST)
    print("\n--- Case 3: Neutral / Fair ---")
    print(format_minimal_report({}, [card3]))
    
    # Case 4: No DCF
    card4 = create_mock_card("UNKNOWN", 50.0, None, 0.0, OverallStatus.WATCHLIST)
    print("\n--- Case 4: No DCF Data ---")
    print(format_minimal_report({}, [card4]))

if __name__ == "__main__":
    verify_report_logic()
