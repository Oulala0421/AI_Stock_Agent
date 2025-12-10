# 🤖 AI Stock Agent (GARP + News Intelligence)

**Academic-Grade Core/Satellite Investment Strategy with AI-Powered News & Multi-Channel Notifications**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Actions](https://img.shields.io/badge/CI/CD-GitHub_Actions-2088FF?logo=github-actions)](https://github.com/features/actions)

---

## 📊 Overview

AI Stock Agent 是一個結合**量化策略 (GARP)** 與 **AI 新聞情報 (Perplexity)** 的自動化投資分析系統。它每天自動分析持股與觀察清單，生成專業的投資報告，並透過 **LINE 群組** 與 **Telegram** 發送通知。

### Key Features

✨ **GARP 核心/衛星策略**
- **Core (70%)**: 長期持有 ETF，強調低成本與穩定性
- **Satellite (30%)**: 追求 Alpha 的個股，使用 GARP (Growth at a Reasonable Price) 模型評分

🧠 **AI News Intelligence**
- **Perplexity AI 整合**: 自動搜尋並摘要個股最新重大新聞
- **智能成本控管**: 僅針對評級為 `PASS` 或 `WATCHLIST` 的股票獲取新聞
- **市場情緒分析**: 結合 VIX 與 SPY 趨勢判斷市場體質

📱 **多管道通知系統**
- **LINE 群組推送**: 支援 Webhook 自動獲取群組 ID，將報告發送到指定群組
- **Telegram Bot**: 發送詳細的 Markdown 格式報告
- **休市日簡報**: 美股休市時自動發送市場概況 (VIX/SPY)，不中斷服務

⚙️ **自動化運維**
- **GitHub Actions**: 每日定時執行 (包含週末)
- **Render Webhook**: 用於自動獲取 LINE 群組 ID
- **Google Sheets**: 雲端管理持股與觀察清單

---

## 🏗️ Architecture

```
AI_Stock_Agent/
├── main.py                  # 主程式 (整合策略、新聞、通知)
├── garp_strategy.py         # GARP 策略邏輯 (Valuation, Growth, Quality)
├── news_agent.py            # Perplexity AI 新聞代理人
├── notifier.py              # LINE & Telegram 通知模組
├── line_webhook_server.py   # Flask Webhook Server (用於取得群組 ID)
├── market_data.py           # yfinance 數據獲取
├── sheet_manager.py         # Google Sheets 連接器
├── config.py                # 設定管理
├── .env                     # API Keys (不在此 repo 中)
│
├── docs/                    # 詳細文件
│   ├── LINE_INTEGRATION_GUIDE.md  # LINE 群組整合指南
│   ├── RENDER_DEPLOYMENT_GUIDE.md # Render 部署教學
│   └── ...
│
└── .github/workflows/
    └── daily_analysis.yml   # 每日自動執行排程
```

---

## 🚀 Quick Start

### 1. 環境準備
- Python 3.9+
- Google Sheets (格式參考 `docs/setup_guide.md`)
- API Keys:
  - **Perplexity API** (新聞摘要)
  - **LINE Messaging API** (通知)
  - **Telegram Bot** (通知)
  - **Google Cloud** (Sheets 存取)

### 2. 安裝
```bash
git clone https://github.com/Oulala0421/AI_Stock_Agent.git
cd AI_Stock_Agent
pip install -r requirements.txt
```

### 3. 設定 .env
複製 `.env.example` 並填入您的金鑰：
```env
PERPLEXITY_API_KEY=pplx-xxxxxxxx...
LINE_TOKEN=xxxxxxxx...
LINE_GROUP_ID=Cxxxxxxxx...  # 執行 line_webhook_server.py 取得
TG_TOKEN=xxxxxxxx...
TG_CHAT_ID=xxxxxxxx...
GCP_JSON={...}
```

### 4. 取得 LINE 群組 ID
詳見 [LINE_INTEGRATION_GUIDE.md](docs/LINE_INTEGRATION_GUIDE.md)
1. 部署 `line_webhook_server.py` 到 Render
2. 設定 LINE Webhook URL
3. 將 Bot 加入群組並發送訊息
4. 從 Logs 取得 Group ID

### 5. 執行測試
```bash
# 測試 LINE 群組發送
python test_line_group.py

# 執行完整分析 (Dry Run)
python main.py --dry-run
```

---

## 🔮 V2.0: Deep Value & Sentiment Engine

New in Version 2.0:
- **Sentiment-Adjusted DCF**: 內在價值模型會根據市場情緒 (Z-Score) 動態調整折現率。
  - 市場貪婪 (Z > 1) -> 折現率提高 (懲罰估值)
  - 市場恐慌 (Z < -1) -> 折現率降低 (挖掘機會)
- **Private Risk Engine**: 針對持倉進行「集中度」與「連動性」風險檢查 (Portfolio Manager)。
- **Visual War Room**: 升級版 Streamlit 戰情室 (`app.py`)。

---

## 📈 Strategy Logic (GARP)

系統根據以下指標進行評分 (0-10 分)：

1.  **Valuation (估值)**: PEG Ratio, P/E vs Industry, **DCF Margin of Safety**
2.  **Growth (成長)**: Revenue Growth, EPS Growth
3.  **Quality (品質)**: ROE, Net Margin, Debt/Equity
4.  **Technical (技術)**: RSI, Moving Averages

**評級標準**:
- 🟢 **PASS**: 總分 >= 7 且無重大紅旗 (Deep Value > 15% 優先)
- 🟡 **WATCHLIST**: 總分 >= 5
- 🔴 **REJECT**: 總分 < 5 或有重大紅旗

---

## 📅 Automation Schedule

系統透過 GitHub Actions 每日執行：

- **時間**: 21:30 (台灣時間) / 13:30 (UTC)
- **頻率**: 每天 (Every Day)
- **行為**:
  - **開市日**: 完整個股分析 + 新聞 + 報告
  - **休市日**: 市場概況簡報 (VIX/SPY) + 休市提示

---

## 🤝 Contributing

歡迎提交 Pull Request 或 Issue！

## 📜 License

MIT License