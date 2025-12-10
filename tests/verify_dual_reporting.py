import sys
import os
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import run_analysis
from data_models import OverallStatus

def verify_dual_reporting():
    print("🚀 Starting Dual Reporting Verification...")
    
    # Mock Data
    mock_holdings = ['NVDA', 'TSM']
    mock_watchlist = ['INTC'] # Should trigger risk if correlated or concentrated
    mock_costs = {'NVDA': 100, 'TSM': 100}
    mock_types = {'NVDA': 'Core', 'TSM': 'Core', 'INTC': 'Satellite'}
    
    # Mock Market Data to avoid API calls
    with patch('main.get_market_regime') as mock_market, \
         patch('main.get_stock_lists') as mock_lists, \
         patch('main.is_market_open', return_value=True), \
         patch('main.Config') as mock_config, \
         patch('news_agent.NewsAgent.get_market_outlook', return_value="AI Outlook: Bullish"), \
         patch('main.DatabaseManager'), \
         patch('main.PortfolioManager') as MockPM, \
         patch('main.GARPStrategy') as MockStrategy, \
         patch('news_agent.NewsAgent.analyze_news') as MockNewsAnalysis, \
         patch('main.GoogleNewsSearcher') as MockSearcher: # Patch MockSearcher class itself, or main.GoogleNewsSearcher

        # Setup Mocks
        MockSearcher.return_value.search_news.return_value = [{'title': 'News', 'link': 'http'}]
        mock_market.return_value = {'spy_price': 500, 'vix': 15, 'is_bullish': True, 'z_score': 1.0}
        mock_lists.return_value = (mock_holdings, mock_watchlist, mock_costs, mock_types)
        
        # Config w/ Private User ID
        mock_config.get.side_effect = lambda k: 'USER123' if k == 'LINE_USER_ID' else ('GROUP123' if k == 'LINE_GROUP_ID' else 'TOKEN123')
        mock_config.__getitem__.side_effect = lambda k: 'TOKEN123'
        
        # Portfolio Manager Behavior
        pm_instance = MockPM.return_value
        # Simulate warnings for INTC
        pm_instance.check_concentration.return_value = ["⚠️ Concentration Warning: Tech sector > 30%"]
        pm_instance.check_correlation.return_value = ["⚠️ Correlation Warning: INTC vs NVDA > 0.8"]
        
        # Strategy Behavior
        mock_card_holdings = MagicMock(symbol='NVDA', overall_status='PASS', private_notes=[], monte_carlo_min=100.0, monte_carlo_max=200.0, price=100.0)
        mock_card_watchlist = MagicMock(symbol='INTC', overall_status='WATCHLIST', private_notes=[], monte_carlo_min=20.0, monte_carlo_max=30.0, price=25.0)
        
        strategy_instance = MockStrategy.return_value
        strategy_instance.analyze.side_effect = lambda symbol: mock_card_holdings if symbol in ['NVDA', 'TSM'] else mock_card_watchlist

        # News Analysis Behavior
        MockNewsAnalysis.return_value = {'sentiment': 'Positive', 'summary_reason': 'Good news'}

        # Run Analysis
        print("Running run_analysis(dry_run=True)...")
        run_analysis(dry_run=True)
        
        # Verification
        print("\n🔎 Verifying Private Notes Populated...")
        if mock_card_watchlist.private_notes:
            print("✅ INTC has private notes:", mock_card_watchlist.private_notes)
        else:
            print("❌ INTC has NO private notes (Failed)")

        print("✅ Verification Complete.")

if __name__ == "__main__":
    verify_dual_reporting()
