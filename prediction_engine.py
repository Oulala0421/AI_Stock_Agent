"""
Prediction Engine - Regime-Based Bootstrap & Formula Alpha

結合「通用策略評分」與「歷史市場狀態重抽樣 (Regime Bootstrap)」，
提供具學術可信度的價格預測，不依賴常態分佈假設。

Methodology:
1. Regime Identification: Classify history into Bull/Bear regimes (SPY > MA200).
2. Stratified Bootstrap: Resample returns ONLY from the matching historical regime.
3. Alpha Overlay: Adjust expected return based on Strategy Formula Score.

Author: Quant Engineer
Date: 2025-12-08
"""

import yfinance as yf
import pandas as pd
import numpy as np
from market_data import fetch_and_analyze
from database_manager import DatabaseManager
from datetime import datetime, timedelta

# Configuration
NUM_SIMULATIONS = 10000  # High precision
FORECAST_DAYS = 5        # 1 Week
CACHE_DURATION_HOURS = 24  # Cache validity

def get_predicted_return(symbol):
    """
    獲取綜合預測結果 (With DB Caching)
    """
    db = DatabaseManager()
    
    try:
        # 1. Check DB for valid cache
        cached_data = db.get_latest_stock_data(symbol)
        if cached_data:
            last_updated = cached_data.get('last_updated')
            raw_data = cached_data.get('raw_data', {})
            
            # If cache is fresh (< 24h) and has prediction data
            if last_updated and (datetime.now() - last_updated).total_seconds() < 3600 * CACHE_DURATION_HOURS:
                if 'predicted_return_1w' in raw_data and 'confidence_score' in raw_data:
                    print(f"📦 [{symbol}] 使用快取預測值 (上次更新: {last_updated})")
                    return {
                        'predicted_return_1w': raw_data['predicted_return_1w'],
                        'confidence_score': raw_data['confidence_score'],
                        'strategy_score': raw_data.get('strategy_score', 0),
                        'from_cache': True
                    }

        print(f"🔄 [{symbol}] 快取過期或不存在，重新計算預測...")
        
        # 2. 獲取基礎數據 (No DB logic changed below here)
        stock = yf.Ticker(symbol)
        hist = stock.history(period="5y") # 5年數據以涵蓋牛熊循環
        
        if len(hist) < 252:
            print(f"⚠️ [{symbol}] 歷史數據不足 1 年，無法進行可靠模擬")
            return None

        # 2. 執行策略評分 (作為 Alpha)
        market_data = fetch_and_analyze(symbol)
        spy_regime = _get_current_regime()
        strategy_score = _calculate_general_score(market_data, spy_regime, symbol)
        
        # 3. 執行 Regime-Based Bootstrap 模擬
        bootstrap_results = _run_regime_bootstrap(hist, spy_regime['is_bullish'])
        
        # 4. 結合 Alpha 與 Beta
        # Base Market Drift (from Bootstrap)
        market_drift = bootstrap_results['expected_return']
        
        # Strategy Alpha (Score 50 is neutral)
        # Score 100 -> +2% Alpha/week
        # Score 0   -> -2% Alpha/week
        alpha = (strategy_score - 50) / 50 * 0.02 
        
        final_predicted_return = market_drift + alpha
        
        # 計算信心分數
        # 結合策略信心 (Score) 與 統計信心 (Win Rate from Bootstrap)
        stat_confidence = bootstrap_results['win_rate']
        strategy_confidence = abs(strategy_score - 50) / 50 # 越極端越有信心
        
        combined_confidence = (stat_confidence * 0.4) + (strategy_confidence * 0.6)
        
        return {
            'predicted_return_1w': final_predicted_return * 100, # 轉百分比
            'confidence_score': min(combined_confidence, 1.0),
            'strategy_score': strategy_score,
            'market_regime': 'Bull 🐂' if spy_regime['is_bullish'] else 'Bear 🐻',
            'simulation_stats': bootstrap_results
        }

    except Exception as e:
        print(f"❌ [{symbol}] 預測引擎執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return None

def _get_current_regime():
    """判斷當前市場狀態"""
    try:
        spy = yf.Ticker("SPY")
        hist = spy.history(period="1y")
        if len(hist) < 200: return {'is_bullish': True, 'vix': 15}
        
        price = hist['Close'].iloc[-1]
        ma200 = hist['Close'].rolling(200).mean().iloc[-1]
        
        # 簡單定義：價格在年線之上為牛市
        is_bullish = price > ma200
        
        # VIX
        try:
            vix = yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1]
        except:
            vix = 15
            
        return {'is_bullish': is_bullish, 'vix': vix, 'Is_Bullish': is_bullish, 'VIX': vix} # Compatible keys
    except:
        return {'is_bullish': True, 'vix': 15, 'Is_Bullish': True, 'VIX': 15}

def _calculate_general_score(market_data, spy_data, symbol):
    """
    通用策略評分公式 (0-100)
    """
    score = 0
    
    # Extract Indicators
    momentum = market_data.get('momentum', {})
    trend = market_data.get('trend', {})
    volatility = market_data.get('volatility', {})
    price = market_data.get('price', 0)
    
    # Handle missing data gracefully
    if not momentum: return 50 # Neutral if no data
    
    rsi_percentile = momentum.get('rsi_percentile', 0.5)
    bb_position = volatility.get('bb_position', 0.5)
    ma50_above_ma200 = trend.get('ma50_above_ma200', False)
    
    # Fetch Basic Info
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        roe = info.get('returnOnEquity', 0.15) 
        if roe is None: roe = 0.15
        roe = roe * 100
        
        target_price = info.get('targetMeanPrice', price)
        if target_price is None: target_price = price
    except:
        roe = 15
        target_price = price

    # === 1. Quality (30%) ===
    q_score = 10
    if roe > 20: q_score += 20
    elif roe > 10: q_score += 10
    score += q_score
    
    # === 2. Valuation (30%) ===
    v_score = 10
    if target_price > price:
        upside = (target_price - price) / price
        if upside > 0.2: v_score += 20
        elif upside > 0.1: v_score += 10
    score += v_score
    
    # === 3. Trend (20%) ===
    t_score = 0
    if ma50_above_ma200: t_score += 10
    if spy_data['is_bullish']: t_score += 10
    if spy_data['vix'] > 25: t_score -= 5
    score += t_score
    
    # === 4. Technical (20%) ===
    tech_score = 0
    if rsi_percentile < 0.2: tech_score += 20 # Strong Mean Reversion
    elif rsi_percentile < 0.4: tech_score += 10
    elif rsi_percentile > 0.6 and rsi_percentile < 0.8: tech_score += 10 # Momentum
    elif rsi_percentile > 0.9: tech_score -= 10 # Extreme Overbought
    
    if bb_position < 0.05: tech_score += 5
    score += tech_score
    
    return max(0, min(100, score))

def _run_regime_bootstrap(hist_df, is_current_bullish):
    """
    執行 Regime-Based Bootstrap 模擬
    
    邏輯:
    1. 取得 SPY 歷史年線數據
    2. 將目標股票的歷史回報標記為 'Bull Sample' 或 'Bear Sample'
    3. 根據當前市場狀態，只從對應的樣本池中抽樣
    """
    # 計算日回報
    returns = hist_df['Close'].pct_change().dropna()
    
    # 獲取同期 SPY 數據進行標記
    start_date = returns.index[0]
    spy = yf.Ticker("SPY").history(start=start_date)
    spy_ma200 = spy['Close'].rolling(200).mean()
    spy_bullish = (spy['Close'] > spy_ma200).reindex(returns.index).fillna(True) # Align dates
    
    # 分割樣本
    if is_current_bullish:
        # 當前是牛市，我們假設未來一週也是牛市機率高
        # 從歷史牛市中抽樣 (Simulate Bull History)
        sample_pool = returns[spy_bullish]
        if len(sample_pool) < 50: sample_pool = returns # Fallback
    else:
        # 當前是熊市，從熊市樣本中抽樣
        sample_pool = returns[~spy_bullish]
        if len(sample_pool) < 50: sample_pool = returns # Fallback
        
    # Bootstrap Simulation
    # 模擬未來 5 天，重複 N 次
    simulated_paths = np.random.choice(sample_pool.values, size=(NUM_SIMULATIONS, FORECAST_DAYS))
    
    # 計算每條路徑的累積回報
    # (1+r1)*(1+r2)... - 1
    cum_returns = np.prod(1 + simulated_paths, axis=1) - 1
    
    # 統計結果
    expected_return = np.median(cum_returns)
    win_rate = np.mean(cum_returns > 0)
    var_95 = np.percentile(cum_returns, 5)
    
    return {
        'expected_return': expected_return,
        'win_rate': win_rate,
        'var_95': var_95,
        'sample_size': len(sample_pool)
    }

# Backward compatibility alias
def get_predicted_return_fast(symbol, days_forward=5):
    return get_predicted_return(symbol)

if __name__ == "__main__":
    print("🧪 測試 Advanced Regime-Based Prediction Engine...")
    sym = "NVDA"
    print(f"分析目標: {sym}")
    
    res = get_predicted_return(sym)
    
    if res:
        print(f"\n✅ 結果:")
        print(f"   市場狀態: {res['market_regime']}")
        print(f"   策略評分: {res['strategy_score']}")
        print(f"   預測漲跌: {res['predicted_return_1w']:.2f}%")
        print(f"   信心分數: {res['confidence_score']:.0%}")
        print(f"   Bootstrap樣本數: {res['simulation_stats']['sample_size']} 天")
    else:
        print("❌ 失敗")
