import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent dir to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from portfolio_manager import PortfolioManager

class TestPortfolioManager(unittest.TestCase):
    
    def setUp(self):
        # Mock Portfolio: Heavy in Technology (NVDA)
        self.mock_data = [
            {'symbol': 'NVDA', 'shares': 50, 'avg_cost': 120, 'sector': 'Technology'}, # Val: 6000
            {'symbol': 'AAPL', 'shares': 10, 'avg_cost': 180, 'sector': 'Technology'}, # Val: 1800
            {'symbol': 'JPM',  'shares': 10, 'avg_cost': 150, 'sector': 'Financial'},  # Val: 1500
        ]
        # Total Val: 9300. Tech Val: 7800 (83%)
        self.pm = PortfolioManager(mock_portfolio=self.mock_data)

    def test_concentration_check(self):
        print("\n🧪 Testing Concentration Check...")
        
        # Test 1: Add another Tech stock (Should warn, 83% > 30%)
        warnings = self.pm.check_concentration("AMD", "Technology")
        print(f"   Input: AMD (Technology) -> Warnings: {warnings}")
        self.assertTrue(len(warnings) > 0)
        self.assertIn("板塊集中度過高", warnings[0])
        
        # Test 2: Add Health stock (Should be safe, 0% < 30%)
        warnings_safe = self.pm.check_concentration("PFE", "Healthcare")
        print(f"   Input: PFE (Healthcare) -> Warnings: {warnings_safe}")
        self.assertEqual(len(warnings_safe), 0)

    @patch('yfinance.download')
    def test_correlation_check(self, mock_download):
        print("\n🧪 Testing Correlation Check...")
        
        # Mock yfinance data for NVDA(Top1), AAPL(Top2), JPM(Top3) + New Stock
        # Create a Mock DataFrame with close prices
        import pandas as pd
        import numpy as np
        
        # Scenario A: High Correlation (TSM vs NVDA)
        # Create correlated series
        dates = pd.date_range(start='2024-01-01', periods=50)
        nvda_prices = np.linspace(100, 150, 50) + np.random.normal(0, 1, 50)
        tsm_prices = nvda_prices * 0.8 + np.random.normal(0, 2, 50) # Highly correlated
        jpm_prices = np.random.normal(150, 10, 50) # Uncorrelated
        aapl_prices = np.linspace(150, 180, 50) 
        
        data = pd.DataFrame({
            'NVDA': nvda_prices,
            'TSM': tsm_prices,
            'JPM': jpm_prices,
            'AAPL': aapl_prices
        }, index=dates)
        
        # Mock the MultiIndex return structure of yf.download (adj close) OR simple df
        # yfinance often returns MultiIndex if group_by='ticker', or single level if 'column'
        # Let's assume standard DataFrame for simplicity as logic handles it
        mock_download.return_value = data
        
        # Override the columns in check_correlation logic (it uses 'Close')
        # Wait, my logic calls ['Close'] on the result.
        # So mock_download should return an object where ['Close'] returns the DF above.
        
        mock_download_obj = MagicMock()
        mock_download_obj.__getitem__.return_value = data # This handles ['Close']
        if not isinstance(mock_download.return_value, pd.DataFrame):
             # If logic expects object['Close']
             mock_download.return_value = {'Close': data}
        else:
             # Logic: yf.download(... )['Close'] -> if yf.download returns DF, this fails if key missing
             # But yf.download(..., group_by='ticker') usually returns complex. 
             # Let's adjust mock to return a DataFrame that HAS a 'Close' key? 
             # No, yf.download returns a DF. accessing ['Close'] gives the Close columns.
             # So I should return a DF with MultiIndex columns (Price, Ticker)? 
             # Simplify: Just verify logic works if 'Close' access works.
             pass
        
        # Re-mocking properly directly in logic via simple patch is hard due to ['Close']
        # Let's Mock the actual call return to be a DF that HAS columns like TSM, NVDA.
        # BUT the code does: data = yf.download(...)['Close']
        # So yf.download(...) must return something subscriptable.
        
        class MockYFResult(dict):
            pass
        
        res = MockYFResult()
        res['Close'] = data
        mock_download.return_value = res
        
        warnings = self.pm.check_correlation("TSM")
        print(f"   Input: TSM (High Corr with NVDA) -> Warnings: {warnings}")
        
        # Expect warning
        self.assertTrue(any("NVDA" in w for w in warnings))


if __name__ == '__main__':
    unittest.main()
