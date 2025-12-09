# MongoDB MCP Server 使用指南

## ✅ 安裝完成

MongoDB MCP Server 已成功安裝並配置！

## 🚀 啟動方式

使用以下命令啟動 MongoDB MCP Server：

```powershell
.\start_mongodb_mcp.ps1
```

此腳本會：
1. 自動從 `.env` 檔案讀取 `MONGODB_URI`
2. 設置官方推薦的環境變數 `MDB_MCP_CONNECTION_STRING`
3. 啟動最新版本的 MongoDB MCP Server

## 📋 配置資訊

- **連接方式**: MongoDB Atlas
- **環境變數**: `MDB_MCP_CONNECTION_STRING`
- **連接字串來源**: `.env` 檔案中的 `MONGODB_URI`
- **參考官方文檔**: https://github.com/mongodb-js/mongodb-mcp-server

## 🔧 可用工具

MongoDB MCP Server 提供以下工具類別（需在 AI 客戶端中使用）：

### 查詢工具
- `find-documents` - 查詢文檔
- `aggregate` - 聚合查詢
- `count-documents` - 計數文檔

### 寫入工具（需移除 --readOnly）
- `insert-one` - 插入單一文檔
- `insert-many` - 插入多個文檔
- `update-one` - 更新單一文檔
- `delete-many` - 刪除多個文檔

### 管理工具
- `list-databases` - 列出所有資料庫
- `list-collections` - 列出集合
- `create-index` - 創建索引

## 📝 注意事項

1. **安全模式**: 目前以預設模式啟動，可讀寫資料庫
2. **只讀模式**: 如需只讀模式，請在 `start_mongodb_mcp.ps1` 中的 npx 命令後加上 `--readOnly`
3. **日誌位置**: 
   - Windows: `%LOCALAPPDATA%\mongodb\mongodb-mcp\.app-logs`

## 🔍 驗證連接

您可以在支援 MCP 的 AI 客戶端（如 Claude Desktop、Windsurf、VSCode Copilot）中測試 MCP Server 功能。

## 🛠️ 故障排除

如遇到問題：
1. 確認 `.env` 中的 `MONGODB_URI` 格式正確
2. 檢查 MongoDB Atlas 的 IP 白名單設定
3. 確認資料庫用戶權限
4. 查看日誌文件以獲取詳細錯誤信息
