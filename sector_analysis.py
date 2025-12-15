
import logging
from config import Config
# from data_adapter import DataAdapter # Future: Fetch sector agg from data provider

logger = logging.getLogger(__name__)

class SectorAnalysis:
    """
    Provides Sector-Neutral Valuation Metrics.
    Calculates Relative Z-Score for valuation ratios (PE, PEG) vs Sector Peers.
    """
    
    def __init__(self):
        self.sector_stats_cache = {}
        # In a real scenario, we'd fetch these from OpenBB/FMP.
        # For Phase 15 prototype, we define "Hardcoded Base Rates" per sector 
        # based on typical historical averages (mock data).
        self.sector_benchmarks = {
            "Technology": {"avg_pe": 35.0, "std_pe": 10.0, "avg_peg": 1.8, "std_peg": 0.5},
            "Financial Services": {"avg_pe": 12.0, "std_pe": 3.0, "avg_peg": 1.0, "std_peg": 0.3},
            "Healthcare": {"avg_pe": 25.0, "std_pe": 8.0, "avg_peg": 2.0, "std_peg": 0.6},
            "Consumer Cyclical": {"avg_pe": 20.0, "std_pe": 6.0, "avg_peg": 1.5, "std_peg": 0.4},
            "Industrials": {"avg_pe": 18.0, "std_pe": 5.0, "avg_peg": 1.4, "std_peg": 0.4},
            # Default fallback
            "Unknown": {"avg_pe": 20.0, "std_pe": 10.0, "avg_peg": 1.5, "std_peg": 0.5}
        }

    def get_sector_stats(self, sector: str):
        """
        Returns {avg_pe, std_pe, avg_peg, std_peg} for the sector.
        """
        return self.sector_benchmarks.get(sector, self.sector_benchmarks["Unknown"])

    def calculate_sector_z_score(self, sector: str, metric_name: str, metric_value: float) -> float:
        """
        Calculates Z-Score of a stock's metric relative to its sector.
        Z = (Value - Mean) / StdDev
        
        Args:
            sector (str): Sector name (e.g. "Technology")
            metric_name (str): "pe" or "peg"
            metric_value (float): The stock's PE or PEG
        
        Returns:
            float: Z-Score. Negative means "Cheaper than peers".
        """
        if metric_value is None:
            return 0.0
            
        stats = self.get_sector_stats(sector)
        
        if metric_name.lower() == 'pe':
            avg = stats['avg_pe']
            std = stats['std_pe']
        elif metric_name.lower() == 'peg':
            avg = stats['avg_peg']
            std = stats['std_peg']
        else:
            return 0.0
            
        if std == 0: return 0.0
        
        z_score = (metric_value - avg) / std
        return z_score
