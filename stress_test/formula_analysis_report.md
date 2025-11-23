# AI Stock Agent 評分公式學術分析報告

---

## 執行摘要

本報告基於學術文獻對 AI Stock Agent 的 Core/Satellite 雙公式評分系統進行深入分析，評估其理論基礎、優缺點，並提出基於 Monte Carlo 模擬的強化方法與可整合的補充資訊。

---

## 第一部分：當前公式解析

### 1.1 Core 策略公式 (長期持有，逢低加碼)

**權重分配:**
- 趨勢健康度 (15%)
- 品質 (35%)
- 價格吸引力 (35%)
- 成本效率 (15%)

**學術對應:**
- **品質因子 (35%)**: 對應 Fama-French Five-Factor Model 的 **Profitability (RMW)** 與 **Quality** 因子
  - 文獻依據: Novy-Marx (2013) 發現 gross profitability 能解釋許多盈餘異常
  - ROE > 20% 門檻: 與 Asness et al. (2019, AQR) "Quality Minus Junk" 因子中的高品質定義一致
  
- **價值因子 (35%)**: 對應 **Value (HML)** 與 **RSI Percentile Ranking**
  - RSI Percentile 創新: 動態調整超買/超賣定義，符合 Jegadeesh \u0026 Titman (1993) 動能反轉理論
  - 文獻支持: RSI 百分位比絕對值更能適應不同波動環境 (Wilder 1978)
  
- **趨勢確認 (15%)**: 對應 **Momentum (UMD)** 與 **MA Crossover**
  - MA50/MA200 金叉/死叉: Brock et al. (1992) 證實移動平均線具有預測能力
  - Dual Momentum: Gary Antonacci (2014) 的絕對+相對動能組合

### 1.2 Satellite 策略公式 (波段操作，Alpha追逐)

**權重分配:**
- 趨勢確認 (20%)
- 品質 (30%)
- 估值安全邊際 (25%)
- 技術時機 (20%)
- 輿情 (5%)

**學術對應:**
- **估值懲罰機制 (25%)**: 創新整合 **Value \u0026 Growth GARP**
  - Discount \u003e 25%: 深度價值投資 (Lakonishok et al. 1994)
  - Discount \u003c -10%: **懲罰追高**，防止 "Winner's Curse" (Thaler 1988)
  
- **技術時機 (20%)**: 整合 **Value Dip \u0026 Momentum Breakout**
  - 同時獎勵 RSI \u003c 20% (逢低) 與 RSI 60-90% (趨勢)
  - 文獻: Jegadeesh \u0026 Titman (2001) 證實短期反轉與中期動能共存
  
- **輿情 (5%)**: 對應 **Behavioral Finance** 情緒因子
  - Baker \u0026 Wurgler (2006) Investor Sentiment Index
  - 低權重 (5%) 符合 Da et al. (2015) 發現情緒僅短期有效

---

## 第二部分：理論基礎評估

### 2.1 多因子模型契合度

| 學術因子 | Core 權重 | Satellite 權重 | 文獻來源 |
|---------|----------|---------------|---------|
| **Market Beta** | ✓ (趨勢15%) | ✓ (趨勢20%) | CAPM (Sharpe 1964) |
| **Size (SMB)** | ✗ | ✗ | Fama-French (1993) |
| **Value (HML)** | ✓ (價值35%) | ✓ (估值25%) | Fama-French (1993) |
| **Momentum (UMD)** | ✓ (隱含) | ✓ (技術20%) | Carhart (1997) |
| **Quality (RMW)** | ✓ (品質35%) | ✓ (品質30%) | Fama-French (2015) |
| **Low Volatility** | ✗ | ✗ | Ang et al. (2006) |

**評分: 4/6 因子覆蓋** (缺少 Size 與 Low Volatility)

### 2.2 Core-Satellite 策略學術驗證

- **理論基礎**: 資產配置文獻強調 Core (70-90%) 穩定、Satellite (10-30%) Alpha (Sharpe 1991, Vanguard 2016)
- **當前實作**: Core Pool $10,200 (60%) vs Satellite Pool $6,800 (40%)
- **偏離度**: **Satellite 比例偏高**，可能增加組合波動
- **建議**: 考慮調整至 Core 70% / Satellite 30% 以符合文獻標準

---

## 第三部分：優缺點分析

### 3.1 優勢 ✅

1. **多因子整合**: 成功整合 Value, Momentum, Quality 三大經典因子
2. **動態超買/超賣**: RSI Percentile 優於固定閾值 (70/30)
3. **防追高機制**: Satellite 的估值懲罰 (-15% if discount \u003c -10%) 罕見且創新
4. **雙公式分離**: Core/Satellite 差異化策略符合學術建議 (Blitz \u0026 van Vliet 2008)

### 3.2 缺陷 ❌

1. **缺少 Size 因子**: 未考慮市值效應，可能錯失小型股溢酬
   - 文獻: Fama-French (1992) 發現 Size 解釋 cross-sectional returns
   
2. **無波動率調整**: 未整合 Low Volatility Anomaly
   - 文獻: Ang et al. (2006) 證實低波動股票長期表現更佳
   
3. **靜態權重**: 各因子權重固定，無法應對市場regime變化
   - 建議: 可考慮 **Dynamic Factor Weighting** (Bender et al. 2010)
   
4. **缺乏流動性因子**: 未考慮交易成本與市場衝擊
   - 文獻: Pástor \u0026 Stambaugh (2003) Liquidity Premium
   
5. **基本面數據滯後**: ROE, Target Price 為時點數據，無法捕捉趨勢變化
   - 建議: 加入 **Earnings Momentum** (Ball \u0026 Brown 1968)

### 3.3 風險警示 ⚠️

1. **過度擬合 (Overfitting)**: 多達 10+ 參數，可能在樣本外失效
   - McLean \u0026 Pontiff (2016): 大部分因子在發表後衰退
   
2. **數據窺探 (Data Snooping)**: 未進行 out-of-sample 測試
   - 建議: 保留 20% 數據作為 hold-out validation set
   
3. **交易成本**: 假設無摩擦，實際回測可能高估收益
   - Novy-Marx \u0026 Velikov (2016): 交易成本可吞噬大部分因子收益

---

## 第四部分：Monte Carlo 強化方法

### 4.1 參數穩健性測試 (Parameter Sensitivity)

**問題**: 當前權重 (Core: 15-35-35-15, Satellite: 20-30-25-20-5) 是否最優?

**解決方案**: **Monte Carlo 隨機化權重**

```python
# 偽代碼示例
for iteration in range(100000):
    # 隨機生成權重 (Dirichlet Distribution)
    weights = np.random.dirichlet(alpha=[1,1,1,1], size=1)
    
    # 用隨機權重跑回測
    portfolio_return = backtest_with_weights(weights)
    
    # 記錄 Sharpe Ratio
    sharpe_ratios[iteration] = portfolio_return / portfolio_volatility
    
# 找出最優權重區間
optimal_weights = weights[sharpe_ratios \u003e percentile(95)]
```

**預期收益**: 
- 發現 **穩健權重範圍** (例如: Value 應在 30-40% 而非固定35%)
- 識別 **脆弱參數** (輕微調整即大幅影響績效)

### 4.2 Regime Switching 模擬

**問題**: 固定權重在牛市/熊市/震盪市表現差異大

**解決方案**: **Hidden Markov Model (HMM) 市場狀態辨識**

- **State 1 (牛市)**: 提升 Momentum 權重, 降低 Value
- **State 2 (熊市)**: 提升 Quality \u0026 Value, 降低 Momentum
- **State 3 (震盪)**: 平衡所有因子

**文獻依據**: Ang \u0026 Bekaert (2002) Regime Switching in Equity Markets

### 4.3 極端情境壓力測試

**當前缺失**: 雖已執行 100K Monte Carlo，但基於**歷史波動率**，未模擬極端事件

**強化方案**: **Fat-Tail Distribution**

```python
# 替換 Gaussian 為 Student-t Distribution (df=3-5)
Z = np.random.standard_t(df=4, size=(days, num_simulations))

# 或使用 Jump-Diffusion Model (Merton 1976)
returns = mu*dt + sigma*Z + jump_probability * jump_size
```

**預期收益**:
- 更準確的 VaR (尾部風險)
- 識別 "Black Swan" 場景下的最大損失

### 4.4 因子正交化 (Factor Orthogonalization)

**問題**: Value 與 Momentum 負相關 (Asness et al. 2013)，直接加權可能抵消

**解決方案**: **Gram-Schmidt 正交化**

```python
# 將 Momentum 從 Value 中移除相關性
momentum_ortho = momentum - (momentum · value) / ||value||² * value

# 重新計算評分
score = w1*value + w2*momentum_ortho + w3*quality
```

**文獻**: Fama-French (2018) 使用正交化處理多重共線性

---

## 第五部分：可加入的補充資訊

### 5.1 基本面因子 (高優先級 🔥)

| 因子 | 計算方式 | 文獻依據 | 資料來源 |
|------|---------|---------|---------|
| **Earnings Momentum** | (EPS本季 - EPS去年同季) / 股價 | Ball \u0026 Brown (1968) | Yahoo Finance / Alpha Vantage |
| **Sales Growth** | (Revenue YoY成長率) | Lakonishok et al. (1994) | 10-Q Filings |
| **Free Cash Flow Yield** | FCF / Market Cap | Novy-Marx (2013) | Cash Flow Statement |
| **Debt-to-Equity** | 總負債 / 股東權益 | Bhandari (1988) | Balance Sheet |
| **Piotroski F-Score** | 9維度財務健康評分 | Piotroski (2000) | Multiple Metrics |

**實作建議**: 優先加入 **Earnings Momentum** (收益最高，成本最低)

### 5.2 市場微觀結構 (中優先級 ⚙)

| 因子 | 計算方式 | 文獻依據 |
|------|---------|---------|
| **Bid-Ask Spread** | (Ask - Bid) / Mid-Price | Roll (1984) |
| **Amihud Illiquidity** | |Return| / Dollar Volume | Amihud (2002) |
| **短期反轉** | 過去1週報酬率 | Jegadeesh (1990) |

**資料來源**: Interactive Brokers API, Polygon.io

### 5.3 另類數據 (低優先級，高成本 💸)

- **社群媒體情緒** (Twitter, StockTwits): Bollen et al. (2011)
- **衛星圖像** (停車場車輛數): RS Metrics
- **信用卡交易數據**: 對沖基金專用

**評估**: 成本效益比低，**不建議**個人投資者採用

### 5.4 機器學習特徵工程

- **Autocorrelation**: 價格序列自相關性
- **Hurst Exponent**: 趨勢持續性vs均值回歸
- **Fractal Dimension**: 價格複雜度

**文獻**: Lopez de Prado (2018) "Advances in Financial Machine Learning"

---

## 第六部分：模擬驗證框架

### 6.1 Walk-Forward Analysis

```
Training Window: 2014-2018 (學習最優參數)
   ↓
Validation: 2019 (調整參數)
   ↓
Test: 2020-2024 (最終績效)
```

### 6.2 Monte Carlo Bootstrap

- **重採樣**: 從歷史中隨機抽取交易日 (with replacement)
- **次數**: 10,000 次
- **目標**: 評估策略在不同歷史序列下的穩定性

### 6.3 Benchmark 對照

| Benchmark | 說明 |
|-----------|------|
| SPY (Buy \u0026 Hold) | 被動基準 |
| 60/40 Portfolio | 傳統配置 |
| AQR Multi-Factor ETF | 學術級多因子 |
| 自定義: Pure Value/Momentum | 單因子對照組 |

---

## 第七部分：具體改進建議

### 優先級 1 (立即實施) 🚨

1. **加入 Market Cap 因子** (Size)
   - 新增: `if market_cap \u003c 10B: score += 5`
   
2. **Earnings Momentum**
   - 新增: `earnings_growth = (EPS_t - EPS_t-4) / price`
   
3. **Walk-Forward 回測**
   - 驗證公式在 out-of-sample 表現

### 優先級 2 (1-2個月) ⏰

4. **動態權重調整**
   - 根據 VIX \u003e 30 調整 Value vs Momentum 比例
   
5. **Low Volatility 篩選**
   - 新增: `if std_dev \u003c median_std: score += 3`
   
6. **交易成本估算**
   - 扣除 bid-ask spread + 滑價

### 優先級 3 (長期研究) 🔬

7. **機器學習整合**
   - XGBoost 取代線性加權
   
8. **Regime Switching**
   - HMM 辨識市場狀態

---

## 第八部分：結論

### 8.1 整體評分

| 維度 | 評分 (1-10) | 說明 |
|------|-----------|------|
| 理論基礎 | 9/10 | 紮實的多因子架構 |
| 創新性 | 8/10 | RSI Percentile 與估值懲罰 |
| 可實作性 | 10/10 | 所有數據可免費取得 |
| 穩健性 | 6/10 | 需 Walk-Forward 驗證 |
| 完整性 | 7/10 | 缺 Size \u0026 Liquidity 因子 |

**綜合評分: 8.0/10** (優秀，但仍有改進空間)

### 8.2 核心洞察

✅ **已做對的事**:
- Core/Satellite 分離策略
- 多因子整合
- 防追高機制

⚠️ **需要警惕**:
- Overfitting 風險
- 靜態權重
- 缺乏 out-of-sample 驗證

🚀 **下一步行動**:
1. 立即: 加入 Earnings Momentum
2. 本月: Walk-Forward 回測
3. 下季: 探索動態權重

---

## 參考文獻

1. Fama, E., \u0026 French, K. (1993). "Common Risk Factors in Returns"
2. Carhart, M. (1997). "On Persistence in Mutual Fund Performance"
3. Novy-Marx, R. (2013). "The Other Side of Value: Gross Profitability Premium"
4. Asness, C., et al. (2013). "Value and Momentum Everywhere"
5. Antonacci, G. (2014). "Dual Momentum Investing"
6. Jorion, P. (2007). "Value at Risk: The New Benchmark"
7. Ang, A., \u0026 Bekaert, G. (2002). "Regime Switches in Interest Rates"
8. Piotroski, J. (2000). "Value Investing: F-Score"
9. McLean, R., \u0026 Pontiff, J. (2016). "Does Academic Research Destroy Return Predictability?"
10. Lopez de Prado, M. (2018). "Advances in Financial Machine Learning"

---

**報告完成日期**: 2025-11-21  
**分析師**: AI Stock Agent Team  
**版本**: 1.0
