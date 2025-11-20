import os
import yaml
from dotenv import load_dotenv

load_dotenv()

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print("⚠️ config.yaml not found, using defaults")
        config = {}

    # System Defaults
    system = config.get('system', {})
    TOTAL_CAPITAL = system.get('total_capital', 17000)
    MAX_RISK_PCT = system.get('max_risk_pct', 0.015)
    
    # API Keys (Load from Env)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    TG_TOKEN = os.getenv("TG_TOKEN")
    TG_CHAT_ID = os.getenv("TG_CHAT_ID")
    LINE_TOKEN = os.getenv("LINE_TOKEN")
    LINE_USER_ID = os.getenv("LINE_USER_ID")
    
    return {
        "TOTAL_CAPITAL": TOTAL_CAPITAL,
        "MAX_RISK_PCT": MAX_RISK_PCT,
        "GEMINI_API_KEY": GEMINI_API_KEY,
        "TG_TOKEN": TG_TOKEN,
        "TG_CHAT_ID": TG_CHAT_ID,
        "LINE_TOKEN": LINE_TOKEN,
        "LINE_USER_ID": LINE_USER_ID,
        "STRATEGY": config.get('strategy', {})
    }

# Singleton instance
Config = load_config()
