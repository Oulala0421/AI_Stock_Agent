import os
import yaml
from dotenv import load_dotenv

# Load env immediately for os.getenv availability (standard practice)
load_dotenv()

class Configuration:
    """
    Lazy Singleton Configuration Manager
    Loads config.yaml only on first access to 'get'.
    """
    _data = None

    @classmethod
    def _ensure_loaded(cls):
        if cls._data is None:
            cls._data = cls._load_from_file()

    @classmethod
    def _load_from_file(cls):
        config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
        config = {}
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
        except FileNotFoundError:
            print("⚠️ config.yaml not found, using defaults")
        
        # System Defaults & Validation
        system = config.get('system', {})
        try:
            total_capital = float(system.get('total_capital', 17000))
            max_risk = float(system.get('max_risk_pct', 0.015))
        except (ValueError, TypeError):
            print("⚠️ Config Type Error: defaulting capital/risk")
            total_capital = 17000.0
            total_capital = 17000.0
            max_risk = 0.015
            
        # Validation Logic (Robustness: Phase 12.3)
        if total_capital <= 0:
            print("⚠️ Config Error: Total Capital must be positive. Resetting to 17000.")
            total_capital = 17000.0
            
        if not (0.0 < max_risk < 1.0):
             print("⚠️ Config Error: Max Risk % should be between 0 and 1. Resetting to 0.015 (1.5%).")
             max_risk = 0.015

        # API Keys (Priority: Env > Config > None)
        return {
            "TOTAL_CAPITAL": total_capital,
            "MAX_RISK_PCT": max_risk,
            
            # APIs
            "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY") or config.get('GEMINI_API_KEY'),
            "PERPLEXITY_API_KEY": os.getenv("PERPLEXITY_API_KEY"),
            "SERPAPI_API_KEY": os.getenv("SERPAPI_API_KEY"),
            "TG_TOKEN": os.getenv("TG_TOKEN"),
            "TG_CHAT_ID": os.getenv("TG_CHAT_ID"),
            "LINE_TOKEN": os.getenv("LINE_TOKEN"),
            "LINE_USER_ID": os.getenv("LINE_USER_ID"),
            "LINE_GROUP_ID": os.getenv("LINE_GROUP_ID"),
            
            # Database
            "MONGODB_URI": os.getenv("MONGODB_URI"),
            
            # Dashboard
            "DASHBOARD_URL": os.getenv("DASHBOARD_URL"),

            # Complex Objects
            "STRATEGY": config.get('strategy', {}),
            "GARP": config.get('garp', {}),
            "MARKET": config.get('market', {}),
            "CAPITAL_ALLOCATION": config.get('capital_allocation', {}),
            "POSITION_LIMITS": config.get('position_limits', {}),
            
            # AI Configuration
            "AI_MODEL": os.getenv("AI_MODEL", "gemini-2.5-flash"),
            "AI_MODEL_FALLBACK": os.getenv("AI_MODEL_FALLBACK", "gemini-2.0-flash")
        }

    @classmethod
    def get(cls, key, default=None):
        """Get configuration value safe-ly"""
        cls._ensure_loaded()
        return cls._data.get(key, default)

    @classmethod
    def reload(cls):
        """Force reload of configuration"""
        cls._data = cls._load_from_file()

# Expose as 'Config' matching existing interface
Config = Configuration
