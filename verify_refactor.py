import unittest
import os
import sys
from unittest.mock import MagicMock, patch

# Ensure imports work
try:
    from config import Config
    from news_agent import NewsAgent
    from analysis_engine import AnalysisEngine
    from data_models import StockHealthCard, OverallStatus
except ImportError as e:
    print(f"❌ Import Failed: {e}")
    sys.exit(1)

class TestArchitecture(unittest.TestCase):
    
    def test_1_config_singleton(self):
        """Test Config Lazy Loading"""
        print("\n🧪 Testing Config Logic...")
        # Config.get should work
        val = Config.get("TOTAL_CAPITAL")
        self.assertIsNotNone(val)
        print(f"   Config loaded capital: {val}")
        
    def test_2_news_agent_prompts(self):
        """Test NewsAgent loads prompts from YAML"""
        print("\n🧪 Testing NewsAgent Prompts...")
        # Patch init to avoid Gemini connection
        with patch('google.generativeai.configure'), \
             patch('google.generativeai.GenerativeModel'):
            agent = NewsAgent()
            # Check if prompts loaded
            self.assertIsInstance(agent.prompts, dict)
            self.assertIn('stock_analysis', agent.prompts)
            self.assertIn('market_outlook', agent.prompts)
            print("   ✅ Prompts loaded from YAML successfully")

    def test_3_stock_health_card_logic(self):
        """Test Business Logic in StockHealthCard"""
        print("\n🧪 Testing StockHealthCard Logic...")
        card = StockHealthCard(symbol="TEST", price=100.0, overall_status="PASS")
        
        # Test Valuation Status
        # Case 1: Undervalued
        card.valuation_check['dcf'] = {'intrinsic_value': 150.0} # MoS = +50%
        self.assertEqual(card.get_valuation_status(), "✅深度低估")
        
        # Case 2: Overvalued
        card.valuation_check['dcf'] = {'intrinsic_value': 50.0} # MoS = -50%
        self.assertEqual(card.get_valuation_status(), "⚠️嚴重高估")
        
        # Test Trend
        card.predicted_return_1w = 3.0
        self.assertEqual(card.get_trend_status(), "🚀強勢看漲")
        card.predicted_return_1w = -2.5
        self.assertEqual(card.get_trend_status(), "⚠️強勢看跌")
        
        # Test Market Mood
        card.valuation_check['tags'] = ["Z=2.0"]
        self.assertEqual(card.get_market_mood(), "🔥市場過熱")
        
        card.valuation_check['tags'] = ["Z=-2.0"]
        self.assertEqual(card.get_market_mood(), "❄️市場恐慌")
        
        card.valuation_check['tags'] = ["Z=0.0"]
        self.assertEqual(card.get_market_mood(), "☁️情緒中性")
        
        print("   ✅ Logic methods verified")

    def test_4_analysis_engine_init(self):
        """Test AnalysisEngine Initialization"""
        print("\n🧪 Testing AnalysisEngine...")
        engine = AnalysisEngine(strategy=MagicMock())
        self.assertIsInstance(engine, AnalysisEngine)
        print("   ✅ AnalysisEngine instantiated")

if __name__ == '__main__':
    unittest.main()
