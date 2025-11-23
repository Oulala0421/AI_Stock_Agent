import pandas as pd
import numpy as np

def calculate_indicators(df):
    """
    Calculate technical indicators for a given DataFrame (must have 'Close')
    Returns DataFrame with added columns
    """
    df = df.copy()
    
    # Ensure Close is present
    if 'Close' not in df.columns:
        return df
        
    close = df['Close']
    
    # 1. Moving Averages
    df['MA50'] = close.rolling(window=50).mean()
    df['MA200'] = close.rolling(window=200).mean()
    
    # 2. RSI (14)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # RSI Percentile (Rolling 252 days - 1 year)
    df['RSI_Percentile'] = df['RSI'].rolling(window=252).rank(pct=True)
    
    # 3. Bollinger Bands (20, 2)
    sma20 = close.rolling(window=20).mean()
    std20 = close.rolling(window=20).std()
    df['BB_Upper'] = sma20 + (std20 * 2)
    df['BB_Lower'] = sma20 - (std20 * 2)
    
    # BB Position (0=Lower, 1=Upper)
    df['BB_Position'] = (close - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
    
    # 4. ATR (14)
    high = df['High']
    low = df['Low']
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=14).mean()
    
    # 5. Dual Momentum (Simplified Proxy)
    # 假設: 若 Close > MA200 且 RSI > 50 視為強勢 (簡化版，因為無法完全重現複雜的相對強弱)
    df['Is_Bullish'] = (close > df['MA200']) & (df['RSI'] > 50)
    
    return df

def calculate_market_regime(spy_df, vix_df):
    """
    Calculate Market Regime (SPY Trend + VIX)
    """
    spy_df = calculate_indicators(spy_df)
    
    regime = pd.DataFrame(index=spy_df.index)
    regime['SPY_Close'] = spy_df['Close']
    regime['Is_Bullish'] = spy_df['Close'] > spy_df['MA200']
    regime['MA50_Above_MA200'] = spy_df['MA50'] > spy_df['MA200']
    
    # Align VIX
    vix_aligned = vix_df['Close'].reindex(spy_df.index, method='ffill')
    regime['VIX'] = vix_aligned
    
    return regime
