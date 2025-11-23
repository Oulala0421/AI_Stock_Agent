# AI Stock Agent - LINE 整合完整流程

這是一份快速參考指南，幫助您完成 LINE 群組通知設定。

---

## 🎯 目標

讓 AI Stock Agent 自動發送股票分析報告到您的 LINE 群組。

---

## 📋 完整流程速查表

### 階段 1：取得 LINE 群組 ID（需要一次性設定）

#### 方法 A：使用 Render.com（推薦 - 永久 URL）

1. **部署 Webhook 伺服器到 Render**
   - 詳細步驟：[RENDER_DEPLOYMENT_GUIDE.md](./RENDER_DEPLOYMENT_GUIDE.md)
   - 簡要：
     ```
     1. 推送代碼到 GitHub
     2. 在 Render.com 建立 Web Service
     3. 連接 GitHub repository
     4. Start Command: python line_webhook_server.py
     5. 部署後取得 URL: https://YOUR-APP.onrender.com
     ```

2. **設定 LINE Developers**
   - Webhook URL: `https://YOUR-APP.onrender.com/webhook`
   - 啟用「Use webhook」
   - 關閉自動回覆

3. **取得群組 ID**
   - 將 Bot 加入 LINE 群組
   - 在群組發送任意訊息
   - 查看 Render Logs 中的群組 ID
   - 複製群組 ID（格式：Cxxxxx...）

#### 方法 B：使用 ngrok（本地測試）

詳見：[LINE_WEBHOOK_SETUP.md](./LINE_WEBHOOK_SETUP.md)

---

### 階段 2：設定環境變數

在 `.env` 檔案加入：

```env
# LINE 設定
LINE_TOKEN=你的Channel_Access_Token
LINE_GROUP_ID=Cxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # 從 webhook 取得
```

**重要**：
- `LINE_USER_ID` 可以留空或刪除
- 系統會優先使用 `LINE_GROUP_ID`

---

### 階段 3：測試發送

```powershell
# 測試 LINE 群組發送
python test_line_group.py
```

**預期結果**：
```
✅ LINE 發送成功 (群組推送 (Group ID: Cxxxxxxx...))
```

然後在 LINE 群組中就會看到測試訊息！

---

### 階段 4：執行完整測試

```powershell
# Dry-run 模式（不會真的在非開市時間發送）
python main.py --dry-run
```

---

### 階段 5：GitHub Actions 設定

在 GitHub Repository 設定 Secret：

```
Settings → Secrets → Actions → New repository secret

Name: LINE_GROUP_ID
Value: Cxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**注意**：如果已經用 `LINE_USER_ID`，可以刪除並改用 `LINE_GROUP_ID`

---

## 🔄 三種發送模式比較

| 模式 | 設定方式 | 優點 | 缺點 |
|------|---------|------|------|
| **群組推送** | 設定 `LINE_GROUP_ID` | ✅ 精準<br>✅ 只發送到特定群組 | 需要一次性 webhook 設定 |
| **個人推送** | 設定 `LINE_USER_ID` | ✅ 發送給個人 | 需要取得 User ID |
| **廣播** | 兩者都不設定 | ✅ 最簡單 | ❌ 發送給所有好友和群組 |

**推薦**：使用 **群組推送**（LINE_GROUP_ID）

---

## 📚 詳細文件

1. **[LINE_WEBHOOK_SETUP.md](./LINE_WEBHOOK_SETUP.md)**  
   - Webhook 概念說明
   - 本地測試（ngrok）
   - 取得群組 ID 的完整步驟

2. **[RENDER_DEPLOYMENT_GUIDE.md](./RENDER_DEPLOYMENT_GUIDE.md)**  
   - Render.com 部署教學（推薦）
   - 永久 HTTPS Webhook URL
   - 故障排除

3. **[LINE_API_COMPARISON.md](./LINE_API_COMPARISON.md)**  
   - Reply vs Push vs Broadcast API 比較
   - 為什麼選擇 Push API
   - 各種 API 的適用場景

4. **[LINE_GROUP_SETUP.md](./LINE_GROUP_SETUP.md)**  
   - 群組設定指南
   - 常見問題排解

---

## ⚡ 快速開始（TL;DR）

最快的方式（假設已有 LINE Bot）：

```powershell
# 1. 部署 webhook 到 Render
# （跟隨 RENDER_DEPLOYMENT_GUIDE.md）

# 2. 設定 LINE Developers Webhook URL
# https://YOUR-APP.onrender.com/webhook

# 3. Bot 加入 LINE 群組，發送訊息取得群組 ID

# 4. 設定 .env
echo "LINE_GROUP_ID=Cxxxxxx..." >> .env

# 5. 測試
python test_line_group.py

# 6. GitHub Actions Secret
# LINE_GROUP_ID = Cxxxxxx...

# 7. 完成！
```

---

## 🆘 常見問題速查

### Q: 如何取得 LINE Bot？
A: 前往 https://developers.line.biz/ 建立 Messaging API Channel

### Q: 需要付費嗎？
A: 
- LINE Bot: 免費（Free plan 500 則/月）
- Render.com: 免費（750 小時/月）
- Push Message: 計費（但有免費額度）

### Q: LINE_GROUP_ID 和 LINE_USER_ID 可以同時設定嗎？
A: 可以，但系統會優先使用 `LINE_GROUP_ID`

### Q: Webhook 取得群組 ID 後，還需要保持運行嗎？
A: 不需要。取得 ID 後可以暫停或刪除 Render 服務

### Q: 如何確認設定正確？
A: 執行 `python test_line_group.py`，如果 LINE 群組收到訊息就成功了！

---

## 📞 需要幫助？

參考各別文件的故障排除章節：
- Render 部署問題 → [RENDER_DEPLOYMENT_GUIDE.md](./RENDER_DEPLOYMENT_GUIDE.md)
- Webhook 問題 → [LINE_WEBHOOK_SETUP.md](./LINE_WEBHOOK_SETUP.md)
- API 選擇問題 → [LINE_API_COMPARISON.md](./LINE_API_COMPARISON.md)

---

**最後更新**: 2025-11-23  
**版本**: Phase 4 - GARP + LINE Webhook Integration
