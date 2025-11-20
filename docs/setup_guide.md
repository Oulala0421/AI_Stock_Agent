# AI Stock Agent 設定指南

完整的 API 設定和 GitHub Secrets 配置指南。

## 📋 前置條件

1. **Gemini API Key** - Google AI Studio
2. **Telegram Bot** - Telegram BotFather
3. **LINE Messaging API** - LINE Developers Console
4. **GitHub Account** - 用於設定 Secrets

---

## 🔑 1. Gemini API Key 設定

### 取得 API Key

1. 前往 [Google AI Studio](https://aistudio.google.com/app/apikey)
2. 點擊 **"Create API Key"**
3. 選擇現有的 Google Cloud 專案（或建立新專案)
4. 複製產生的 API Key

### 檢查 Quota

1. 前往 [Google Cloud Console - APIs](https://console.cloud.google.com/apis/dashboard)
2. 選擇你的專案
3. 查看 **Generative Language API** 的使用量
4. 確認沒有超過免費額度或付費限制

### 常見問題

- **ClientError**: API Key 無效或已過期
- **Quota exceeded**: 免費額度用盡，需升級或等待重置

---

## 💬 2. Telegram 設定

### 建立 Bot 並取得 Token

1. 在 Telegram 搜尋 **@BotFather**
2. 發送 `/newbot` 命令
3. 按照指示設定 Bot 名稱
4. 複製 BotFather 提供的 **HTTP API Token**（格式：`123456789:ABCdefGHIjklMNOpqrsTUVwxyz`）

### 取得正確的 Chat ID

**方法 1：透過 API（推薦）**

1. 開啟你剛建立的 Bot
2. 傳送任何訊息給 Bot（例如：`/start`）
3. 在瀏覽器開啟以下網址（替換 `YOUR_BOT_TOKEN`）:
   ```
   https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
   ```
4. 找到 JSON 回應中的 `"chat":{"id":XXXXXXX}`
5. 複製這個數字（可能是正數或負數，**保留正負號**）

**範例回應**:
```json
{
  "ok": true,
  "result": [{
    "update_id": 123456789,
    "message": {
      "message_id": 1,
      "from": {"id": 987654321, ...},
      "chat": {"id": 987654321, "type": "private", ...},
      "text": "/start"
    }
  }]
}
```

**Chat ID 是**: `987654321`

**方法 2：使用 Bot（替代方案）**

1. 搜尋 **@userinfobot** 或 **@getidsbot**
2. 傳送 `/start`
3. Bot 會回覆你的 User ID（這也是單人 Chat ID）

### 常見問題

- **404 Not Found**: Chat ID 錯誤或格式不正確
- **群組 Chat ID**: 群組的 Chat ID 通常是負數（例如：`-1001234567890`）

---

## 📱 3. LINE Messaging API 設定

### 建立 Channel

1. 前往 [LINE Developers Console](https://developers.line.biz/console/)
2. 登入你的 LINE 帳號
3. 建立新的 Provider（或選擇現有的）
4. 建立新的 **Messaging API Channel**
5. 填寫必要資訊並同意條款

### 取得 Channel Access Token

1. 進入剛建立的 Channel
2. 前往 **"Messaging API"** 頁籤
3. 滾動到 **"Channel access token (long-lived)"**
4. 點擊 **"Issue"** 產生 Token
5. 複製 Token

### 取得 User ID

**重要**：LINE Messaging API 的 User ID **無法手動取得**，必須透過 Webhook 事件。

**方法 1：透過 Webhook（正確方法）**

為了簡化測試，我們將建立一個測試腳本來取得 User ID。**但對於生產環境**，建議使用以下方式：

1. 啟用 Webhook URL （需要公開的 HTTPS 網址）
2. 用戶傳送訊息後，從 Webhook 事件中讀取 `userId`

**方法 2：使用 Push Message（本專案方法）**

如果你希望主動推送訊息，你需要：

1. 先傳送一個 Broadcast 或 Multicast 訊息
2. 或者從 LINE Official Account Manager 中查看追蹤者
3. **注意**: 本專案使用的是 `push` API，需要知道確切的 `userId`

### 推薦方案：改用 Broadcast

如果你不確定 User ID，建議修改程式碼改用 **Broadcast API**（推送給所有好友）:

```python
# 替換 notifier.py 中的 send_line 函式
def send_line(message, token):
    if not token: return
    url = "https://api.line.me/v2/bot/message/broadcast"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    
    payload = {"messages": [{"type": "text", "text": message[:5000]}]}
    
    try: 
        r = requests.post(url, headers=headers, json=payload)
        if r.status_code != 200: print(f"❌ LINE 發送失敗: {r.text}")
        else: print("✅ LINE 發送成功")
    except Exception as e: print(f"❌ LINE 錯誤: {e}")
```

---

## 🔐 4. 設定 GitHub Secrets

1. 前往你的 GitHub Repository
2. 點擊 **Settings** → **Secrets and variables** → **Actions**
3. 點擊 **"New repository secret"**
4. 依序新增以下 Secrets:

| Secret Name | 說明 | 範例格式 |
|-------------|------|----------|
| `GEMINI_API_KEY` | Google Gemini API Key | `AIzaSyABC...XYZ` |
| `TG_TOKEN` | Telegram Bot Token | `123456789:ABCdef...` |
| `TG_CHAT_ID` | Telegram Chat ID | `987654321` |
| `LINE_TOKEN` | LINE Channel Access Token | `eyJhbGciOi...` |
| `LINE_USER_ID` | LINE User ID（或改用 Broadcast）| `Uabcd1234...` |
| `GCP_JSON` | Google Sheets Service Account JSON | 完整 JSON 內容 |

---

## 🧪 5. 本地測試

### 建立 `.env` 檔案

在專案根目錄建立 `.env` 檔案（不要提交到 Git）:

```env
GEMINI_API_KEY=你的_Gemini_API_Key
TG_TOKEN=你的_Telegram_Bot_Token
TG_CHAT_ID=你的_Chat_ID
LINE_TOKEN=你的_LINE_Token
LINE_USER_ID=你的_LINE_User_ID或留空
```

### 執行測試腳本

```powershell
# 設置虛擬環境
.\setup_venv.ps1

# 啟動虛擬環境
.\.venv\Scripts\Activate.ps1

# 執行通知測試
python tests\test_notifications.py
```

---

## 🔧 疑難排解

### Gemini API 失敗

- ✅ 檢查 API Key 是否正確
- ✅ 檢查 Quota 是否用盡
- ✅ 確認專案已啟用 Generative Language API

### Telegram 404 錯誤

- ✅ 重新取得 Chat ID（參考上方步驟）
- ✅ 確認 Chat ID 包含正負號
- ✅ 檢查 Bot Token 是否正確

### LINE 發送失敗

- ✅ 考慮改用 Broadcast API
- ✅ 如使用 Push API，確認 User ID 正確
- ✅ 檢查 Channel Access Token 是否有效

---

## ✅ 驗證檢查清單

- [ ] Gemini API 測試通過
- [ ] Telegram 收到測試訊息
- [ ] LINE 收到測試訊息（或改用 Broadcast）
- [ ] GitHub Secrets 全部設定完成
- [ ] GitHub Actions 手動執行成功
- [ ] 等待排程自動執行並確認收到通知
