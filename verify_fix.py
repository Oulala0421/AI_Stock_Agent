import sys
import os
from unittest.mock import MagicMock, patch

# Add current directory to sys.path
sys.path.append(os.getcwd())

from strategy import calculate_position_size
# We import main inside the test function to patch dependencies if needed, 
# but patching decorators handle it if we import at top level.
# However, main imports might run code. main.py imports are safe.
from main import run_analysis

def test_position_size_logic():
    print("Testing calculate_position_size logic...")
    # Test Core
    shares, val, stop, sig = calculate_position_size(100, 5, 60, "Core", 10000)
    print(f"Core: {shares} shares, ${val}, Sig: {sig}")
    
    # Test Satellite
    shares, val, stop, sig = calculate_position_size(100, 5, 80, "Satellite", 5000)
    print(f"Satellite: {shares} shares, ${val}, Sig: {sig}")

@patch('main.get_stock_lists')
@patch('main.fetch_and_analyze')
@patch('main.get_market_news')
@patch('main.get_fundamentals')
@patch('main.generate_ai_briefing')
@patch('main.send_telegram')
@patch('main.send_line')
@patch('main.is_market_open')
@patch('main.get_market_regime')
@patch('main.get_economic_events')
def test_main_flow(mock_events, mock_regime, mock_open, mock_line, mock_tg, mock_ai, mock_fund, mock_news, mock_fetch, mock_lists):
    print("\nTesting main.py flow...")
    
    # Setup mocks
    mock_open.return_value = True
    mock_regime.return_value = {'spy_price': 400, 'is_bullish': True, 'vix': 15, 'ma50_above_ma200': True}
    mock_events.return_value = "No events"
    
    # Mock Lists: 1 Core Holding, 1 Satellite Watchlist
    mock_lists.return_value = (['AAPL'], ['GOOG'], {'AAPL': 100}, {'AAPL': 'Core', 'GOOG': 'Satellite'})
    
    # Mock Data
    mock_fetch.return_value = {
        'price': 150,
        'volatility': {'atr': 5},
        'trend': {'dual_momentum': {'is_bullish': True}},
        'momentum': {'rsi': 50, 'rsi_percentile': 0.5, 'bb_position': 0.5},
        'is_etf': False
    }
    mock_news.return_value = ("News Summary", 0.5)
    mock_fund.return_value = {'roe': '15%', 'target': 180}
    mock_ai.return_value = "AI Report Content"
    
    # Run main
    try:
        run_analysis(mode="post_market", dry_run=True)
        print("✅ main.py ran successfully with mocks!")
    except Exception as e:
        print(f"❌ main.py failed: {e}")
        import traceback
        traceback.print_exc()
        raise e

if __name__ == "__main__":
    try:
        test_position_size_logic()
        test_main_flow()
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
