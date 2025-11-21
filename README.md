# 🤖 AI Stock Agent

**Academic-Grade Core/Satellite Investment Strategy with Daily Telegram & LINE Notifications**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Actions](https://img.shields.io/badge/CI/CD-GitHub_Actions-2088FF?logo=github-actions)](https://github.com/features/actions)

---

## 📊 Overview

AI Stock Agent is a quantitative investment system that implements a **Core/Satellite portfolio strategy** based on academic research from Fama-French, Carhart, and modern factor investing literature. The system analyzes stocks daily, generates AI-powered briefings using Gemini API, and sends notifications via Telegram and LINE.

### Key Features

✨ **Dual-Formula Scoring System**
- **Core (70%)**: Long-term ETF holdings with DCA (Dollar Cost Averaging)
- **Satellite (30%)**: Alpha-seeking individual stocks with flexible position sizing

📈 **Multi-Factor Analysis**
- Value (HML) - Price-to-intrinsic-value ratios
- Momentum (UMD) - Dual momentum strategy
- Quality (RMW) - ROE and profitability metrics
- Market Sentiment - VIX regime analysis

🔬 **Academic Validation**
- 10-year stress test (2014-2024) with **CAGR 16.52%**
- Monte Carlo simulation (100,000 iterations) for risk assessment
- Tested against 2015 Flash Crash, 2018 Trade War, 2020 COVID, 2022 Bear Market

🤖 **AI Integration**
- Google Gemini API for investment briefings
- Sentiment analysis with VADER
- RSI Percentile Ranking (dynamic technical analysis)

📱 **Daily Notifications**
- Telegram (detailed private reports)
- LINE (public-friendly summaries)
- Scheduled via GitHub Actions (Taiwan Time 21:30)

---

## 🎯 Performance (Backtest 2014-2024)

| Metric | Value |
|--------|-------|
| **CAGR** | 16.52% |
| **Max Drawdown** | -21.2% (2022 Bear Market) |
| **Sharpe Ratio** | 0.91 |
| **Total Return** | +387.89% |
| **95% VaR** (1-year forward) | -13.3% |
| **Bankruptcy Risk** | 0.00% |

### Stress Test Results

| Event | Return | Evaluation |
|-------|--------|-----------|
| 2015 Flash Crash | +2.3% | ✅ Resilient |
| 2018 Trade War | -8.1% | ⚠️ Moderate Impact |
| 2020 COVID | -15.7% | ✅ V-Shape Recovery |
| 2022 Bear Market | **-21.2%** | ❌ Maximum Stress |

📄 Full analysis: [`stress_test/stress_test_report.md`](stress_test/stress_test_report.md)

---

## 🏗️ Architecture

```
AI_Stock_Agent/
├── main.py                  # Entry point (pre_market / post_market modes)
├── strategy.py              # Core/Satellite scoring formulas
├── market_data.py           # yfinance data fetching + technical indicators
├── notifier.py              # Telegram & LINE notification senders
├── sheet_manager.py         # Google Sheets integration (holdings/watchlist)
├── config.yaml              # Strategy parameters
├── .env                     # API keys (local only, not in git)
│
├── docs/
│   ├── setup_guide.md       # Step-by-step setup instructions
│   └── troubleshooting.md   # Common issues & solutions
│
├── stress_test/             # Academic analysis & backtesting
│   ├── run_stress_test.py   # 10-year backtest + Monte Carlo
│   ├── formula_analysis_report.md  # Literature review (Fama-French, etc.)
│   └── stress_test_report.md       # Backtest results
│
└── .github/workflows/
    └── daily_analysis.yml   # Automated daily notifications (21:30 Taiwan Time)
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Google Sheets with Holdings/Watchlist (see [`docs/setup_guide.md`](docs/setup_guide.md))
- API Keys:
  - **Gemini API** (for AI briefings)
  - **Telegram Bot** (for notifications)
  - **LINE Messaging API** (optional)
  - **Google Cloud** (for Sheets access)

### Installation

#### 1. Clone Repository
```bash
git clone https://github.com/Oulala0421/AI_Stock_Agent.git
cd AI_Stock_Agent
```

#### 2. Setup Virtual Environment (Windows)
```powershell
.\setup_venv.ps1
```

Or manually:
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

#### 3. Configure API Keys
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

Edit .env:
```env
GEMINI_API_KEY=your_gemini_api_key
TG_TOKEN=your_telegram_bot_token
TG_CHAT_ID=your_telegram_chat_id
LINE_TOKEN=your_line_channel_token
LINE_USER_ID=your_line_user_id
GCP_JSON={"type":"service_account", ...}
```

📘 **Detailed Setup Guide**: [`docs/setup_guide.md`](docs/setup_guide.md)

#### 4. Test Locally
```bash
# Test API connections
python tests/test_notifications.py

# Dry run (no notifications sent)
python main.py --dry-run

# Real run (post-market analysis)
python main.py
```

---

## ⚙️ Configuration

### Strategy Parameters (`config.yaml`)

```yaml
capital_allocation:
  core_pool: 11900        # 70% - Academic standard (Vanguard 2016)
  satellite_pool: 5100    # 30%

strategy:
  core:
    threshold_buy: 55     # Relaxed for DCA
    threshold_sell: 35
  satellite:
    threshold_buy: 70     # Strict for alpha
    threshold_accumulate: 65
    threshold_reduce: 35
```

### Google Sheets Format

**Holdings Sheet**:
| Symbol | Type | Cost |
|--------|------|------|
| VOO | Core | 450 |
| NVDA | Satellite | 120 |

**Watchlist Sheet**:
| Symbol | Type |
|--------|------|
| PLTR | Satellite |
| QQQ | Core |

---

## 📱 GitHub Actions Automation

The system runs automatically at **21:30 Taiwan Time** (13:30 UTC) via GitHub Actions.

### Setup GitHub Secrets

1. Go to `Settings` → `Secrets and variables` → `Actions`
2. Add the following secrets:
   - `GEMINI_API_KEY`
   - `TG_TOKEN`
   - `TG_CHAT_ID`
   - `LINE_TOKEN`
   - `LINE_USER_ID`
   - `GCP_JSON`

### Manual Trigger

Go to `Actions` → `Daily AI Stock Analysis` → `Run workflow`

---

## 🧪 Stress Testing

Run the 10-year backtest + Monte Carlo simulation:

```bash
python -m stress_test.run_stress_test
```

Output:
- Terminal: CAGR, Max DD, Sharpe Ratio
- Report: `stress_test/stress_test_report.md`

**Monte Carlo Settings**:
- Iterations: 100,000 (academic standard per Jorion 2007, Hull 2018)
- Simulation period: 1 year (252 trading days)
- Method: GBM (Geometric Brownian Motion)

---

## 📚 Academic Foundation

This system is built on peer-reviewed financial research:

### Core Theories
- **Fama-French 3/5-Factor Models** (1993, 2015) - Size, Value, Profitability
- **Carhart 4-Factor** (1997) - Momentum
- **Dual Momentum** (Antonacci 2014) - Absolute + Relative momentum
- **Core-Satellite Strategy** (Vanguard 2016) - 70/30 allocation
- **Kelly Criterion** (1956) - Optimal position sizing

### Technical Innovations
- **RSI Percentile Ranking**: Dynamic overbought/oversold thresholds
- **Bollinger Band Positioning**: Value entry timing
- **VIX Regime Analysis**: Market sentiment quantification

📄 Full literature review: [`stress_test/formula_analysis_report.md`](stress_test/formula_analysis_report.md)

---

## 🔧 Troubleshooting

### Common Issues

**Gemini API Error**:
```
⚠️ AI 生成最終失敗: ClientError
```
→ Check API key validity & quota

**Telegram 404 Error**:
```
❌ TG 發送失敗: {"ok":false,"error_code":404}
```
→ Verify Chat ID (should be a number, not username)

**LINE Invalid Property**:
```
❌ LINE 發送失敗: "to" property invalid
```
→ Use User ID (starts with `U`), not Display Name

📘 **Full Troubleshooting Guide**: [`docs/troubleshooting.md`](docs/troubleshooting.md)

---

## 📜 License

MIT License - See [LICENSE](LICENSE)

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## ⚠️ Disclaimer

**This software is for educational and research purposes only.**
- Not financial advice
- Past performance does not guarantee future results
- Use at your own risk
- Authors assume no liability for financial losses

---

## 📞 Contact

**Project Maintainer**: [@Oulala0421](https://github.com/Oulala0421)

**Issues**: [GitHub Issues](https://github.com/Oulala0421/AI_Stock_Agent/issues)

---

## 🌟 Acknowledgments

- **Gemini API** by Google
- **yfinance** by Ran Aroussi
- **Fama-French Data Library**
- Academic research by Eugene Fama, Kenneth French, Mark Carhart, Clifford Asness

---

<p align="center">Made with ❤️ and 📊 by quants, for quants</p>