
import unittest
from unittest.mock import patch
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from market_status import is_market_open
from report_formatter import format_minimal_report
from constants import Emojis

class TestMarketClosedRefinement(unittest.TestCase):
    
    def test_is_market_open_tuple_return(self):
        print("\n🧪 Testing is_market_open tuple return...")
        is_open, reason = is_market_open()
        self.assertIsInstance(is_open, bool)
        self.assertIsInstance(reason, str)
        print(f"   ✅ Return: ({is_open}, '{reason}')")

    def test_report_macros_removed(self):
        print("\n🧪 Testing 'Risk On' removed from report...")
        # Mock macro status "RISK_ON" passed in, should NOT be in output
        report = format_minimal_report({}, [], macro_status="RISK_ON 🚀", market_is_open=(True, "Open"))
        
        self.assertNotIn("宏觀: RISK_ON", report)
        print("   ✅ Macro Status line successfully removed.")

    def test_market_closed_reason_display(self):
        print("\n🧪 Testing Market Closed Reason display...")
        # Mock closed with specific reason
        reason_str = "國定假日 (Test Holiday)"
        report = format_minimal_report({}, [], market_is_open=(False, reason_str))
        
        self.assertIn("今日美股休市", report)
        self.assertIn(f"原因: {reason_str}", report)
        print("   ✅ Market Closed Reason displayed correctly.")

if __name__ == '__main__':
    unittest.main()
