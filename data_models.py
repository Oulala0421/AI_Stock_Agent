from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
from constants import Emojis

class OverallStatus(Enum):
    PASS = "PASS"
    WATCHLIST = "WATCHLIST"
    REJECT = "REJECT"

@dataclass
class StockHealthCard:
    """
    A data class to strictly structure the stock analysis output for the GARP strategy.
    It serves as a "Health Card" for each stock, containing checks for solvency, quality,
    valuation, and technical setup, along with an overall status.
    """
    symbol: str
    price: float
    strategy_type: str = "GARP"
    sector: Optional[str] = None # [New] For Concentration Risk Check
    sparkline: List[float] = field(default_factory=list) # [New] Persist sparkline data
    
    # Solvency Check: Contains debt_to_equity, current_ratio, is_passing (bool), tags (list of strings)
    solvency_check: Dict = field(default_factory=lambda: {
        "debt_to_equity": None,
        "current_ratio": None,
        "is_passing": False,
        "tags": []
    })
    
    # Quality Check: Contains roe, gross_margin, is_passing (bool), tags (list of strings)
    quality_check: Dict = field(default_factory=lambda: {
        "roe": None,
        "gross_margin": None,
        "is_passing": False,
        "tags": []
    })
    
    # Valuation Check: Contains pe_ratio, peg_ratio, fair_value, margin_of_safety, tags (list of strings)
    valuation_check: Dict = field(default_factory=lambda: {
        "pe_ratio": None,
        "peg_ratio": None,
        "fair_value": None,
        "margin_of_safety": None,
        "tags": []
    })
    
    # Technical Setup: Contains rsi, trend_status (Bull/Bear), tags
    technical_setup: Dict = field(default_factory=lambda: {
        "rsi": None,
        "trend_status": None,
        "tags": []
    })
    
    # Overall Status: "PASS", "WATCHLIST", or "REJECT"
    overall_status: str = OverallStatus.REJECT.value
    
    # Red Flags: A consolidated list of all severe warning tags
    red_flags: List[str] = field(default_factory=list)

    # Advanced Metrics: Piotroski F-Score (0-9), Altman Z-Score, FCF Yield, News Sentiment
    advanced_metrics: Dict = field(default_factory=lambda: {
        "piotroski_score": None,
        "altman_z_score": None,
        "fcf_yield": None,
        "news_analysis": None, # {sentiment, confidence, summary_reason}
        "tags": []
    })
    
    # Private Personalization Notes (e.g., Concentration Warning)
    private_notes: List[str] = field(default_factory=list)
    
    # === Price Prediction Fields (Sprint 1 Extension) ===
    # AI-driven price forecasting and Monte Carlo simulation results
    predicted_return_1w: Optional[float] = None  # 1-week predicted return (%)
    predicted_return_1m: Optional[float] = None  # 1-month predicted return (%)
    confidence_score: Optional[float] = None     # AI confidence score (0.0 - 1.0)
    monte_carlo_min: Optional[float] = None      # Pessimistic scenario price
    monte_carlo_max: Optional[float] = None      # Optimistic scenario price

    def __post_init__(self):
        """
        Validate that overall_status is a valid enum value.
        """
        if self.overall_status not in [status.value for status in OverallStatus]:
            raise ValueError(f"Invalid overall_status: {self.overall_status}")

    # === Presentation Logic ===
    
    def get_valuation_status(self) -> str:
        """Determine valuation status based on DCF Margin of Safety"""
        dcf_data = self.valuation_check.get('dcf', {})
        intrinsic_val = dcf_data.get('intrinsic_value') if dcf_data else None
        
        if not intrinsic_val or intrinsic_val <= 0:
            return f"{Emojis.FAIR}合理" # Default if no data
            
        mos = (intrinsic_val - self.price) / self.price
        
        if mos < -0.2:
            return f"{Emojis.OVERVALUED_SEVERE}嚴重高估"
        elif mos < -0.1:
            return f"{Emojis.OVERVALUED}高估"
        elif mos > 0.2:
            return f"{Emojis.UNDERVALUED_DEEP}深度低估"
        elif mos > 0.1:
            return f"{Emojis.UNDERVALUED}低估"
        else:
            return f"{Emojis.FAIR}合理"

    def get_trend_status(self) -> str:
        """Determine trend direction based on predicted return"""
        val = self.predicted_return_1w
        if val is None: return f"{Emojis.FLAT}持平"
        
        if val > 2.0: return f"{Emojis.ROCKET}強勢看漲"
        if val > 0.5: return f"{Emojis.UP}看漲"
        if val > -0.5: return f"{Emojis.FLAT}持平"
        if val > -2.0: return f"{Emojis.DOWN}看跌"
        return f"{Emojis.WARN}強勢看跌"

    def get_confidence_label(self) -> str:
        """Determine AI confidence level"""
        conf = self.confidence_score or 0.5
        if conf > 0.7: return "高"
        if conf > 0.5: return "中"
        return "低"

    def get_market_mood(self) -> str:
        """Parse Z-Score tag to determine market mood"""
        # Parse Z-Score from tags if not available elsewhere
        z_score = 0.0
        import re
        for tag in self.valuation_check.get('tags', []):
            if "Z=" in tag:
                match = re.search(r"Z=([-\d\.]+)", tag)
                if match:
                    z_score = float(match.group(1))
                    break
        
        if z_score > 1.5: return f"{Emojis.OVERHEATED}市場過熱"
        if z_score < -1.5: return f"{Emojis.PANIC}市場恐慌"
        return f"{Emojis.CLOUD}情緒中性"


