import sys
import os
import pandas as pd
from .config import START_DATE, END_DATE, STRESS_PERIODS
from .data_loader import fetch_all_data
from .indicators import calculate_indicators, calculate_market_regime
from .backtester import Backtester
from .monte_carlo import run_monte_carlo_simulation

def main():
    print("🔥 啟動極限壓力模擬系統 (Stress Test System) 🔥")
    print("==================================================")
    
    # 1. Fetch Data
    data_dict, all_symbols, stock_types = fetch_all_data(START_DATE, END_DATE)
    
    if "SPY" not in data_dict or "^VIX" not in data_dict:
        print("❌ 缺少 SPY 或 VIX 數據，無法執行回測")
        return

    # 2. Calculate Indicators & Market Regime
    print("⚙️ 計算技術指標...")
    for symbol in data_dict:
        data_dict[symbol] = calculate_indicators(data_dict[symbol])
        
    market_regime = calculate_market_regime(data_dict['SPY'], data_dict['^VIX'])
    
    # 3. Run Backtest
    backtester = Backtester(data_dict, stock_types)
    history_df = backtester.run(market_regime)
    
    # 4. Analyze Performance
    results, analysis_df = backtester.analyze_performance(history_df)
    
    print("\n📊 全歷史回測結果 (2014-Present):")
    print(f"💰 最終淨值: ${results['Final_Value']:.2f}")
    print(f"📈 總報酬率: {results['Total_Return']*100:.2f}%")
    print(f"📅 年化報酬 (CAGR): {results['CAGR']*100:.2f}%")
    print(f"📉 最大回撤 (Max DD): {results['Max_Drawdown']*100:.2f}%")
    print(f"⚖️ 夏普比率 (Sharpe): {results['Sharpe_Ratio']:.2f}")
    
    # 5. Stress Period Analysis
    print("\n🌪️ 極限壓力測試場景分析:")
    for name, (start, end) in STRESS_PERIODS.items():
        # Filter history for this period
        period_df = analysis_df.loc[start:end]
        if period_df.empty: continue
        
        start_val = period_df['Total_Value'].iloc[0]
        end_val = period_df['Total_Value'].iloc[-1]
        min_val = period_df['Total_Value'].min()
        
        period_return = (end_val / start_val) - 1
        period_dd = (min_val / start_val) - 1
        
        print(f"  🔸 {name}: 報酬率 {period_return*100:.1f}% | 最大跌幅 {period_dd*100:.1f}%")
        
    # 6. Monte Carlo Simulation (Academic Standard: 100,000 iterations)
    print("\n🎲 執行 Monte Carlo 未來模擬 (1年, 100K 次迭代)...")
    mc_results = run_monte_carlo_simulation(
        portfolio_value=results['Final_Value'],
        daily_returns=analysis_df['Return'].dropna(),
        num_simulations=100000,  # Academic literature standard for robust estimates
        days=252
    )
    
    print(f"  🔮 預期中位數: ${mc_results['Median_Final_Value']:.2f}")
    print(f"  ⚠️ 95% 風險值 (VaR): ${mc_results['VaR_95']:.2f} (-{mc_results['VaR_95_Percent']*100:.1f}%)")
    print(f"  ☠️ 腰斬風險 (Loss > 50%): {mc_results['Bankruptcy_Risk']*100:.2f}%")
    
    print("\n✅ 壓力測試完成！")

if __name__ == "__main__":
    main()
