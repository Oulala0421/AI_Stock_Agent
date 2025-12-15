
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from garp_strategy import GARPStrategy
from data_adapter import DataAdapter
from logger import logger

# Helper for RSI
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

class BacktestAdapter(DataAdapter):
    """
    Mock DataAdapter for Backtesting.
    Intercepts calls to provide Point-in-Time (PIT) data.
    """
    def __init__(self, full_history_df: pd.DataFrame):
        super().__init__()
        self.full_history = full_history_df
        self.current_date = None # Set this during simulation loop

    def set_current_date(self, date):
        self.current_date = pd.to_datetime(date)

    def get_price_data(self, ticker: str, period="2y", interval="1d"):
        """
        Overridden: Returns history UP TO self.current_date.
        """
        if self.current_date is None:
            return self.full_history
            
        # Slice history to simulate "Knowledge at time t"
        mask = self.full_history.index <= self.current_date
        sliced_df = self.full_history.loc[mask].copy()
        return sliced_df
        
    # Note: mocking get_financials for true PIT is complex (requires filing dates).
    # For Phase 16 MVP, we assume financials are "static" or "known" (Look-ahead bias on fundamentals),
    # but Price/Technicals are strictly PIT.
    # Future 16.3: Implement simulated quarterly release dates.

class BacktestEngine:
    def __init__(self, ticker: str, start_date: str, end_date: str, initial_capital: float = 10000.0):
        self.ticker = ticker
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.capital = initial_capital
        self.holdings = 0
        self.ledger = []
        self.strategy = GARPStrategy()
        
        # Pre-fetch full history once to speed up simulation
        logger.info(f"📚 Pre-fetching full history for {ticker}...")
        self.real_adapter = DataAdapter()
        full_price_history = self.real_adapter.get_price_data(ticker, period="5y") # Ensure enough runway
        
        # Standardize to TZ-Naive to avoid mismatch with start_date/end_date (which are naive)
        if hasattr(full_price_history.index, 'tz'):
             full_price_history.index = full_price_history.index.tz_localize(None)
        
        # Initialize Mock Adapter
        self.mock_adapter = BacktestAdapter(full_price_history)
        
        # Inject Mock Adapter into Strategy
        # This requires GARPStrategy to respect injected adapter if we modify it, 
        # or we manually overwrite attributes.
        self.strategy.data_adapter = self.mock_adapter
        
        # Optimization: Disable News & Market Sentiment API calls for Mass Backtest
        self.strategy.news_agent.enabled = False 
        self.strategy.get_market_sentiment = lambda: 0.0 # Mock SPY sentiment
        self.strategy.sector_analysis.calculate_sector_z_score = lambda s, m, v: 0.0 # Mock Sector Analysis if needed

    def run(self):
        logger.info(f"🚀 Starting Walk-Forward Backtest for {self.ticker} ({self.start_date.date()} to {self.end_date.date()})...")
        
        # Generate Trading Days Loop
        history = self.mock_adapter.full_history
        mask = (history.index >= self.start_date) & (history.index <= self.end_date)
        trading_days = history.loc[mask].index
        
        for current_time in trading_days:
            self.mock_adapter.set_current_date(current_time)
            
            # Get Current Price (Close)
            # In backtest, we trade at Close of Day t (or Open of t+1, let's say Close for simplicity)
            current_price = history.loc[current_time]['Close']
            
            # --- 1. Run Strategy Analysis ---
            # We must pass the mocked adapter logic indirectly or rely on strategy using it.
            # verify_phase13 confirmed strategy uses self.data_adapter. 
            # We overwrote it in __init__.
            
            # 4. Execute Strategy
            try:
                # OPTIMIZATION: Manually construct market_data to avoid yfinance call in fetch_and_analyze
                # We need to slice the mock adapter's full history up to current_time explicitly for calculations
                sliced_price = history.loc[history.index <= current_time] 
                market_data = self._calculate_market_data(sliced_price)
                
                # Pass explicit market_data to bypass fetch_and_analyze
                card = self.strategy.analyze(self.ticker, market_data=market_data)
            except Exception as e:
                logger.error(f"Analysis failed on {current_time}: {e}")
                continue
                
            # --- 2. Execution Logic ---
            signal = card.overall_status # PASS, WATCHLIST, REJECT
            
            self._execute_trade(current_time, current_price, signal, card)
            
        self._generate_report()

    def _execute_trade(self, date, price, signal, card):
        """
        Simple Long-Only System:
        - Buy if PASS and Cash > 0.
        - Sell if REJECT and Holdings > 0.
        - Hold if WATCHLIST.
        """
        # Slippage Model (Phase 16.2 Simple)
        # Assuming 0.1% slippage
        execution_price = price * 1.001 if signal == 'PASS' else price * 0.999
        
        if signal == 'PASS':
            if self.capital > execution_price:
                # Buy Max
                shares_to_buy = int(self.capital // execution_price)
                if shares_to_buy > 0:
                    cost = shares_to_buy * execution_price
                    self.capital -= cost
                    self.holdings += shares_to_buy
                    self.ledger.append({
                        'Date': date, 'Action': 'BUY', 'Price': execution_price, 
                        'Shares': shares_to_buy, 'Value': cost, 'Reason': card.overall_reason
                    })
                    logger.info(f"🟢 [BUY] {date.date()} {shares_to_buy} shares @ ${execution_price:.2f}")
                    
        elif signal == 'REJECT':
            if self.holdings > 0:
                # Sell All
                proceeds = self.holdings * execution_price
                self.capital += proceeds
                self.ledger.append({
                    'Date': date, 'Action': 'SELL', 'Price': execution_price, 
                    'Shares': self.holdings, 'Value': proceeds, 'Reason': card.overall_reason
                })
                self.holdings = 0
                logger.info(f"🔴 [SELL] {date.date()} ALL shares @ ${execution_price:.2f}")

    def _generate_report(self):
        # Calculate Final Value
        last_price = self.mock_adapter.full_history.iloc[-1]['Close']
        portfolio_value = self.capital + (self.holdings * last_price)
        initial_val = 10000.0
        return_pct = (portfolio_value - initial_val) / initial_val
        
        logger.info("="*40)
        logger.info(f"🏁 Backtest Complete for {self.ticker}")
        logger.info(f"   Initial Capital: ${initial_val:.2f}")
        logger.info(f"   Final Value:     ${portfolio_value:.2f}")
        logger.info(f"   Total Return:    {return_pct:.2%}")
        logger.info(f"   Total Trades:    {len(self.ledger)}")
        logger.info("="*40)
        
        # Dump Ledger
        if self.ledger:
            df = pd.DataFrame(self.ledger)
            logger.info("\n" + df.to_string())

    def _calculate_market_data(self, df):
        """Calculates indicators locally from the sliced dataframe"""
        if df is None or df.empty or len(df) < 50:
            return {}
            
        close = df['Close']
        latest_price = close.iloc[-1]
        
        # MAs
        ma50 = close.rolling(50).mean().iloc[-1]
        ma200 = close.rolling(200).mean().iloc[-1]
        
        # RSI
        try:
            rsi = calculate_rsi(close).iloc[-1]
        except:
            rsi = 50.0
        
        # Bollinger
        try:
            sma20 = close.rolling(20).mean()
            std20 = close.rolling(20).std()
            upper = sma20 + 2*std20
            lower = sma20 - 2*std20
            
            bb_upper = upper.iloc[-1]
            bb_lower = lower.iloc[-1]
            bb_pct = (latest_price - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) != 0 else 0.5
        except:
            bb_pct = 0.5

        # ATR (Simplified)
        try:
            high = df['High']
            low = df['Low']
            tr = pd.concat([
                high - low,
                (high - close.shift()).abs(),
                (low - close.shift()).abs()
            ], axis=1).max(axis=1)
            atr = tr.rolling(14).mean().iloc[-1]
        except:
            atr = 0.0

        return {
            "price": latest_price,
            "change_pct": (latest_price - close.iloc[-2])/close.iloc[-2] * 100 if len(close) > 1 else 0,
            "volume": df['Volume'].iloc[-1] if 'Volume' in df else 0,
            "trend": {
                "ma50": ma50,
                "ma200": ma200,
                "is_uptrend": latest_price > ma200,
                "ma50_above_ma200": ma50 > ma200
            },
            "momentum": {
                "rsi": rsi,
                "rsi_percentile": rsi / 100.0 # Proxy
            },
            "volatility": {
                "atr": atr,
                "bb_pct": bb_pct
            },
            "levels": {
                "support": low.iloc[-60:].min(),
                "resistance": high.iloc[-60:].max()
            },
            "returns": close.pct_change().dropna().tail(252) # Last 1 year returns
        }
