# 🚀 AI Stock Agent v1.0 - Go Live Checklist

## ✅ Sprint 3 完成項目回顧

- [x] **Mobile-First UI**: 單欄佈局 (< 768px)，觸控友善，字體優化。
- [x] **Regime-Based Prediction Engine**: 牛熊市區分歷史重抽樣 + 策略 Alpha。
- [x] **通知整合**: `report_formatter.py` 已加入預測漲跌與信心分數。
- [x] **智能快取**: MongoDB 24 小時有效期，避免重複計算。
- [x] **GitHub Actions**: 已補充 `SERPAPI_API_KEY` 環境變數。

---

## 📋 上線前最終確認 (請逐項檢查)

### 1. GitHub Secrets 設定
前往 `https://github.com/YOUR_USERNAME/AI_Stock_Agent/settings/secrets/actions` 確認以下 Secrets 已設定：

- [ ] `MONGODB_URI` (例: `mongodb+srv://user:pass@cluster.mongodb.net/stock_db`)
- [ ] `SERPAPI_API_KEY` (從 https://serpapi.com/manage-api-key 取得)
- [ ] `GEMINI_API_KEY` (從 Google AI Studio 取得)
- [ ] `LINE_TOKEN` (LINE Notify Token)
- [ ] `LINE_USER_ID` (可選)
- [ ] `LINE_GROUP_ID` (可選，若要推群組)
- [ ] `TG_TOKEN` (Telegram Bot Token，可選)
- [ ] `TG_CHAT_ID` (Telegram Chat ID，可選)
- [ ] `PERPLEXITY_API_KEY` (可選，若使用 Perplexity 替代 Gemini)

### 2. 排程驗證
`.github/workflows/daily_analysis.yml` 當前排程：
- **Pre-Market**: 每日 UTC 23:00 (台灣時間隔天 AM 7:00) - 晨間報告
- **Post-Market**: 每日 UTC 13:30 (台灣時間 PM 9:30) - 盤後報告

**建議調整** (美股收盤後):
```yaml
schedule:
  # 美股收盤後 (US Market Close: 4PM ET = 9PM ET = UTC 1AM+1 = 台灣 AM 9:00)
  - cron: '0 1 * * 2-6'  # 周二至周六 UTC 1AM (美股周一-五收盤後)
```

請確認是否符合您的需求。

### 3. 本地測試執行
在正式啟用排程前，請先手動執行一次完整流程：

```powershell
# Dry Run (不發送通知，僅測試邏輯)
python main.py --mode post_market --dry-run

# 實際執行(會發送LINE/TG通知)
python main.py --mode post_market
```

**預期輸出範例**:
```
🟢 NVDA | $135.20 | PASS
📈 高品質 | 🎯 合理價值 | ⚙️ 趨勢向上
📊 ROE: 44.2% | PEG: 1.15 | Debt/Eq: 22%
🔮 AI預測: 強勢看漲 (+3.14%) | 信心: 高 (85%)

📰 MARKET INTELLIGENCE:
Gemini: NVDA財報超預期，AI需求強勁...
```

### 4. Mobile 視覺驗證
請用實體手機瀏覽 `http://YOUR_IP:8501` (或部署後的 URL):

- [ ] 卡片是否垂直堆疊 (非橫向排列)？
- [ ] 字體大小是否舒適 (標題 ~1.8rem，數據 ~2.5rem)？
- [ ] 信心度進度條是否清晰可見？
- [ ] 預測漲跌顏色是否直覺 (綠色 = 上漲，紅色 = 下跌)？
- [ ] 卡片背景色是否符合評級 (綠/黃/紅)？

### 5. 資料庫初始化
確認 MongoDB 中至少有一條測試數據：

```python
# 執行測試腳本 (可選)
python update_db_test.py
```

或者直接跑一次 `main.py`，讓系統自動儲存 Card 數據。

### 6. 手動觸發 GitHub Actions (首次驗證)
1. 前往 `https://github.com/YOUR_USERNAME/AI_Stock_Agent/actions`
2. 點選 `Daily AI Stock Analysis`
3. 點選右上角 `Run workflow`
4. 選擇 `post_market` 模式
5. 點擊綠色 `Run workflow` 按鈕
6. 等待執行完成 (~2-5分鐘)
7. **檢查 LINE/Telegram 是否收到通知**

---

## 🎯 v1.0-RELEASE 發布標準

當以上 6 項全部通過後，即可：

1. **建立 Git Tag**:
   ```bash
   git tag -a v1.0-RELEASE -m "Production Ready: Mobile UI + Regime-Based Prediction"
   git push origin v1.0-RELEASE
   ```

2. **更新 README.md** (可選，建議加入):
   ```markdown
   ## ✨ v1.0 核心功能
   - 🧠 GARP 策略智能評分
   - 🔮 Regime-Based Bootstrap 價格預測 (區分牛熊市)
   - 📱 Mobile-First UI (App 等級體驗)
   - 💾 MongoDB 持久化 + 智能快取
   - 📢 LINE/Telegram 自動推播
   - ⏰ GitHub Actions 定時執行
   ```

3. **慶祝 🎉**: 您已成功打造一個全端 AI 量化產品！

---

## 🔮 未來優化方向 (v1.1+)

- 執行 `stress_test/optimize_thresholds.py` 尋找最佳參數
- 整合 Webhook (即時推播)
- 加入回測績效追蹤儀表板
- 支援自訂觀察清單 (Google Sheets 雙向同步)
