import pandas as pd
import yfinance as yf
import logging
from sheet_manager import get_my_portfolio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PortfolioManager:
    """
    Personalized Risk Manager
    
    Responsibilities:
    1. Check Sector Concentration (avoid over-exposure)
    2. Check Correlation (avoid buying stocks that move identically to top holdings)
    """
    
    def __init__(self, mock_portfolio=None):
        """
        Initialize with real portfolio data.
        mock_portfolio: Optional list for testing purposes.
        """
        self.portfolio = mock_portfolio if mock_portfolio is not None else get_my_portfolio()
        self.total_value = 0.0
        self.sector_allocations = {}
        self.top_holdings = []
        
        self._process_portfolio()
        
    def _process_portfolio(self):
        """
        Pre-calculate portfolio stats: total value, sector map, top holdings.
        """
        if not self.portfolio:
            logger.warning("⚠️ Portfolio is empty or failed to load.")
            return

        for item in self.portfolio:
            value = item['shares'] * item['avg_cost']
            sector = item['sector']
            
            # Asset Allocation
            self.total_value += value
            self.sector_allocations[sector] = self.sector_allocations.get(sector, 0) + value
            
            # Helper for sorting
            item['market_value'] = value
            
        # Identify Top 3 Holdings by Value (for efficient correlation check)
        # We don't want to correlate against 20 stocks, just the big movers.
        sorted_holdings = sorted(self.portfolio, key=lambda x: x['market_value'], reverse=True)
        self.top_holdings = sorted_holdings[:3]
        
        logger.info(f"✅ Portfolio Loaded: Value ${self.total_value:,.2f}, Top 3: {[h['symbol'] for h in self.top_holdings]}")

    def check_concentration(self, new_symbol: str, new_sector: str, threshold_pct: float = 30.0) -> list:
        """
        Check if adding this stock would exacerbate sector concentration.
        Returns a list of warning strings (empty if safe).
        """
        if not self.portfolio: return []
        
        current_sector_val = self.sector_allocations.get(new_sector, 0)
        current_pct = (current_sector_val / self.total_value) * 100 if self.total_value > 0 else 0
        
        warnings = []
        if current_pct > threshold_pct:
            warnings.append(f"⚠️ 板塊集中度過高: {new_sector} 已佔 {current_pct:.1f}% (> {threshold_pct}%)")
            
        return warnings

    def check_correlation(self, new_symbol: str, threshold: float = 0.8) -> list:
        """
        Check price correlation with Top 3 Holdings.
        Returns list of warnings if correlation > threshold.
        """
        if not self.top_holdings: return []
        
        # Prepare Top 3 Symbols
        top_symbols = [h['symbol'] for h in self.top_holdings]
        
        # Skip if analyzing a stock we already own in Top 3 (it will obviously correlate 1.0)
        if new_symbol in top_symbols:
            return []
            
        # Fetch Data (New Symbol + Top 3)
        tickers = [new_symbol] + top_symbols
        warnings = []
        
        try:
            # Fetch 6 months history
            logger.info(f"🔄 Calculating Correlation: {new_symbol} vs {top_symbols}")
            data = yf.download(tickers, period="6m", auto_adjust=True, progress=False)['Close']
            
            if data.empty or len(data) < 30:
                logger.warning(f"⚠️ Insufficient data for correlation check: {new_symbol}")
                return []
                
            # If only one stock fetched (e.g. invalid symbols), corr() won't work effectively
            if isinstance(data, pd.Series):
                 # Single column means others failed
                 return []
            
            # Calculate Correlation Matrix
            corr_matrix = data.corr()
            
            # extracting correlation between new_symbol and others
            # data columns might be MultiIndex if yfinance updated, or simple Index
            # yfinance>=0.2 returns simple columns usually if auto_adjust=True? 
            # safe access:
            
            if new_symbol not in corr_matrix.columns:
                 # Check if it was downloaded?
                 return []
            
            for holding_symbol in top_symbols:
                if holding_symbol in corr_matrix.columns:
                    corr_value = corr_matrix.loc[new_symbol, holding_symbol]
                    if corr_value > threshold:
                        warnings.append(f"⚠️ 與持股 {holding_symbol} 高度連動 (Corr: {corr_value:.2f})")
                        
        except Exception as e:
            logger.error(f"❌ Correlation Check Failed: {e}")
            
        return warnings
