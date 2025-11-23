# 在 Render.com 部署 LINE Webhook 伺服器

完整教學：如何在 Render.com 免費部署 Flask Webhook 伺服器來取得 LINE 群組 ID

---

## 🎯 目標

建立一個永久的 HTTPS Webhook URL，用來接收 LINE 事件並取得群組 ID。

**優點**：
- ✅ 永久 HTTPS URL（不需要 ngrok）
- ✅ 完全免費（Render 免費方案）
- ✅ 自動 SSL 憑證
- ✅ 自動重啟和日誌

---

## 📋 前置準備

1. ✅ GitHub 帳號
2. ✅ Render.com 帳號（使用 GitHub 登入即可）
3. ✅ `line_webhook_server.py` 已在專案中

---

## 🚀 步驟 1：準備專案檔案

### 1.1 檢查必要檔案

確認以下檔案存在：

```
AI_Stock_Agent/
├── line_webhook_server.py    ← Webhook 伺服器
├── requirements.txt           ← Python 套件清單
└── (其他檔案...)
```

### 1.2 檢查 requirements.txt

確保包含 `flask`：

```txt
yfinance
pandas
numpy
flask
requests
python-dotenv
...
```

如果沒有 `flask`，請執行：
```powershell
echo flask >> requirements.txt
```

---

## 📤 步驟 2：推送到 GitHub

```powershell
# 確保所有變更已提交
git add .
git commit -m "Add LINE webhook server for Render deployment"
git push origin main
```

---

## 🌐 步驟 3：在 Render.com 建立 Web Service

### 3.1 登入 Render
前往：https://render.com/  
點選「Get Started」並使用 GitHub 登入

### 3.2 建立新的 Web Service

1. 點選「New +」→「Web Service」
2. 連接您的 GitHub Repository：
   - 搜尋：`AI_Stock_Agent`
   - 點選「Connect」

### 3.3 配置 Web Service

填寫以下資訊：

| 欄位 | 值 | 說明 |
|------|-----|------|
| **Name** | `ai-stock-webhook` | 您的服務名稱（小寫、數字、破折號） |
| **Region** | `Oregon (US West)` | 選擇最近的區域（建議美西） |
| **Branch** | `main` | Git 分支 |
| **Root Directory** | (留空) | 因為在根目錄 |
| **Runtime** | `Python 3` | 自動偵測 |
| **Build Command** | `pip install -r requirements.txt` | 自動偵測 |
| **Start Command** | `python line_webhook_server.py` | ⚠️ **重要**：手動輸入 |

### 3.4 選擇方案

- 選擇 **「Free」** 方案（$0/month）
- 點選「Create Web Service」

---

## ⏳ 步驟 4：等待部署完成

### 4.1 觀察部署日誌

Render 會自動：
1. Clone 您的 GitHub repository
2. 執行 `pip install -r requirements.txt`
3. 啟動 `python line_webhook_server.py`

**預期輸出**：
```
==> Installing dependencies...
Successfully installed flask requests...
==> Starting service...
🚀 LINE Webhook Server 啟動中...
 * Running on http://0.0.0.0:5000
```

### 4.2 取得您的 Webhook URL

部署成功後，在頁面頂部會看到：

```
https://ai-stock-webhook.onrender.com
         ↑
     複製這個 URL
```

您的 **Webhook URL** = `https://ai-stock-webhook.onrender.com/webhook`

---

## 🔧 步驟 5：設定 LINE Developers Console

### 5.1 登入 LINE Developers
前往：https://developers.line.biz/console/

### 5.2 選擇您的 Messaging API Channel

1. 點選您的 Provider
2. 選擇 Messaging API Channel

### 5.3 設定 Webhook URL

在「Messaging API」分頁：

1. **Webhook settings** → **Webhook URL**
   ```
   https://ai-stock-webhook.onrender.com/webhook
   ```

2. 點選「Update」

3. 點選「Verify」測試連線
   - ✅ 成功：顯示「Success」
   - ❌ 失敗：檢查 Render 服務是否運行中

### 5.4 啟用 Webhook

- 打開「Use webhook」開關 → **ON**

### 5.5 關閉自動回覆（重要！）

前往 **LINE Official Account Manager**：

1. 點選頁面右上角的設定圖示
2. **回應設定**：
   - ❌ 關閉「自動回應訊息」
   - ❌ 關閉「加入好友的歡迎訊息」
   - ✅ 開啟「Webhook」

---

## 📱 步驟 6：取得群組 ID

### 6.1 將 Bot 加入 LINE 群組

1. 在 LINE 群組中，點選「邀請」
2. 搜尋並加入您的 LINE Official Account

### 6.2 發送測試訊息

在群組中輸入任意訊息，例如：
```
/getgroupid
```

### 6.3 查看 Render 日誌

#### 方法 A：Render 網頁界面
1. 在 Render Dashboard 中，點選您的服務
2. 點選左側「Logs」分頁
3. 即時查看日誌

#### 方法 B：使用 Render CLI（進階）
```powershell
# 安裝 Render CLI
npm install -g render-cli

# 登入
render login

# 查看日誌
render logs ai-stock-webhook
```

**預期日誌輸出**：
```
========================================
📱 收到群組訊息！

群組 ID: Cxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
用戶 ID: Uxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
訊息內容: /getgroupid
========================================

請將以下內容複製到 .env 檔案：
LINE_GROUP_ID=Cxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 6.4 複製群組 ID 到 .env

```env
# 在本地 .env 檔案加入
LINE_GROUP_ID=Cxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 🧪 步驟 7：測試發送到群組

### 7.1 在本地測試

```powershell
# 確保 .env 已設定 LINE_GROUP_ID
python test_line_group.py
```

### 7.2 預期結果

- ✅ 終端機顯示：`✅ LINE 發送成功 (群組推送 (Group ID: Cxxxxxxx...)`
- ✅ LINE 群組收到測試訊息

---

## 🔄 步驟 8：關閉 Webhook 伺服器（完成後）

### 重要提醒

Webhook 伺服器**只用於取得群組 ID**，取得後可以：

#### 選項 A：暫停服務（節省資源）

1. 在 Render Dashboard
2. 點選服務 → Settings
3. 點選「Suspend」

#### 選項 B：刪除服務

1. Settings → Danger Zone
2. 點選「Delete Service」

#### 選項 C：保持運行（推薦）

保持服務運行的好處：
- 可以隨時查看新群組的 ID
- 未來如果 Bot 加入新群組，可以即時取得 ID
- Render 免費方案有 750 小時/月（足夠使用）

---

## ⚠️ Render 免費方案限制

### 注意事項

1. **閒置休眠**
   - 15 分鐘無請求會進入休眠
   - 下次請求需 30-60 秒喚醒
   - 解決方案：使用 UptimeRobot 每 5 分鐘 ping 一次（可選）

2. **月使用時數**
   - 免費方案：750 小時/月
   - 對於 Webhook 伺服器來說非常充足

3. **自動重啟**
   - 服務每次接收請求後自動喚醒
   - 第一次請求可能較慢

---

## 📊 故障排除

### 問題 1：Render 部署失敗

**檢查**：
```powershell
# 確認 requirements.txt 包含 flask
cat requirements.txt | findstr flask
```

**解決**：
```powershell
echo flask >> requirements.txt
git add requirements.txt
git commit -m "Add flask to requirements"
git push origin main
```

Render 會自動重新部署。

---

### 問題 2：LINE Webhook 驗證失敗

**可能原因**：
1. Render 服務尚未完成部署
2. URL 輸入錯誤（少了 `/webhook`）
3. Render 服務進入休眠

**解決**：
1. 等待 Render 完成部署（查看 Logs）
2. 確認 URL: `https://YOUR-APP.onrender.com/webhook`
3. 手動訪問 `https://YOUR-APP.onrender.com/` 喚醒服務

---

### 問題 3：沒有收到 Webhook 事件

**檢查清單**：
- [ ] LINE Developers 中「Use webhook」已啟用
- [ ] 自動回覆訊息已關閉
- [ ] Bot 已加入群組
- [ ] 在群組中發送訊息（不是一對一聊天）
- [ ] Render 服務正在運行（查看 Logs）

---

## 🎓 進階：環境變數設定（可選）

如果您想在 Render 設定 LINE_CHANNEL_SECRET 來驗證簽名：

1. Render Dashboard → 您的服務
2. Environment → Environment Variables
3. 新增變數：
   ```
   Key: LINE_CHANNEL_SECRET
   Value: 您的 Channel Secret（從 LINE Developers 取得）
   ```
4. 點選「Save Changes」（會自動重啟服務）

---

## ✅ 完成檢查清單

完成以下步驟後，您就可以發送訊息到 LINE 群組了：

- [ ] Render 服務已部署並運行
- [ ] LINE Webhook URL 已設定
- [ ] Webhook 驗證成功
- [ ] Bot 已加入 LINE 群組
- [ ] 成功從日誌取得群組 ID
- [ ] LINE_GROUP_ID 已加入 .env
- [ ] test_line_group.py 測試成功

---

## 📞 需要幫助？

- Render 文件：https://render.com/docs
- LINE Developers：https://developers.line.biz/en/docs/

---

**恭喜！** 您現在有一個永久的 Webhook URL，可以隨時接收 LINE 事件！

下一步：執行 `python main.py --dry-run` 測試完整的 AI Stock Agent 功能。
