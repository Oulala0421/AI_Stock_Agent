# LINE API 訊息發送方式比較

根據 [LINE Messaging API 官方文件](https://developers.line.biz/en/docs/messaging-api/sending-messages/)，LINE 提供多種訊息發送方式。

---

## 📊 API 方式比較

| 方式 | 使用時機 | 需要 | 費用 | 適合 AI Stock Agent？ |
|------|---------|------|------|---------------------|
| **Reply Message** | 回覆用戶訊息 | `replyToken` | ✅ 免費 | ❌ **不適合** |
| **Push Message** | 主動發送到特定對象 | User/Group ID | 💰 計費 | ✅ **適合** (已採用) |
| **Broadcast** | 廣播給所有好友/群組 | 無 | 💰 計費 | ⚠️ 可用（但不精準） |
| **Multicast** | 發送給多個特定對象 | User/Group ID 列表 | 💰 計費 | ⚠️ 未來可用 |

---

## ❌ Reply Message 為何不適合

### 限制條件
1. **需要 replyToken**  
   - Reply Token 只能從 webhook 事件中取得（當用戶發送訊息時）
   - 每個 replyToken 只能使用一次
   - 有時效性（通常幾分鐘內失效）

2. **必須是回應用戶動作**
   - 用戶發送訊息 → Bot 才能回覆
   - 用戶加入群組 → Bot 才能回覆
   - 用戶點擊按鈕 → Bot 才能回覆

3. **AI Stock Agent 的使用場景**
   ```python
   # GitHub Actions 每天 21:00 UTC 自動執行
   python main.py --mode post_market
   
   # 這是主動發送，沒有用戶觸發事件！
   # 沒有 replyToken 可用！
   ```

### 結論
**Reply Message API 不適合**，因為：
- ❌ AI Stock Agent 是**定時自動化**系統（GitHub Actions cron job）
- ❌ 沒有用戶觸發事件
- ❌ 無法取得 replyToken

---

## ✅ 目前採用的方案：Push Message API

### 為什麼選擇 Push Message？

1. **主動發送能力**
   - 可以隨時發送，不需要等待用戶觸發
   - 適合定時排程（GitHub Actions）

2. **精準目標**
   - 可以指定特定 User ID 或 Group ID
   - 不會打擾其他人

3. **實作方式**
   ```python
   # notifier.py 的實作
   url = "https://api.line.me/v2/bot/message/push"
   payload = {
       "to": "C1234567... ",  # 群組 ID (從 webhook 取得)
       "messages": [{"type": "text", "text": "股票分析報告..."}]
   }
   ```

---

## 🎯 您的使用場景總結

### AI Stock Agent 工作流程
```
GitHub Actions (每天 21:00 UTC)
  ↓
執行: python main.py
  ↓
分析股票 (GARP Strategy + Perplexity News)
  ↓
生成報告
  ↓
主動發送到 LINE 群組 (Push API) ← 這裡！
```

### 為何必須用 Push API？
1. 沒有用戶互動（自動化）
2. 需要主動發送（不是回覆）
3. 需要精準發送到特定群組

---

## 🔄 Reply Message 的適用場景（參考）

如果您未來想要**互動功能**，可以考慮：

### 場景 A：用戶查詢特定股票
```
用戶在群組輸入: /AAPL
  ↓
Bot 收到 webhook (包含 replyToken)
  ↓
Bot 立即回覆 AAPL 的即時分析 (使用 Reply API - 免費！)
```

### 場景 B：用戶觸發報表
```
用戶輸入: /report
  ↓
Webhook 觸發
  ↓
Bot 回覆今日股票分析 (Reply API)
```

這種情況下 Reply Message 就很有用，因為：
- ✅ 有 replyToken（用戶觸發）
- ✅ 免費（Reply 不計費）
- ✅ 即時回應

---

## 📝 建議

### 目前階段（已實作）
✅ 繼續使用 **Push Message API**  
✅ 設定 `LINE_GROUP_ID` 環境變數  
✅ 透過 webhook 取得群組 ID

### 未來擴充（可選）
如果您想要互動功能：
1. 保留 `line_webhook_server.py`
2. 部署到雲端（Render/Railway）
3. 實作指令系統（`/AAPL`、`/report`）
4. 使用 Reply API 回應（免費且即時）

這樣就能同時擁有：
- **Push API**: 定時自動報告
- **Reply API**: 即時互動查詢

---

**結論**: Reply Message API 雖然免費，但**不適合**您目前的自動化定時報告需求。Push Message API 是正確選擇！
