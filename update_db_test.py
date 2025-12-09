from database_manager import DatabaseManager
from datetime import datetime

# Initialize DB
db = DatabaseManager()

# Mock NVDA Card Data with Prediction
mock_card = {
    'symbol': 'NVDA',
    'price': 135.50,
    'strategy_type': 'GARP',
    'overall_status': 'PASS',
    'confidence_score': 0.85,
    'predicted_return_1w': 3.14159, # Distinctive number to verify
    'summary_reason': 'Regime-Based Bootstrap Test Injection',
    'quality_check': {'roe': 0.45, 'is_passing': True},
    'valuation_check': {'peg_ratio': 1.2, 'is_passing': True},
    'raw_data': {
        'predicted_return_1w': 3.14159,
        'confidence_score': 0.85,
        'summary_reason': 'End-to-End Test Verification Data'
    },
    'last_updated': datetime.now()
}

# Update Record
print("Updating NVDA with test prediction data...")
db.save_daily_snapshot(type("obj", (object,), mock_card), "Test Report") # Mock object
print("Update complete.")
