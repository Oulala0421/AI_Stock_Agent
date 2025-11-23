import pandas as pd
import numpy as np
from .config import INITIAL_CAPITAL, STRESS_PERIODS
from .strategy_proxy import calculate_historical_scores

class Backtester:
    def __init__(self, data_dict, stock_types, initial_capital=INITIAL_CAPITAL):
        self.data_dict = data_dict
        self.stock_types = stock_types
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {} # {symbol: shares}
        self.portfolio_history = []
        self.trade_log = []
        
    def run(self, market_regime):
        print("🚀 開始執行回測...")
        
        # Align all data to market regime index
        dates = market_regime.index
        
        # Pre-calculate scores for all stocks to speed up loop
        stock_scores = {}
        stock_signals = {}
        
        print("📊 計算歷史評分中...")
        for symbol, df in self.data_dict.items():
            if symbol in ["SPY", "^VIX"]: continue
            
            stock_type = self.stock_types.get(symbol, "Satellite")
            # Assume static quality data for now (can be improved)
            static_quality = {'roe': '15%', 'target': '0'} 
            
            scores, signals = calculate_historical_scores(df, market_regime, stock_type, static_quality)
            stock_scores[symbol] = scores
            stock_signals[symbol] = signals
            
        print("⏳ 逐日模擬交易中...")
        for date in dates:
            # 1. Update Portfolio Value
            current_value = self.cash
            for symbol, shares in self.positions.items():
                if symbol in self.data_dict and date in self.data_dict[symbol].index:
                    price = self.data_dict[symbol].loc[date, 'Close']
                    current_value += shares * price
            
            self.portfolio_history.append({
                'Date': date,
                'Total_Value': current_value,
                'Cash': self.cash
            })
            
            # 2. Execute Trades based on Signals
            for symbol in stock_scores:
                if date not in stock_scores[symbol].index: continue
                
                score = stock_scores[symbol].loc[date]
                signal = stock_signals[symbol].loc[date]
                price = self.data_dict[symbol].loc[date, 'Close']
                atr = self.data_dict[symbol].loc[date, 'ATR']
                
                if pd.isna(price) or pd.isna(atr) or atr == 0: continue
                
                # Position Sizing Logic (Simplified for Backtest)
                # Core: Max 30% alloc, Satellite: Max 25% alloc
                # We use a simplified pool model: Total Capital * Allocation %
                
                stock_type = self.stock_types.get(symbol, "Satellite")
                max_alloc_pct = 0.30 if stock_type == "Core" else 0.25
                max_position_value = current_value * max_alloc_pct
                
                current_shares = self.positions.get(symbol, 0)
                current_pos_value = current_shares * price
                
                target_value = 0
                
                if signal == "BUY":
                    # Target 100% of max allocation (aggressive)
                    target_value = max_position_value
                elif signal == "ACCUMULATE":
                    # Target 50% of max allocation
                    target_value = max_position_value * 0.5
                elif signal == "HOLD":
                    target_value = current_pos_value # Keep as is
                elif signal == "REDUCE":
                    target_value = 0 # Exit
                
                # Rebalance if difference is significant (>10% change)
                diff_value = target_value - current_pos_value
                
                if abs(diff_value) > 1000: # Minimum trade size
                    if diff_value > 0 and self.cash > diff_value:
                        # Buy
                        shares_to_buy = int(diff_value / price)
                        if shares_to_buy > 0:
                            cost = shares_to_buy * price
                            self.cash -= cost
                            self.positions[symbol] = current_shares + shares_to_buy
                            self.trade_log.append({'Date': date, 'Symbol': symbol, 'Action': 'BUY', 'Price': price, 'Shares': shares_to_buy})
                    elif diff_value < 0:
                        # Sell
                        shares_to_sell = int(abs(diff_value) / price)
                        if shares_to_sell > 0:
                            shares_to_sell = min(shares_to_sell, current_shares)
                            proceeds = shares_to_sell * price
                            self.cash += proceeds
                            self.positions[symbol] = current_shares - shares_to_sell
                            self.trade_log.append({'Date': date, 'Symbol': symbol, 'Action': 'SELL', 'Price': price, 'Shares': shares_to_sell})
                            
        print("✅ 回測完成")
        return pd.DataFrame(self.portfolio_history).set_index('Date')

    def analyze_performance(self, history_df):
        """
        Calculate CAGR, Max DD, Sharpe
        """
        df = history_df.copy()
        df['Return'] = df['Total_Value'].pct_change()
        
        # CAGR
        days = (df.index[-1] - df.index[0]).days
        years = days / 365.25
        total_return = (df['Total_Value'].iloc[-1] / df['Total_Value'].iloc[0]) - 1
        cagr = (1 + total_return) ** (1 / years) - 1
        
        # Max DD
        df['Peak'] = df['Total_Value'].cummax()
        df['Drawdown'] = (df['Total_Value'] - df['Peak']) / df['Peak']
        max_dd = df['Drawdown'].min()
        
        # Sharpe (Assume risk-free 2%)
        rf = 0.02
        excess_ret = df['Return'].mean() * 252 - rf
        volatility = df['Return'].std() * (252 ** 0.5)
        sharpe = excess_ret / volatility if volatility > 0 else 0
        
        results = {
            "CAGR": cagr,
            "Max_Drawdown": max_dd,
            "Sharpe_Ratio": sharpe,
            "Total_Return": total_return,
            "Final_Value": df['Total_Value'].iloc[-1]
        }
        
        return results, df
