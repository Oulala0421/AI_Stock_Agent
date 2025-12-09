# MongoDB MCP Server 啟動腳本
# 參考: https://github.com/mongodb-js/mongodb-mcp-server

# 載入 .env 文件中的 MONGODB_URI
$envFile = Join-Path $PSScriptRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*MONGODB_URI\s*=\s*(.+)$') {
            $mongoUri = $matches[1].Trim('"')
            Write-Host "✓ 已從 .env 讀取 MongoDB URI" -ForegroundColor Green
        }
    }
}

if (-not $mongoUri) {
    Write-Host "✗ 錯誤: 無法從 .env 讀取 MONGODB_URI" -ForegroundColor Red
    exit 1
}

# 設置 MongoDB MCP Server 的環境變數（官方推薦方式）
$env:MDB_MCP_CONNECTION_STRING = $mongoUri

Write-Host "`n正在啟動 MongoDB MCP Server..." -ForegroundColor Cyan
Write-Host "配置:" -ForegroundColor Yellow
Write-Host "  - 連接模式: MongoDB Atlas" -ForegroundColor Gray
Write-Host "  - 使用環境變數: MDB_MCP_CONNECTION_STRING" -ForegroundColor Gray
Write-Host ""

# 啟動 MongoDB MCP Server（使用官方最新版本）
npx -y mongodb-mcp-server@latest
