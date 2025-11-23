import pandas as pd
import numpy as np

def calculate_historical_scores(df, market_regime, stock_type="Satellite", static_quality_data=None):
    """
    Calculate Confidence Scores for the entire history (Vectorized-ish or Row-based)
    
    df: DataFrame with indicators (RSI, BB_Position, etc.)
    market_regime: DataFrame with SPY/VIX info aligned to df index
    stock_type: "Core" or "Satellite"
    static_quality_data: dict of current fundamentals (ROE, Target, etc.) - acting as static proxy
    """
    
    scores = []
    signals = []
    
    if static_quality_data is None:
        static_quality_data = {}
        
    # Pre-calculate some static scores to save time
    quality_score_base = 0
    # ROE Logic (Static)
    try:
        roe_val = float(static_quality_data.get('roe', '0').strip('%')) if isinstance(static_quality_data.get('roe'), str) and static_quality_data.get('roe') != 'N/A' else 0
        if stock_type == "Core":
            if roe_val > 20: quality_score_base += 15
            elif roe_val > 15: quality_score_base += 10
        else:
            if roe_val > 25: quality_score_base += 15
            elif roe_val > 20: quality_score_base += 10
            elif roe_val > 15: quality_score_base += 5
    except: pass
    quality_score_base += 5 # Base quality
    
    # Iterate through history (using loop for clarity and complex logic, can be vectorized later if slow)
    # Align indices
    common_index = df.index.intersection(market_regime.index)
    df = df.loc[common_index]
    market_regime = market_regime.loc[common_index]
    
    for date, row in df.iterrows():
        regime = market_regime.loc[date]
        score = 0
        
        # === Core Strategy ===
        if stock_type == "Core":
            # A. Market (20%)
            if regime['Is_Bullish']: score += 10
            if regime['VIX'] < 20: score += 10
            elif regime['VIX'] < 30: score += 5
            
            # B. Quality (30%)
            q_score = quality_score_base
            if row['Is_Bullish']: q_score += 15 # Dual Momentum proxy
            score += q_score
            
            # C. Value (35%)
            v_score = 0
            rsi_pct = row.get('RSI_Percentile', 0.5)
            if rsi_pct < 0.25: v_score += 20
            elif rsi_pct < 0.40: v_score += 15
            elif rsi_pct < 0.60: v_score += 10
            elif rsi_pct < 0.80: v_score += 5
            
            bb_pos = row.get('BB_Position', 0.5)
            if bb_pos < 0.3: v_score += 10
            elif bb_pos < 0.7: v_score += 5
            
            if regime['VIX'] > 25: v_score += 5
            score += v_score
            
            # D. Cost Efficiency (15%) - Static Target Proxy
            # Assuming Target Price is relative to current price, hard to backtest without historical targets.
            # We will use a simplified logic: if price is significantly below MA200, assume "cheap" relative to long term value
            c_score = 10
            if row['Close'] < row['MA200'] * 0.95: c_score += 5
            score += c_score
            
        # === Satellite Strategy ===
        else:
            # A. Trend (20%)
            t_score = 0
            if regime['Is_Bullish']: t_score += 10
            if regime['MA50_Above_MA200']: t_score += 5
            if row['Is_Bullish']: t_score += 5
            
            if regime['VIX'] > 30: t_score -= 10
            elif regime['VIX'] > 25: t_score -= 5
            score += t_score
            
            # B. Quality (30%)
            q_score = quality_score_base
            if row['Is_Bullish']: q_score += 10
            q_score += 5 # Revenue growth proxy
            score += q_score
            
            # C. Valuation (25%)
            val_score = 0
            # Proxy: Distance from MA200 as valuation proxy
            # If price is too far above MA200, expensive. If below, cheap.
            dist_ma200 = (row['Close'] - row['MA200']) / row['MA200'] if row['MA200'] > 0 else 0
            
            if dist_ma200 < -0.15: val_score += 25 # Deep discount
            elif dist_ma200 < -0.05: val_score += 15
            elif dist_ma200 < 0.05: val_score += 5
            elif dist_ma200 > 0.20: val_score -= 15 # Expensive
            elif dist_ma200 > 0.10: val_score -= 5
            else: val_score += 5 # Neutral
            
            score += val_score
            
            # D. Tech Timing (20%)
            tech_score = 0
            rsi_pct = row.get('RSI_Percentile', 0.5)
            rsi = row.get('RSI', 50)
            
            if rsi_pct < 0.20: tech_score += 15
            elif rsi_pct < 0.40: tech_score += 10
            elif rsi_pct > 0.60 and rsi_pct < 0.90: tech_score += 10
            elif rsi_pct >= 0.40 and rsi_pct <= 0.60: tech_score += 5
            
            if rsi > 85: tech_score -= 5
            if row.get('BB_Position', 0.5) < 0.05: tech_score += 5 # Oversold BB
            
            score += tech_score
            
        # Cap Score
        score = max(0, min(100, score))
        scores.append(score)
        
        # Generate Signal
        signal = "HOLD"
        if stock_type == "Core":
            if score >= 55: signal = "BUY"
            elif score >= 50: signal = "ACCUMULATE"
        else:
            if score >= 70: signal = "BUY"
            elif score >= 65: signal = "ACCUMULATE"
            elif score < 35: signal = "REDUCE"
            
        signals.append(signal)
        
    # Return Series aligned with df
    return pd.Series(scores, index=common_index), pd.Series(signals, index=common_index)
