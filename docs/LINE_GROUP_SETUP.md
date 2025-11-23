# LINE 群組發送設定指南

## 問題診斷

如果您只收到 Telegram 通知，沒收到 LINE 通知，可能的原因：
1. `LINE_USER_ID` 留空或設定不正確
2. LINE Bot 設定問題

## 解決方案：改用群組廣播模式

### 方法 1：使用 Broadcast (推薦給單一群組)

**步驟**：
1. 將 LINE Bot 加入您的 LINE 群組
2. 在 `.env` 檔案中：
   ```
   LINE_TOKEN=你的Channel_Access_Token
   LINE_USER_ID=
   ```
   ⚠️ **重點**: `LINE_USER_ID` 請留空（不要刪除這行，只是不填值）

3. 系統會自動使用 Broadcast API 發送到所有加入 Bot 的好友和群組

### 方法 2：使用個人推送（需要正確的 User ID）

如果您想發送到個人：
```
LINE_USER_ID=U1234567890abcdef...
```

**如何取得 LINE User ID**：
1. 加入 Bot 為好友
2. 發送任意訊息給 Bot
3. 查看 LINE Developers Console 的 Webhook 日誌取得 User ID

## Broadcast API 的運作方式

- **Broadcast** 會發送給所有：
  - 已加入 Bot 的好友
  - 已加入 Bot 的群組

- **適用情境**：
  - Bot 只加入一個群組 → 訊息會發送到該群組 ✅
  - Bot 加入多個群組或有多個好友 → 訊息會發送給所有人

## 實際應用範例

### 情境 A：發送到單一群組
```env
LINE_TOKEN=你的Token
LINE_USER_ID=           # 留空使用 broadcast
```
**結果**: Bot 會將通知發送到已加入的群組 ✅

### 情境 B：發送到特定個人
```env
LINE_TOKEN=你的Token
LINE_USER_ID=U1234567890abcdef
```
**結果**: 只發送給該 User ID 的個人

## 測試方法

1. 修改 `.env` 後
2. 執行測試：
   ```powershell
   python main.py --dry-run
   ```
3. 查看輸出：
   - 成功：`✅ LINE 發送成功 (群組廣播 (Broadcast))`
   - 失敗：會顯示詳細錯誤訊息

## 常見錯誤訊息

| 錯誤 | 原因 | 解決方法 |
|------|------|---------|
| `⚠️ LINE_TOKEN 未設定` | TOKEN 為空 | 檢查 .env 中的 LINE_TOKEN |
| `400 - Invalid user` | User ID 錯誤 | 改用 broadcast（USER_ID 留空）|
| `401 - 認證錯誤` | TOKEN 無效 | 重新取得 Channel Access Token |
| `403 - 權限不足` | Bot 未加入群組 | 確認 Bot 已被邀請進群組 |

## GitHub Actions 設定

如果您使用 GitHub Actions 自動執行：

**Repository → Settings → Secrets**：
```
LINE_TOKEN = 你的Token
LINE_USER_ID = (留空，不要設定這個 secret，或設定為空字串)
```

---

**最後更新**: 2025-11-23  
**適用版本**: Phase 4+
