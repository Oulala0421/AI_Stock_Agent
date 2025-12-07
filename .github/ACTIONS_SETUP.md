# GitHub Actions Setup for Phase 4

This document describes the required GitHub Secrets configuration for the AI Stock Agent Phase 4 (GARP + News Intelligence).

## Required Secrets

Navigate to: **GitHub Repository → Settings → Secrets and variables → Actions**

### 1. Google Sheets Access
- **`GCP_JSON`**: Service account JSON credentials for Google Sheets API
  - Format: Complete JSON object from Google Cloud Console
  - Used by: `sheet_manager.py` to fetch Holdings and Watchlist

### 2. Telegram Integration (Optional)
- **`TG_TOKEN`**: Telegram Bot API token
  - Get from: [@BotFather](https://t.me/botfather)
- **`TG_CHAT_ID`**: Your Telegram chat ID
  - Get from: [@userinfobot](https://t.me/userinfobot)

### 3. LINE Integration (Optional)
- **`LINE_TOKEN`**: LINE Messaging API Channel Access Token
- **`LINE_USER_ID`**: Your LINE user ID or leave empty for broadcast

### 4. AI Services
- **`GEMINI_API_KEY`**: Google Gemini API key (legacy, may be removed in future)
  - Get from: [Google AI Studio](https://makersuite.google.com/app/apikey)
- **`PERPLEXITY_API_KEY`**: ⭐ **NEW in Phase 4** - Perplexity AI API key
  - Get from: [Perplexity AI](https://www.perplexity.ai/)
  - **IMPORTANT**: This is required for news intelligence features

### 5. Database (Phase 6+)
- **`MONGODB_URI`**: ⭐ **NEW in Phase 6** - MongoDB connection string
  - Get from: [MongoDB Atlas](https://cloud.mongodb.com/)
  - Format: `mongodb+srv://username:password@cluster.mongodb.net/stock_agent`
  - **IMPORTANT**: Required for stateful analysis and historical tracking
  - Fallback: If not set, system will warn but continue with limited features

## Setting Up Secrets

### Via GitHub Web UI
```
1. Go to your repository
2. Click Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Name: PERPLEXITY_API_KEY
5. Value: [your API key from Perplexity]
6. Click "Add secret"
```

### Via GitHub CLI (Optional)
```bash
gh secret set PERPLEXITY_API_KEY --body "pplx-xxxxxxxxxxxxx"
gh secret set GCP_JSON --body "$(cat service_account.json)"
gh secret set TG_TOKEN --body "your_telegram_token"
gh secret set TG_CHAT_ID --body "your_chat_id"
```

## Workflow Triggers

### Automatic (Scheduled)
- **Pre-Market**: 13:30 UTC (9:30 PM Taiwan / 9:30 AM EST)
- **Post-Market**: 21:00 UTC (5:00 AM Taiwan / 5:00 PM EST)
- Active: Monday-Friday only

### Manual (Workflow Dispatch)
```
1. Go to Actions tab
2. Select "Daily AI Stock Analysis"
3. Click "Run workflow"
4. Choose mode: pre_market or post_market
5. Click "Run workflow"
```

## Verifying Setup

After adding secrets, test the workflow:

1. **Manual Test**:
   ```
   Actions → Daily AI Stock Analysis → Run workflow → post_market
   ```

2. **Check Output**:
   - Should see "🚀 AI Stock Agent (GARP + News) 啟動中..."
   - News fetching should work (not show "News unavailable")
   - Reports sent to Telegram/LINE

3. **Common Issues**:
   - ❌ "News unavailable (API key not configured)" → Check PERPLEXITY_API_KEY secret
   - ❌ Google Sheets error → Check GCP_JSON formatting
   - ❌ No messages received → Check TG_TOKEN/LINE_TOKEN

## Phase 4 Changes

### What's New
- Added `PERPLEXITY_API_KEY` secret requirement
- Workflow unchanged (still uses `python main.py`)
- Same schedule and triggers

### Migration from Phase 3
If upgrading from older versions:
1. ✅ Keep existing secrets (GCP_JSON, TG_TOKEN, etc.)
2. ➕ Add only `PERPLEXITY_API_KEY`
3. ✅ No other changes needed

## Phase 6 Changes (MongoDB)

### What's New
- Added `MONGODB_URI` secret requirement for stateful analysis
- Database migrated from SQLite to MongoDB
- Enables historical tracking and status change detection

### Migration from Phase 4/5
If upgrading to Phase 6:
1. ✅ Keep all existing secrets
2. ➕ Add `MONGODB_URI` from MongoDB Atlas
3. ⚠️ **Optional**: SQLite data (`stocks.db`) will not be auto-migrated
4. ✅ System will work without MongoDB (with warning)

---

**Last Updated**: 2025-12-07 (Phase 6 Release - MongoDB)  
**Maintainer**: Antigravity AI
