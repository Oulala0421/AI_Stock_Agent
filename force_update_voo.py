from scripts.update_daily import main
from database_manager import DatabaseManager
from garp_strategy import GARPStrategy
from data_models import StockHealthCard
import logging

# Configure logging to stdout
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def force_param_check():
    # Verify Data Model Runtime
    try:
        c = StockHealthCard(symbol="TEST", price=100.0, sparkline=[1,2,3])
        print(f"✅ DataModel accepts sparkline: {c.sparkline}")
    except TypeError as e:
        print(f"❌ DataModel Failed: {e}")

def force_update():
    # Manual update for VOO
    s = GARPStrategy()
    card = s.analyze("VOO")
    print(f"Card Sparkline Len: {len(card.sparkline)}")
    
    if len(card.sparkline) > 0:
        db = DatabaseManager()
        db.save_daily_snapshot(card, "Force Update Report")
        print("Saved to DB.")
    else:
        print("Card sparkline empty, not saving.")

if __name__ == "__main__":
    force_param_check()
    force_update()
