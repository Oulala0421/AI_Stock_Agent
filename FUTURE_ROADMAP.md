# 🚀 AI Stock Agent - Future Roadmap & Technical Audit

**Last Updated**: 2025-11-23
**Status**: Phase 5 Completed (LINE Integration & Market Outlook)

---

## 🔍 Deep Code Review & Logic Audit

### ✅ Current System Health
- **Core Logic**: GARP Strategy implementation is robust and verified against academic formulas.
- **Error Handling**: Defensive programming is implemented across all external API calls (Perplexity, LINE, Telegram, Google Sheets).
- **Cost Optimization**: Smart news fetching logic effectively reduces API usage by ~50-70%.
- **Notification**: Multi-channel delivery (LINE Group + Telegram) is fully functional.

### ⚠️ Identified Areas for Improvement

#### 1. Logging System
- **Current**: Uses `print()` statements for logging.
- **Issue**: Hard to debug in production environments (e.g., GitHub Actions) without structured logs.
- **Recommendation**: Implement Python's built-in `logging` module with file rotation and log levels (INFO, ERROR, DEBUG).

#### 2. Configuration Management
- **Current**: Mix of `config.yaml` and `.env`.
- **Issue**: Some strategy parameters are hardcoded or scattered.
- **Recommendation**: Centralize all strategy thresholds (e.g., PEG < 1.5, ROE > 15%) into `config.yaml` for easier tuning without code changes.

#### 3. Test Coverage
- **Current**: High coverage for integration tests (`test_phase4_functionality.py`), but lower for unit tests.
- **Issue**: `garp_strategy.py` relies heavily on integration tests.
- **Recommendation**: Add dedicated unit tests for `calculate_garp_score` using `pytest` and mocked data.

#### 4. Type Safety
- **Current**: Partial type hinting.
- **Issue**: Some functions lack return type annotations.
- **Recommendation**: Enforce strict type checking with `mypy` in CI/CD pipeline.

---

## 🗺️ Future Roadmap

### Phase 6: Advanced Analytics & Data Persistence (Q1 2026)

#### 1. Database Integration (SQLite/PostgreSQL)
- **Goal**: Store historical analysis results.
- **Why**: Enable trend analysis (e.g., "Is AAPL's GARP score improving over time?").
- **Implementation**: Use `SQLAlchemy` ORM.

#### 2. Performance Tracking Dashboard
- **Goal**: Visualize portfolio performance vs. SPY.
- **Why**: Better insight into strategy effectiveness.
- **Implementation**: Streamlit or Dash web app.

#### 3. Sentiment Trend Analysis
- **Goal**: Track news sentiment changes over time.
- **Why**: Detect shifts in market narrative before price action.
- **Implementation**: Store VADER scores in DB and calculate moving averages.

### Phase 7: Interactive Features (Q2 2026)

#### 1. Two-Way LINE Bot
- **Goal**: Allow users to query stock status via LINE (e.g., `/analyze TSLA`).
- **Why**: On-demand analysis without waiting for daily reports.
- **Implementation**: Expand `line_webhook_server.py` to handle text messages.

#### 2. Portfolio Rebalancing Alerts
- **Goal**: Notify when portfolio weights drift significantly from 70/30.
- **Why**: Automate risk management.
- **Implementation**: Weekly check in `main.py`.

### Phase 8: Multi-Strategy Support (Q3 2026)

#### 1. Dividend Growth Strategy
- **Goal**: Add a new strategy module for income-focused investing.
- **Why**: Diversify investment styles.
- **Implementation**: Create `dividend_strategy.py` inheriting from a base `Strategy` class.

#### 2. Technical Swing Trading
- **Goal**: Short-term trading based on RSI/MACD divergence.
- **Why**: Capture short-term volatility.

---

## 📝 Maintenance Schedule

- **Weekly**: Check GitHub Actions logs for API failures.
- **Monthly**: Review Perplexity API usage and costs.
- **Quarterly**: Backtest strategy against recent market data and adjust `config.yaml` thresholds.

---

## 💡 User Feedback Loop

Please update this document as you discover new needs or issues. This roadmap is a living document.
