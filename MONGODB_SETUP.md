# MongoDB 環境設定快速指南

## 🎯 目標
在 `.env` 文件中正確設定 MONGODB_URI，啟用 MongoDB 功能

## 📝 設定步驟

### Step 1: 打開 .env 文件
文件位置：`AI_Stock_Agent/.env`

### Step 2: 添加 MONGODB_URI
在文件末尾添加以下行：

```bash
# MongoDB Atlas Connection (Phase 6)
MONGODB_URI=mongodb+srv://admin:<YOUR_PASSWORD>@cluster.mongodb.net/stock_agent?retryWrites=true&w=majority
```

**重要**：將 `<YOUR_PASSWORD>` 替換為您的 MongoDB Atlas 密碼

### Step 3: 完整範例
您的 `.env` 文件應該類似：

```bash
# 您的 SerpApi 金鑰
SERPAPI_API_KEY=<YOUR_SERPAPI_KEY>

# 您的 Google AI Gemini 金鑰
GEMINI_API_KEY=<YOUR_GEMINI_KEY>

SCRAPER_API_KEY=<YOUR_SCRAPER_KEY>
LINE_TOKEN=<YOUR_LINE_TOKEN>
LINE_USER_ID=<YOUR_LINE_USER_ID>
TG_TOKEN=<YOUR_TG_TOKEN>
TG_CHAT_ID=<YOUR_TG_CHAT_ID>
PERPLEXITY_API_KEY=<YOUR_PERPLEXITY_KEY>
LINE_GROUP_ID=<YOUR_LINE_GROUP_ID>

# MongoDB Atlas Connection (Phase 6)
MONGODB_URI=mongodb+srv://admin:YOUR_NEW_PASSWORD@cluster.mongodb.net/stock_agent?retryWrites=true&w=majority
```

### Step 4: 保存文件
按 `Ctrl+S` (Windows) 或 `Cmd+S` (Mac) 保存

### Step 5: 驗證設定
執行測試腳本：
```bash
python test_mongodb_integration.py
```

**預期輸出**：
```
✅ [MongoDB] Connection Successful
✅ Index 'idx_symbol_date' exists
```

## ⚠️ 常見問題

### Q: 我沒有 MongoDB 密碼
**A**: 前往 MongoDB Atlas → Database Access → 編輯用戶 → Edit Password → Autogenerate

### Q: 連線失敗 (ServerSelectionTimeoutError)
**A**: 檢查：
1. 密碼是否正確（特殊字元需 URL 編碼）
2. IP 白名單是否包含您的 IP（或設為 0.0.0.0/0）
3. 網路連線是否正常

### Q: 認證失敗 (AuthenticationFailed)
**A**: 密碼錯誤或用戶名錯誤，重新生成密碼

## 🔒 安全提醒
- ✅ `.env` 已在 `.gitignore` 中，不會被提交
- ❌ 絕不將密碼貼在聊天或文檔中
- ✅ 定期輪換密碼
