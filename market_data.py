"""
Enhanced market_data.py with RSI percentile ranking and multi-timeframe analysis
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime


def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0))
    loss = (-delta.where(delta < 0, 0))
    rs = gain.rolling(window=period).mean() / loss.rolling(window=period).mean()
    return 100 - (100 / (1 + rs))


def calculate_rsi_percentile(current_rsi, rsi_history, lookback=252):
    """
    Calculate RSI percentile ranking - where current RSI stands relative to past year
    
    Parameters:
    -----------
    current_rsi : float
        Current RSI value
    rsi_history : pd.Series
        Historical RSI values
    lookback : int
        Number of days to look back (default 252 = 1 year)
    
    Returns:
    --------
    float : Percentile (0.0 to 1.0) where current RSI sits in historical distribution
    """
    if len(rsi_history) < lookback:
        lookback = len(rsi_history)
    
    recent_rsi = rsi_history.iloc[-lookback:]
    percentile = (recent_rsi < current_rsi).sum() / len(recent_rsi)
    
    return percentile


def calculate_bollinger_bands(series, period=20, std_dev=2):
    ma = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    return ma + (std * std_dev), ma - (std * std_dev), (series - (ma - std * std_dev)) / (2 * std * std_dev)


def calculate_atr(high, low, close, period=14):
    tr = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def calculate_dual_momentum(symbol, benchmark="VOO"):
    try:
        tickers = yf.Tickers(f"{symbol} {benchmark}")
        df = tickers.history(period="18mo", interval="1d", auto_adjust=True)['Close'].dropna()
        if len(df) < 253:
            return {"is_bullish": False, "beat_market": False, "return_12m": 0}
        
        # 12個月回報率
        ret_symbol = (df[symbol].iloc[-1] - df[symbol].iloc[-252]) / df[symbol].iloc[-252]
        ret_benchmark = (df[benchmark].iloc[-1] - df[benchmark].iloc[-252]) / df[benchmark].iloc[-252]
        
        return {
            "is_bullish": ret_symbol > 0 and ret_symbol > ret_benchmark,
            "beat_market": ret_symbol > ret_benchmark,
            "return_12m": ret_symbol
        }
    except:
        return {"is_bullish": False, "beat_market": False, "return_12m": 0}


def get_earnings_warning(ticker_obj):
    try:
        cal = ticker_obj.calendar
        if cal is None or cal.empty:
            return None
        
        if isinstance(cal, dict) and 'Earnings Date' in cal:
            ed = cal['Earnings Date'][0]
        elif isinstance(cal, pd.DataFrame) and 'Earnings Date' in cal.columns:
            ed = cal['Earnings Date'].iloc[0]
        else:
            return None
            
        if isinstance(ed, pd.Timestamp):
            ed = ed.date()
        diff = (ed - datetime.now().date()).days
        return f"⚠️ 警報：{diff} 天後 ({ed}) 財報" if 0 <= diff <= 7 else None
    except:
        return None


def get_market_regime():
    print("🌍 分析市場體質 (SPY & VIX)...")
    try:
        # 1. SPY 趨勢
        spy = yf.Ticker("SPY")
        spy_hist = spy.history(period="1y")
        if spy_hist.empty:
            raise Exception("SPY data empty")
        
        spy_price = spy_hist['Close'].iloc[-1]
        spy_ma200 = spy_hist['Close'].rolling(200).mean().iloc[-1]
        spy_ma50 = spy_hist['Close'].rolling(50).mean().iloc[-1]
        
        # 2. VIX 恐慌指數
        vix = yf.Ticker("^VIX")
        vix_hist = vix.history(period="5d")
        if vix_hist.empty:
            raise Exception("VIX data empty")
        vix_price = vix_hist['Close'].iloc[-1]
        
        return {
            "spy_price": spy_price,
            "spy_ma200": spy_ma200,
            "spy_ma50": spy_ma50,
            "is_bullish": spy_price > spy_ma200,
            "ma50_above_ma200": spy_ma50 > spy_ma200,  # 金叉/死叉
            "vix": vix_price
        }
    except Exception as e:
        print(f"⚠️ 市場數據抓取失敗: {e}")
        return {
            "spy_price": 0,
            "spy_ma200": 0,
            "spy_ma50": 0,
            "is_bullish": False,
            "ma50_above_ma200": False,
            "vix": 25.0
        }


def fetch_and_analyze(symbol):
    print(f"🔄 分析數據: {symbol}...")
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="2y", interval="1d", auto_adjust=True)
        if df.empty:
            return None
        close = df['Close']
        
        latest = df.iloc[-1]
        is_etf = ticker.info.get('quoteType', '') == 'ETF'
        
        # 計算技術指標
        rsi_series = calculate_rsi(close)
        current_rsi = rsi_series.iloc[-1]
        
        # **NEW**: RSI Percentile Ranking
        rsi_percentile = calculate_rsi_percentile(current_rsi, rsi_series, lookback=252)
        
        bb_upper, bb_lower, bb_pct = calculate_bollinger_bands(close)
        atr = calculate_atr(df['High'], df['Low'], close).iloc[-1]
        
        # MA50 for trend confirmation
        ma50 = close.rolling(50).mean().iloc[-1]
        ma200 = close.rolling(200).mean().iloc[-1]
        
        # Dual momentum
        dual_momentum_data = calculate_dual_momentum(symbol)
        
        return {
            "symbol": symbol,
            "price": latest['Close'],
            "is_etf": is_etf,
            "trend": {
                "is_above_ma200": latest['Close'] > ma200,
                "is_above_ma50": latest['Close'] > ma50,
                "ma50_above_ma200": ma50 > ma200,  # 金叉
                "dual_momentum": dual_momentum_data
            },
            "momentum": {
                "rsi": current_rsi,
                "rsi_percentile": rsi_percentile,  # **NEW**
                "is_oversold_bb": latest['Close'] < bb_lower.iloc[-1],
                "bb_position": bb_pct.iloc[-1]  # 0=lower band, 1=upper band
            },
            "volatility": {
                "atr": atr,
                "atr_pct": (atr / latest['Close']) * 100,
                "bb_pct": bb_pct.iloc[-1]
            },
            "levels": {
                "support": df[-60:]['Low'].min(),
                "resistance": df[-60:]['High'].max(),
                "ma50": ma50,
                "ma200": ma200
            },
            "event": {
                "earnings_warning": get_earnings_warning(ticker)
            }
        }
    except Exception as e:
        print(f"❌ 數據錯誤 {symbol}: {e}")
        return None