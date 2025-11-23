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

    def __post_init__(self):
        """
        Validate that overall_status is a valid enum value.
        """
        if self.overall_status not in [status.value for status in OverallStatus]:
            raise ValueError(f"Invalid overall_status: {self.overall_status}")
