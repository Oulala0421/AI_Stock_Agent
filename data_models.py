from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

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

