
import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from datetime import datetime
import json

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from market_status import calculate_macro_status
from constants import Emojis
from config import Configuration
from advanced_metrics import AdvancedFinancials
from google_news_searcher import GoogleNewsSearcher

class TestSystemHardening(unittest.TestCase):
    
    def test_macro_status_logic(self):
        print("\n🧪 Testing Macro Logic...")
        # RISK ON
        status = calculate_macro_status({'vix': 15, 'is_bullish': True})
        self.assertIn("RISK_ON", status)
        self.assertIn(Emojis.ROCKET, status)
        print(f"   ✅ Risk On: {status}")
        
        # RISK OFF
        status = calculate_macro_status({'vix': 30, 'is_bullish': False})
        self.assertIn("RISK_OFF", status)
        self.assertIn(Emojis.SHIELD, status)
        print(f"   ✅ Risk Off: {status}")

    def test_config_validation(self):
        print("\n🧪 Testing Config Validation...")
        # Mock loading bad values
        with patch.dict(os.environ, {}):
            with patch('config.yaml.safe_load', return_value={'system': {'total_capital': -100, 'max_risk_pct': 5.0}}):
                # Trigger reload logic (simulated)
                # We can't easily standard-patch a class method's internal file read without refactoring the class to accept a dict.
                # However, we can test validation logic if we could inject it.
                # Configuration._load_from_file reads directly.
                # Let's inspect the results of _load_from_file by mocking open/yaml
                pass 
                # Since Config is already loaded, we might skip deep testing here and rely on manual verify.
                # Or we call _load_from_file() directly.
                
                # Let's allow prints to happen
                data = Configuration._load_from_file()
                
                # Check resets
                self.assertEqual(data['TOTAL_CAPITAL'], 17000.0) # Should reset from -100
                self.assertEqual(data['MAX_RISK_PCT'], 0.015) # Should reset from 5.0 (if logic was < 1.0)
                print("   ✅ Config Validation Reset Invalid Values")

    def test_graham_number_fallback(self):
        print("\n🧪 Testing Graham Number Fallback...")
        # Mock Ticker and Financials
        mock_ticker = MagicMock()
        mock_ticker.info = {'sharesOutstanding': 100}
        
        # Create DataFrames simulating Negative FCF but Positive Earnings
        # Create DataFrames simulating Negative FCF but Positive Earnings
        
        # Let's reconstruct properly as yfinance does
        # Index: Metrics, Columns: Dates
        dates = pd.to_datetime(['2024-01-01', '2023-01-01'])
        
        mock_ticker.cashflow = pd.DataFrame(
            [[-500, -100]], 
            index=['Free Cash Flow'], 
            columns=dates
        )
        
        mock_ticker.financials = pd.DataFrame(
            [[1000, 800], [5000, 4000]],
            index=['Net Income', 'Total Revenue'],
            columns=dates
        )
        
        mock_ticker.balance_sheet = pd.DataFrame(
            [[2000, 1800], [100, 100]],
            index=['Stockholders Equity', 'Ordinary Shares Number'],
            columns=dates
        )
        
        adv = AdvancedFinancials(mock_ticker)
        
        # Test DCF Fallback
        # Sentinel Z-Score = 0
        res = adv.calculate_sentiment_adjusted_dcf(0.0)
        
        # Graham Number = Sqrt(22.5 * EPS * BVPS)
        # EPS = 1000 / 100 = 10
        # BVPS = 2000 / 100 = 20
        # GN = Sqrt(22.5 * 10 * 20) = Sqrt(4500) ≈ 67.08
        
        self.assertIsNotNone(res['intrinsic_value'])
        self.assertIn("Graham Number", res['details'])
        self.assertAlmostEqual(res['intrinsic_value'], 67.08, delta=0.1)
        print(f"   ✅ Graham Number Calculated: {res['intrinsic_value']:.2f}")

    def test_news_caching(self):
        print("\n🧪 Testing News Caching...")
        searcher = GoogleNewsSearcher()
        searcher.cache_file = "test_cache.json"
        
        # Clear test cache
        if os.path.exists(searcher.cache_file):
            os.remove(searcher.cache_file)
            
        # 1. Mock Search
        # Must patch 'google_news_searcher.GoogleSearch' since that's where it's imported
        with patch('google_news_searcher.GoogleSearch') as MockSearch:
            mock_inst = MockSearch.return_value
            mock_inst.get_dict.return_value = {
                "news_results": [
                    {"title": "Test News", "date": "1 hour ago", "source": "CNBC"}
                ]
            }
            
            # First Run (Miss)
            res1 = searcher.search_news("TEST", days=1)
            self.assertEqual(len(res1), 1)
            self.assertTrue(os.path.exists(searcher.cache_file))
            print("   ✅ Cache Miss: Fetched and Saved")
            
            # Second Run (Hit) without Mock (Should skip API)
            # We enforce Mock again to ensure it WOULD return something different if called
            mock_inst.get_dict.return_value = { "news_results": [] } # Should not be called
            
            res2 = searcher.search_news("TEST", days=1)
            self.assertEqual(len(res2), 1) # Should still return 1 form cache
            self.assertEqual(res2[0]['title'], "Test News")
            print("   ✅ Cache Hit: Returned valid data without API")
            
        # Cleanup
        if os.path.exists(searcher.cache_file):
            os.remove(searcher.cache_file)

if __name__ == '__main__':
    unittest.main()
