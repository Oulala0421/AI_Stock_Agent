# AI Stock Agent 虛擬環境設置腳本
# 自動建立 Python 虛擬環境並安裝所有依賴

Write-Host "🚀 AI Stock Agent 虛擬環境設置" -ForegroundColor Cyan
Write-Host "=" * 60

# 檢查 Python 是否安裝
Write-Host "`n📌 檢查 Python 安裝..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "❌ 找不到 Python，請先安裝 Python 3.9 或更高版本" -ForegroundColor Red
    Write-Host "   下載: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# 建立虛擬環境
Write-Host "`n📌 建立虛擬環境..." -ForegroundColor Yellow
if (Test-Path ".venv") {
    Write-Host "⚠️ 虛擬環境已存在，跳過建立" -ForegroundColor Yellow
}
else {
    python -m venv .venv
    if ($?) {
        Write-Host "✅ 虛擬環境建立成功" -ForegroundColor Green
    }
    else {
        Write-Host "❌ 虛擬環境建立失敗" -ForegroundColor Red
        exit 1
    }
}

# 啟動虛擬環境
Write-Host "`n📌 啟動虛擬環境..." -ForegroundColor Yellow
& ".\.venv\Scripts\Activate.ps1"

# 升級 pip
Write-Host "`n📌 升級 pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet
Write-Host "✅ pip 已升級" -ForegroundColor Green

# 安裝依賴
Write-Host "`n📌 安裝套件依賴..." -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt --quiet
    if ($?) {
        Write-Host "✅ 所有套件安裝完成" -ForegroundColor Green
    }
    else {
        Write-Host "❌ 套件安裝失敗" -ForegroundColor Red
        exit 1
    }
}
else {
    Write-Host "❌ 找不到 requirements.txt" -ForegroundColor Red
    exit 1
}

# 檢查 .env 檔案
Write-Host "`n📌 檢查環境變數設定..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✅ .env 檔案已存在" -ForegroundColor Green
}
else {
    Write-Host "⚠️ 找不到 .env 檔案" -ForegroundColor Yellow
    Write-Host "   請建立 .env 檔案並設定必要的 API keys" -ForegroundColor Yellow
    Write-Host "   參考: docs/setup_guide.md" -ForegroundColor Yellow
    
    # 建立範例 .env 檔案
    $envExample = @"
# Google Gemini API
GEMINI_API_KEY=你的_Gemini_API_Key

# Telegram 設定
TG_TOKEN=你的_Telegram_Bot_Token
TG_CHAT_ID=你的_Chat_ID

# LINE 設定
LINE_TOKEN=你的_LINE_Channel_Access_Token
LINE_USER_ID=你的_LINE_User_ID或留空改用Broadcast
"@
    
    $envExample | Out-File -FilePath ".env.example" -Encoding UTF8
    Write-Host "   已建立 .env.example 範例檔案" -ForegroundColor Green
}

# 完成
Write-Host "`n" + ("=" * 60)
Write-Host "🎉 虛擬環境設置完成！" -ForegroundColor Green
Write-Host ("=" * 60)

Write-Host "`n📝 下一步:" -ForegroundColor Cyan
Write-Host "1. 確認 .env 檔案中的 API keys 已正確設定"
Write-Host "2. 執行測試: python tests\test_notifications.py"
Write-Host "3. 執行 Dry Run: python main.py --mode post_market --dry-run"

Write-Host "`n💡 提示:" -ForegroundColor Yellow
Write-Host "- 啟動虛擬環境: .\.venv\Scripts\Activate.ps1"
Write-Host "- 停用虛擬環境: deactivate"
Write-Host "- 查看說明文件: docs\setup_guide.md"

Write-Host ""
