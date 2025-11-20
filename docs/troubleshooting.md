# 疑難排解指南

常見問題和解決方案。

## 🔍 問題診斷步驟

### 1. 執行測試腳本

```powershell
# 啟動虛擬環境
.\.venv\Scripts\Activate.ps1

# 執行通知測試
python tests\test_notifications.py
```

測試腳本會自動診斷：
- ✅ Gemini API 連線狀態
- ✅ Telegram Bot Token 和 Chat ID
- ✅ LINE Channel Token 和 User ID

---

## 🐛 常見錯誤

### Gemini API 錯誤

#### `ClientError` 或 `RetryError`

**可能原因**：
1. API Key 無效或過期
2. API Quota 用盡
3. 網路連線問題

**解決方法**：

1. **檢查 API Key**
   - 前往 [Google AI Studio](https://aistudio.google.com/app/apikey)
   - 確認 API Key 狀態
   - 如需要，重新產生新的 Key

2. **檢查 Quota**
   - 前往 [Google Cloud Console](https://console.cloud.google.com/apis/dashboard)
   - 查看 Generative Language API 使用量
   - 免費額度：每分鐘 60 requests

3. **測試連線**
   ```powershell
   python tests\test_notifications.py
   ```

---

### Telegram 錯誤

#### `404 Not Found`

**錯誤訊息**：
```json
{"ok":false,"error_code":404,"description":"Not Found"}
```

**原因**：Chat ID 錯誤或格式不正確

**解決方法**：

1. **重新取得 Chat ID**（參考 `docs/setup_guide.md`）
   
   方法 A：透過 API
   ```
   1. 傳送訊息給你的 Bot
   2. 開啟：https://api.telegram.org/botYOUR_TOKEN/getUpdates
   3. 找到 "chat":{"id":XXXXXXX}
   ```
   
   方法 B：使用 @userinfobot
   ```
   1. 搜尋 @userinfobot
   2. 傳送 /start
   3. Bot 會回覆你的 User ID
   ```

2. **確認 Chat ID 格式**
   - 單人聊天：正數（例如：`987654321`）
   - 群組聊天：負數（例如：`-1001234567890`）
   - **保留正負號**

3. **更新設定**
   - 本地：更新 `.env` 檔案中的 `TG_CHAT_ID`
   - GitHub：更新 Repository Secret `TG_CHAT_ID`

#### `401 Unauthorized`

**原因**：Bot Token 錯誤

**解決方法**：
1. 確認 Token 格式：`數字:字母數字` (例如：`123456789:ABCdef...`)
2. 重新從 @BotFather 取得 Token
3. 更新 `.env` 和 GitHub Secret

---

### LINE 錯誤

#### `The property, 'to', in the request body is invalid`

**原因**：User ID 格式錯誤或無法使用 Push API

**解決方法**：

**選項 A：改用 Broadcast API（推薦）**

修改 `notifier.py` 的 `send_line` 函式：

```python
def send_line(message, token):
    if not token: return
    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    payload = {
        "messages": [{
            "type": "text",
            "text": message[:5000]
        }]
    }
    
    try:
        r = requests.post(url, headers=headers, json=payload)
        if r.status_code != 200:
            print(f"❌ LINE 發送失敗: {r.text}")
        else:
            print("✅ LINE 發送成功")
    except Exception as e:
        print(f"❌ LINE 錯誤: {e}")
```

**選項 B：使用正確的 User ID**

LINE User ID 格式：`U` + 32 個字元（例如：`Uabcd1234efgh5678ijkl9012mnop3456`）

取得方式（需要設定 Webhook）：
1. 建立接收 Webhook 的伺服器
2. 用戶傳送訊息後，從 `userId` 欄位取得

#### `400 Bad Request - Invalid access token`

**原因**：Channel Access Token 錯誤

**解決方法**：
1. 前往 [LINE Developers Console](https://developers.line.biz/console/)
2. 進入你的 Channel
3. 前往 "Messaging API" 頁籤
4. 重新 Issue Channel Access Token
5. 更新 `.env` 和 GitHub Secret

---

## 🔄 GitHub Actions 問題

### Workflow 執行失敗

#### 檢查執行日誌

1. GitHub Repository → **Actions** 標籤
2. 點選失敗的 Workflow run
3. 查看 "Run Analysis" step 的詳細日誌

#### 常見問題

**問題 1：Secrets 未設定**

**症狀**：
```
⚠️ 未設定 Gemini API Key
❌ TG 發送失敗 (第1段)
   Response: {"ok":false,"error_code":404...}
```

**解決**：
1. Settings → Secrets and variables → Actions
2. 確認所有 Secrets 都已設定：
   - `GEMINI_API_KEY`
   - `TG_TOKEN`
   - `TG_CHAT_ID`
   - `LINE_TOKEN`
   - `LINE_USER_ID` (或留空改用 Broadcast)
   - `GCP_JSON`

**問題 2：排程時間錯誤**

**症狀**：沒有在預期時間收到通知

**檢查**：
- Pre-market: `13:30 UTC` = 台灣時間 21:30
- Post-market: `21:00 UTC` = 台灣時間 05:00 (隔天)

**修改排程**（如需要）：
編輯 `.github/workflows/daily_analysis.yml`:
```yaml
on:
  schedule:
    # 台灣時間 21:30 = UTC 13:30
    - cron: '30 13 * * 1-5'
```

---

## 🧪 本地測試流程

### 完整測試步驟

```powershell
# 1. 設置虛擬環境
.\setup_venv.ps1

# 2. 啟動虛擬環境
.\.venv\Scripts\Activate.ps1

# 3. 測試 API 連線
python tests\test_notifications.py

# 4. Dry Run（不發送通知）
python main.py --mode post_market --dry-run

# 5. 實際發送測試
python main.py --mode post_market
```

### 預期結果

**測試腳本**：
- ✅ Gemini API 連線成功
- ✅ Telegram 發送測試訊息
- ✅ LINE 發送測試訊息

**Dry Run**：
- ✅ 所有股票分析正常
- ✅ 報告內容顯示在終端機

**實際發送**：
- ✅ 收到 Telegram 通知
- ✅ 收到 LINE 通知

---

## 📝 檢查清單

完成以下項目確保系統正常運作：

### 本地環境
- [ ] Python 虛擬環境已建立
- [ ] `.env` 檔案已設定並包含所有必要的 Keys
- [ ] `python tests\test_notifications.py` 全部通過
- [ ] `python main.py --dry-run` 執行無錯誤

### GitHub 設定
- [ ] 所有 Secrets 已正確設定
- [ ] Workflow 手動執行成功
- [ ] 收到測試通知（Telegram 和 LINE）

### 排程驗證
- [ ] 等待下一個排程時間
- [ ] 確認有收到自動通知
- [ ] 檢查 Actions 執行日誌

---

## 🆘 仍然無法解決？

1. **檢查日誌**
   - GitHub Actions 日誌
   - 本地執行輸出

2. **重新設定**
   - 刪除並重建 Bot/Channel
   - 重新產生 API Keys
   - 更新所有 Secrets

3. **聯繫支援**
   - [Google AI Studio 論壇](https://discuss.ai.google.dev/)
   - [Telegram Bot API 文件](https://core.telegram.org/bots/api)
   - [LINE Developers Forum](https://developers.line.biz/en/community/)
