import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from garp_strategy import GARPStrategy
from data_models import OverallStatus

class TestGARPStrategy(unittest.TestCase):
    def setUp(self):
        self.strategy = GARPStrategy()

    @patch('garp_strategy.yf.Ticker')
    @patch('garp_strategy.fetch_and_analyze')
    def test_perfect_stock(self, mock_fetch, mock_ticker):
        """Test a stock that passes all checks."""
        # Mock Market Data (Technicals)
        mock_fetch.return_value = {
            'price': 100.0,
            'momentum': {'rsi': 50},
            'trend': {'ma50_above_ma200': True}
        }
        
        # Mock Fundamental Data
        mock_info = {
            'debtToEquity': 50,          # < 200 (Pass)
            'currentRatio': 2.0,         # > 1.0 (Pass)
            'returnOnEquity': 0.20,      # > 15% (Pass)
            'grossMargins': 0.50,        # > 0 (Pass)
            'trailingPE': 20,
            'pegRatio': 1.0,             # < 1.5 (Pass)
            'targetMeanPrice': 120.0,    # > 100 (Pass)
            'currentPrice': 100.0
        }
        mock_ticker.return_value.info = mock_info

        card = self.strategy.analyze("AAPL")
        
        self.assertEqual(card.overall_status, OverallStatus.PASS.value)
        self.assertTrue(card.solvency_check['is_passing'])
        self.assertTrue(card.quality_check['is_passing'])
        self.assertTrue(card.valuation_check['is_passing'])
        self.assertEqual(len(card.red_flags), 0)

    @patch('garp_strategy.yf.Ticker')
    @patch('garp_strategy.fetch_and_analyze')
    def test_high_debt_fail(self, mock_fetch, mock_ticker):
        """Test a stock that fails solvency check."""
        mock_fetch.return_value = {'price': 100.0}
        mock_info = {
            'debtToEquity': 300,         # > 200 (Fail)
            'currentRatio': 0.5,         # < 1.0 (Fail)
            'returnOnEquity': 0.20,
            'grossMargins': 0.50,
            'pegRatio': 1.0,
            'targetMeanPrice': 120.0
        }
        mock_ticker.return_value.info = mock_info

        card = self.strategy.analyze("FAIL")
        
        self.assertEqual(card.overall_status, OverallStatus.REJECT.value)
        self.assertFalse(card.solvency_check['is_passing'])
        self.assertIn("🔴 High Debt", card.red_flags)

    @patch('garp_strategy.yf.Ticker')
    @patch('garp_strategy.fetch_and_analyze')
    def test_overvalued_watchlist(self, mock_fetch, mock_ticker):
        """Test a stock that is good quality but overvalued (Watchlist)."""
        mock_fetch.return_value = {'price': 100.0}
        mock_info = {
            'debtToEquity': 50,
            'currentRatio': 2.0,
            'returnOnEquity': 0.20,      # Good Quality
            'grossMargins': 0.50,
            'pegRatio': 2.0,             # > 1.5 (Fail Valuation)
            'targetMeanPrice': 90.0      # Overpriced
        }
        mock_ticker.return_value.info = mock_info

        card = self.strategy.analyze("WATCH")
        
        self.assertEqual(card.overall_status, OverallStatus.WATCHLIST.value)
        self.assertTrue(card.quality_check['is_passing'])
        self.assertFalse(card.valuation_check['is_passing'])

if __name__ == '__main__':
    unittest.main()
