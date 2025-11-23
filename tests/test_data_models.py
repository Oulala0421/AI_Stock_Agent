import unittest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data_models import StockHealthCard, OverallStatus

class TestStockHealthCard(unittest.TestCase):
    def test_initialization(self):
        """Test that the StockHealthCard can be initialized with required fields."""
        card = StockHealthCard(symbol="AAPL", price=150.0)
        self.assertEqual(card.symbol, "AAPL")
        self.assertEqual(card.price, 150.0)
        self.assertEqual(card.strategy_type, "GARP")
        self.assertEqual(card.overall_status, "REJECT") # Default
        self.assertIsInstance(card.solvency_check, dict)
        self.assertIsInstance(card.quality_check, dict)
        self.assertIsInstance(card.valuation_check, dict)
        self.assertIsInstance(card.technical_setup, dict)
        self.assertIsInstance(card.red_flags, list)

    def test_custom_values(self):
        """Test initialization with custom values."""
        card = StockHealthCard(
            symbol="GOOGL",
            price=2800.0,
            overall_status=OverallStatus.PASS.value,
            solvency_check={"is_passing": True},
            red_flags=["High Debt"]
        )
        self.assertEqual(card.symbol, "GOOGL")
        self.assertEqual(card.overall_status, "PASS")
        self.assertEqual(card.solvency_check["is_passing"], True)
        self.assertEqual(card.red_flags, ["High Debt"])

    def test_invalid_status(self):
        """Test that invalid overall_status raises ValueError."""
        with self.assertRaises(ValueError):
            StockHealthCard(symbol="TSLA", price=900.0, overall_status="MAYBE")

if __name__ == '__main__':
    unittest.main()
