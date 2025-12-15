import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import unittest
from unittest.mock import MagicMock, patch
from advanced_metrics import AdvancedFinancials
from garp_strategy import GARPStrategy
from data_models import StockHealthCard, OverallStatus

class TestCalibrationLogic(unittest.TestCase):

    def setUp(self):
        # Mock Financials (Orient: Index=Metrics, Columns=Dates)
        self.mock_bs = pd.DataFrame({
            '2023-12-31': [1000, 400, 100, 500, 1000],  # Shares, Liab, Assets, Equity, Assets for Graham
            '2022-12-31': [900, 500, 100, 400, 900]
        }, index=['Total Assets', 'Total Liabilities Net Minority Interest', 'Ordinary Shares Number', 'Stockholders Equity', 'Working Capital'])
        
        self.mock_inc = pd.DataFrame({
            '2023-12-31': [100, 2000, 200, 100],
            '2022-12-31': [80, 1800, 150, 80]
        }, index=['Net Income', 'Total Revenue', 'EBIT', 'Gross Profit'])
        
        self.mock_cf = pd.DataFrame({
            '2023-12-31': [200, -50, 150],
            '2022-12-31': [180, -40, 140]
        }, index=['Operating Cash Flow', 'Capital Expenditure', 'Free Cash Flow'])
        
        self.mock_info = {'sharesOutstanding': 100, 'revenueGrowth': 0.40, 'sector': 'Technology'} # 40% Growth
        self.adv = AdvancedFinancials('TEST', self.mock_bs, self.mock_inc, self.mock_cf, self.mock_info)
        
        # Mock Strategy
        self.strategy = GARPStrategy()
        self.strategy.thresholds = {'max_pe': 25, 'max_peg': 1.0}
        self.strategy.db = MagicMock()

    def test_growth_cap_unlock(self):
        """Test that Technology sector uses 30% growth cap instead of 15%"""
        # Case 1: Technology
        res_tech = self.adv.calculate_sentiment_adjusted_dcf(
            sentiment_z_score=0.0, 
            sector="Technology",
            risk_free_rate=0.04
        )
        growth_tech = res_tech.get('growth_rate')
        self.assertEqual(growth_tech, 0.30, f"Tech Growth should be 30%, got {growth_tech}")
        
        # Case 2: Utilities (Conservative)
        res_util = self.adv.calculate_sentiment_adjusted_dcf(
            sentiment_z_score=0.0, 
            sector="Utilities",
            risk_free_rate=0.04
        )
        growth_util = res_util.get('growth_rate')
        self.assertEqual(growth_util, 0.15, f"Utilities Growth should be 15%, got {growth_util}")

    def test_z_score_clamping(self):
        """Test Z-Score floor and clamping logic in GarP Strategy"""
        # Mock DB returning low std dev (Danger Zone)
        self.strategy.db.get_sentiment_stats.return_value = {'mean': 50.0, 'std_dev': 0.1} 
        
        # Mock sentiment
        self.strategy.get_market_sentiment = MagicMock(return_value=80.0) # Score 80
        
        # We need to access the logic inside _check_valuation (via private method access or mock)
        # Actually, let's just copy the logic snippet since it's hard to isolate _check_valuation due to dependencies
        # OR better, run _check_valuation with mocks
        card = StockHealthCard("TEST", 100.0)
        info = {'trailingPE': 20, 'forwardPE': 15, 'sector': 'Technology'}
        
        # We need to prevent _check_valuation from crashing on missing keys
        # It calls self.get_market_sentiment() internally
        
        self.strategy._check_valuation(card, info, 100.0, self.adv)
        
        # Check Z-Score in logs? Hard.
        # Check PEG limit. If Z-Score was (80-50)/0.1 = 300, PEG would be huge or crashed.
        # With Floor std=5, Z=(80-50)/15 = 2.0 (fallback std=15) OR std=5?
        # Logic: std = max(0.1, 5.0) -> 5.0.
        # Z = (80 - 50) / 5.0 = 6.0
        # Clamp: max(-5, min(5, 6.0)) -> 5.0
        
        # If Z=5.0, Dynamic PEG = 1.0 + 0.2*5 = 2.0
        # Let's check card tags for "Dynamic PEG" value
        tags = str(card.valuation_check['tags'])
        self.assertIn("Z=5.00", tags) # Should see clamped value

    def test_forward_pe_priority(self):
        """Test that reasonable Forward PE passes even if Trailing PE is high"""
        card = StockHealthCard("TEST", 100.0)
        # Trailing 50 (Fail), Forward 20 (Pass, threshold 25)
        info = {'trailingPE': 50, 'forwardPE': 20, 'sector': 'Technology'}
        
        self.strategy.get_market_sentiment = MagicMock(return_value=50.0)
        self.strategy.db.get_sentiment_stats.return_value = {'mean': 50, 'std_dev': 15}
        
        self.strategy._check_valuation(card, info, 100.0, self.adv)
        
        tags = card.valuation_check['tags']
        print(f"Tags: {tags}")
        
        # Should contain "Reasonable Forward PE"
        has_forward_pass = any("Reasonable Forward PE" in t for t in tags)
        self.assertTrue(has_forward_pass, "Should accept based on Forward PE")
        
        # Should NOT be overall failure due to PE
        # But wait, logic: if passed_pe is True, it appends "Reasonable..."
        # If passed_pe is False, it appends "High PE..." and sets is_passing=False
        # So check is_passing
        self.assertTrue(card.valuation_check['is_passing'], "Valuation should pass via Forward PE")

if __name__ == '__main__':
    unittest.main()
