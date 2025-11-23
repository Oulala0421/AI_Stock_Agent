# LINE Webhook 設定教學 - 取得群組 ID

## 📚 背景知識

根據 [LINE Messaging API 官方文件](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)：

當用戶在群組中發送訊息時，LINE Platform 會發送 Webhook 事件到您的伺服器，其中包含 `groupId`。

**Webhook 範例**：
```json
{
  "events": [{
    "type": "message",
    "source": {
      "type": "group",
      "groupId": "Ca56f94637c...",  ← 這就是群組 ID！
      "userId": "U4af4980629..."
    },
    "message": {
      "type": "text",
      "text": "Hello"
    }
  }]
}
```

---

## 🎯 目標

建立一個臨時 Webhook 伺服器來接收並顯示您的 LINE 群組 ID，然後用這個 ID 直接發送訊息到特定群組。

---

## 🔧 步驟 1：在 LINE Developers 設定 Webhook URL

### 1.1 登入 LINE Developers Console
前往：https://developers.line.biz/console/

### 1.2 選擇您的 Messaging API Channel

### 1.3 設定 Webhook URL
1. 找到「Messaging API」分頁
2. 啟用「Use webhook」
3. 設定 Webhook URL：
   - **本地測試**（使用 ngrok）：`https://YOUR_NGROK_URL/webhook`
   - **雲端部署**（建議）：使用免費服務如 Render、Railway、Fly.io

### 1.4 重要設定
- ✅ 啟用「Use webhook」
- ✅ 關閉「Auto-reply messages」（在 LINE Official Account Manager）
- ✅ 關閉「Greeting messages」

---

## 🚀 步驟 2：執行本地 Webhook 伺服器

### 方法 A：使用 ngrok (推薦給本地測試)

#### 2.1 安裝 ngrok
```bash
# 下載：https://ngrok.com/download
# Windows: 解壓縮後將 ngrok.exe 放到專案資料夾
```

#### 2.2 啟動 Webhook 伺服器
```powershell
# 終端機 1: 啟動 Flask 伺服器
python line_webhook_server.py
```

#### 2.3 啟動 ngrok
```powershell
# 終端機 2: 暴露本地 5000 port
ngrok http 5000
```

#### 2.4 複製 ngrok URL
```
Forwarding  https://abc123.ngrok.io -> http://localhost:5000
                    ↑
            複製這個 HTTPS URL
```

#### 2.5 設定到 LINE Developers
Webhook URL = `https://abc123.ngrok.io/webhook`

---

## 🔍 步驟 3：取得群組 ID

### 3.1 將 Bot 加入群組
1. 在 LINE 群組中，點選「邀請」
2. 搜尋並加入您的 LINE Official Account

### 3.2 發送測試訊息
在群組中發送任意訊息（例如：`/getgroupid`）

### 3.3 查看終端機輸出
您會看到類似：
```
========================================
📱 收到群組訊息！

群組 ID: Ca56f94637c41b581f6196d7dc4a953f3
用戶 ID: U4af4980629e5e072570bc7c0a5e8c1e2
訊息內容: /getgroupid
========================================

請將以下內容複製到 .env 檔案：
LINE_GROUP_ID=Ca56f94637c41b581f6196d7dc4a953f3
```

### 3.4 複製 Group ID 到 .env
```env
LINE_TOKEN=你的Token
LINE_GROUP_ID=Ca56f94637c41b581f6196d7dc4a953f3
```

---

## 📝 步驟 4：測試發送到群組

```powershell
# 測試發送
python test_line_group.py
```

應該會看到：
```
✅ LINE 發送成功 (群組推送 (Group ID: Ca56f94637...))
```

然後在 LINE 群組中就會收到測試訊息！

---

## 🌐 方法 B：使用雲端服務（不需要 ngrok）

### Render.com (免費方案)

1. 註冊：https://render.com
2. New → Web Service
3. 連接 GitHub Repository
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `python line_webhook_server.py`
6. 複製 Render 提供的 URL：`https://your-app.onrender.com`
7. LINE Webhook URL = `https://your-app.onrender.com/webhook`

---

## ❗ 常見問題

### Q1: Webhook 顯示「未驗證」
**A**: 確認：
1. 伺服器正在運行
2. ngrok 已啟動（本地測試）
3. URL 是 HTTPS（不是 HTTP）
4. 路徑包含 `/webhook`

### Q2: 沒有收到 Webhook 事件
**A**: 檢查：
1. LINE Official Account Manager → 關閉「自動回覆訊息」
2. Bot 已被加入群組
3. 查看 LINE Developers Console → Webhook → 測試連接

### Q3: 取得的是 userId 而不是 groupId
**A**: 這表示您在「一對一聊天」中測試，請在「群組」中發送訊息

---

## 🎓 進階：Webhook 事件類型

當 Bot 加入群組時，會收到 `join` 事件：
```json
{
  "type": "join",
  "source": {
    "type": "group",
    "groupId": "Ca56f94637c..."
  }
}
```

您可以修改 webhook 伺服器，自動在 Bot 加入時記錄 Group ID！

---

## 📦 所需檔案

本教學需要以下檔案（已為您建立）：
1. `line_webhook_server.py` - Webhook 伺服器
2. `test_line_group.py` - 測試腳本
3. `requirements.txt` - 確保包含 `flask`

---

**最後更新**: 2025-11-23  
**參考文件**: [LINE Messaging API - Receiving Messages](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)
