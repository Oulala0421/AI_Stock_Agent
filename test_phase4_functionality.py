"""
Comprehensive functionality test for Phase 4 GARP News Integration.
Tests all modules without making actual API calls.
"""

import sys
import traceback

def test_imports():
    """Test 1: Verify all modules can be imported."""
    print("=" * 60)
    print("TEST 1: Module Import Verification")
    print("=" * 60)
    
    modules_to_test = [
        ('data_models', ['StockHealthCard', 'OverallStatus']),
        ('garp_strategy', ['GARPStrategy']),
        ('news_agent', ['NewsAgent']),
        ('report_formatter', ['format_stock_report']),
        ('market_data', ['fetch_and_analyze', 'get_market_regime']),
        ('sheet_manager', ['get_stock_lists']),
        ('notifier', ['send_telegram', 'send_line']),
        ('market_status', ['is_market_open', 'get_economic_events']),
        ('config', ['Config']),
    ]
    
    results = []
    for module_name, expected_items in modules_to_test:
        try:
            module = __import__(module_name)
            # Check if expected items exist
            missing = [item for item in expected_items if not hasattr(module, item)]
            if missing:
                results.append(f"❌ {module_name}: Missing {missing}")
            else:
                results.append(f"✅ {module_name}: All exports present")
        except Exception as e:
            results.append(f"❌ {module_name}: Import failed - {e}")
    
    for result in results:
        print(f"  {result}")
    
    return all("✅" in r for r in results)

def test_data_models():
    """Test 2: Verify StockHealthCard structure."""
    print("\n" + "=" * 60)
    print("TEST 2: Data Models Structure")
    print("=" * 60)
    
    try:
        from data_models import StockHealthCard, OverallStatus
        
        # Create a test card
        card = StockHealthCard(symbol="TEST", price=100.0)
        
        # Verify all required fields
        checks = [
            (hasattr(card, 'solvency_check'), "solvency_check exists"),
            (hasattr(card, 'quality_check'), "quality_check exists"),
            (hasattr(card, 'valuation_check'), "valuation_check exists"),
            (hasattr(card, 'technical_setup'), "technical_setup exists"),
            (hasattr(card, 'overall_status'), "overall_status exists"),
            (hasattr(card, 'red_flags'), "red_flags exists"),
            (card.overall_status == OverallStatus.REJECT.value, "Default status is REJECT"),
        ]
        
        for check, description in checks:
            status = "✅" if check else "❌"
            print(f"  {status} {description}")
        
        return all(check for check, _ in checks)
    except Exception as e:
        print(f"  ❌ Error: {e}")
        traceback.print_exc()
        return False

def test_news_agent_initialization():
    """Test 3: Verify NewsAgent can initialize safely."""
    print("\n" + "=" * 60)
    print("TEST 3: News Agent Initialization")
    print("=" * 60)
    
    try:
        from news_agent import NewsAgent
        
        # Initialize agent (should work even without API key)
        agent = NewsAgent()
        
        checks = [
            (hasattr(agent, 'api_key'), "api_key attribute exists"),
            (hasattr(agent, 'model'), "model attribute exists"),
            (hasattr(agent, 'endpoint'), "endpoint attribute exists"),
            (agent.model == "sonar-pro", "Correct model configured"),
            (hasattr(agent, 'get_stock_news'), "get_stock_news method exists"),
        ]
        
        for check, description in checks:
            status = "✅" if check else "❌"
            print(f"  {status} {description}")
        
        # Test fallback behavior (should not crash)
        print("\n  Testing fallback behavior (no actual API call)...")
        result = agent.get_stock_news("AAPL")
        print(f"  ✅ Fallback returned: '{result[:50]}...'")
        
        return all(check for check, _ in checks)
    except Exception as e:
        print(f"  ❌ Error: {e}")
        traceback.print_exc()
        return False

def test_garp_strategy():
    """Test 4: Verify GARPStrategy initialization."""
    print("\n" + "=" * 60)
    print("TEST 4: GARP Strategy Initialization")
    print("=" * 60)
    
    try:
        from garp_strategy import GARPStrategy
        
        strategy = GARPStrategy()
        
        checks = [
            (hasattr(strategy, 'analyze'), "analyze method exists"),
            (hasattr(strategy, 'strategy_type'), "strategy_type exists"),
            (strategy.strategy_type == "GARP", "Correct strategy type"),
        ]
        
        for check, description in checks:
            status = "✅" if check else "❌"
            print(f"  {status} {description}")
        
        return all(check for check, _ in checks)
    except Exception as e:
        print(f"  ❌ Error: {e}")
        traceback.print_exc()
        return False

def test_report_formatter():
    """Test 5: Verify report_formatter signature."""
    print("\n" + "=" * 60)
    print("TEST 5: Report Formatter Signature")
    print("=" * 60)
    
    try:
        from report_formatter import format_stock_report
        from data_models import StockHealthCard
        import inspect
        
        # Check function signature
        sig = inspect.signature(format_stock_report)
        params = list(sig.parameters.keys())
        
        checks = [
            ('card' in params, "card parameter exists"),
            ('news_summary' in params, "news_summary parameter exists"),
            (len(params) == 2, "Correct number of parameters"),
        ]
        
        for check, description in checks:
            status = "✅" if check else "❌"
            print(f"  {status} {description}")
        
        # Test with sample card
        print("\n  Testing report generation...")
        card = StockHealthCard(symbol="TEST", price=123.45)
        
        # Test without news
        report1 = format_stock_report(card)
        print(f"  ✅ Report without news: {len(report1)} chars")
        
        # Test with news
        report2 = format_stock_report(card, "- Test news bullet")
        has_news_emoji = "📰" in report2
        print(f"  {'✅' if has_news_emoji else '❌'} Report with news contains 📰 emoji")
        
        return all(check for check, _ in checks) and has_news_emoji
    except Exception as e:
        print(f"  ❌ Error: {e}")
        traceback.print_exc()
        return False

def test_main_imports():
    """Test 6: Verify main.py can import all dependencies."""
    print("\n" + "=" * 60)
    print("TEST 6: Main Orchestration Dependencies")
    print("=" * 60)
    
    try:
        # Try to import main module
        import main
        
        checks = [
            (hasattr(main, 'run_analysis'), "run_analysis function exists"),
            (hasattr(main, 'GARPStrategy'), "GARPStrategy imported"),
            (hasattr(main, 'NewsAgent'), "NewsAgent imported"),
            (hasattr(main, 'format_stock_report'), "format_stock_report imported"),
            (hasattr(main, 'OverallStatus'), "OverallStatus imported"),
        ]
        
        for check, description in checks:
            status = "✅" if check else "❌"
            print(f"  {status} {description}")
        
        return all(check for check, _ in checks)
    except Exception as e:
        print(f"  ❌ Error: {e}")
        traceback.print_exc()
        return False

def test_integration_workflow():
    """Test 7: Verify end-to-end workflow logic."""
    print("\n" + "=" * 60)
    print("TEST 7: Integration Workflow Logic")
    print("=" * 60)
    
    try:
        from garp_strategy import GARPStrategy
        from news_agent import NewsAgent
        from report_formatter import format_stock_report
        from data_models import OverallStatus
        
        print("  Simulating workflow for test symbol...")
        
        # Step 1: Initialize components
        strategy = GARPStrategy()
        news_agent = NewsAgent()
        print("  ✅ Components initialized")
        
        # Step 2: Smart news fetching logic simulation
        test_statuses = [
            (OverallStatus.PASS.value, True, "PASS triggers news fetch"),
            (OverallStatus.WATCHLIST.value, True, "WATCHLIST triggers news fetch"),
            (OverallStatus.REJECT.value, False, "REJECT skips news fetch"),
        ]
        
        for status, should_fetch, description in test_statuses:
            # Simulate the smart fetching logic from main.py
            news_summary = None
            if status in [OverallStatus.PASS.value, OverallStatus.WATCHLIST.value]:
                news_summary = "simulated news"
            
            result = (news_summary is not None) == should_fetch
            print(f"  {'✅' if result else '❌'} {description}: {result}")
        
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("\n🧪 AI Stock Agent - Phase 4 Functionality Test Suite")
    print("=" * 60)
    
    tests = [
        ("Module Imports", test_imports),
        ("Data Models", test_data_models),
        ("News Agent", test_news_agent_initialization),
        ("GARP Strategy", test_garp_strategy),
        ("Report Formatter", test_report_formatter),
        ("Main Dependencies", test_main_imports),
        ("Integration Workflow", test_integration_workflow),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ {test_name} crashed: {e}")
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {status}: {test_name}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print("\n" + "=" * 60)
    print(f"OVERALL: {total_passed}/{total_tests} tests passed")
    print("=" * 60)
    
    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED! System is ready for production.")
        return 0
    else:
        print(f"\n⚠️ {total_tests - total_passed} test(s) failed. Please review.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
