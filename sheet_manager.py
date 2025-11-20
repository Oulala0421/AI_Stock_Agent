import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

load_dotenv()

SCOPE = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]

def get_google_sheet_client():
    creds = None
    # 1. 優先檢查本地檔案
    if os.path.exists("service_account.json"):
        creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", SCOPE)
    # 2. 檢查環境變數 (GitHub Actions 用)
    elif os.getenv("GCP_JSON"):
        key_dict = json.loads(os.getenv("GCP_JSON"))
        creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, SCOPE)
        
    if not creds:
        return None

    try:
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        print(f"❌ Google 連線失敗: {e}")
        return None

def get_stock_lists():
    client = get_google_sheet_client()
    if not client:
        print("❌ 無法建立 Google 客戶端，請檢查 service_account.json")
        return [], [], {} # 回傳三個空值，防止 main.py 崩潰

    try:
        sheet = client.open("My_Stock_Database")
        
        # 讀取 Holdings
        ws_holdings = sheet.worksheet("Holdings")
        holdings_data = ws_holdings.get_all_records()
        my_holdings = []
        holdings_cost = {}
        for row in holdings_data:
            symbol = row.get('Symbol')
            if symbol:
                symbol = symbol.upper().strip()
                my_holdings.append(symbol)
                holdings_cost[symbol] = row.get('Cost', 0)

        # 讀取 Watchlist
        ws_watchlist = sheet.worksheet("Watchlist")
        watchlist_data = ws_watchlist.get_all_records()
        my_watchlist = []
        for row in watchlist_data:
            symbol = row.get('Symbol')
            if symbol:
                my_watchlist.append(symbol.upper().strip())

        print(f"✅ Google Sheets 讀取成功: 持股{len(my_holdings)}檔 / 關注{len(my_watchlist)}檔")
        return my_holdings, my_watchlist, holdings_cost

    except Exception as e:
        print(f"❌ 讀取試算表失敗: {e}")
        return [], [], {}