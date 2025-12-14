from report_formatter import format_minimal_report
from garp_strategy import GARPStrategy
from data_models import StockHealthCard, OverallStatus

def test_market_closed_format():
    print("--- Testing Market Closed Format ---")
    market_status = {"vix": 15.0, "is_bullish": True}
    report = format_minimal_report(market_status, [], macro_status="RISK_ON", market_is_open=False)
    print(report)
    assert "😴 **休市通知**" in report
    assert "今日美股休市" in report
    print("✅ Market Closed Format Verified\n")

def test_strategy_logic():
    print("--- Testing Strategy Logic (Duplicate Fix & Sector) ---")
    strategy = GARPStrategy()
    
    # Create a mock card
    card = StockHealthCard(symbol="TEST", price=100.0, sector="Technology")
    
    # Verify Sector Field Exists
    assert hasattr(card, 'sector')
    assert card.sector == "Technology"
    print("✅ Sector Field Verified")
    
    # Mock checks to pass everything
    card.solvency_check['is_passing'] = True
    card.quality_check['is_passing'] = True
    card.valuation_check['is_passing'] = True
    card.technical_setup['is_passing'] = True
    
    # Test Logic Execution
    # We expect status to be PASS initially
    strategy._determine_overall_status(card, market_data={"trend": {"is_above_ma200": True}})
    print(f"Status (All Pass): {card.overall_status}")
    assert card.overall_status == "PASS"
    
    # Test SMA200 Logic (This was lost in the duplicate method)
    # If market_data says below MA200, should downgrade to WATCHLIST
    strategy._determine_overall_status(card, market_data={"trend": {"is_above_ma200": False}})
    print(f"Status (Below MA200): {card.overall_status}")
    assert card.overall_status == "WATCHLIST"
    assert "Below SMA200" in card.overall_reason
    
    print("✅ Strategy Logic (SMA200 Filter) Verified - Duplicate Method Successfully Removed\n")

if __name__ == "__main__":
    try:
        test_market_closed_format()
        test_strategy_logic()
        print("🎉 All Phase 8 Tests Passed!")
    except Exception as e:
        print(f"❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
