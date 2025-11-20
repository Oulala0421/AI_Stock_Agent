import os
import json
import gspread
from datetime import datetime
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
        return [], [], {}, {}

    try:
        sheet = client.open("My_Stock_Database")
        
        # 讀取 Holdings
        ws_holdings = sheet.worksheet("Holdings")
        holdings_data = ws_holdings.get_all_records()
        my_holdings = []
        holdings_cost = {}
        holdings_type = {}  # NEW: Track Core vs Satellite
        
        for row in holdings_data:
            symbol = row.get('Symbol')
            if symbol:
                symbol = symbol.upper().strip()
                my_holdings.append(symbol)
                holdings_cost[symbol] = row.get('Cost', 0)
                holdings_type[symbol] = row.get('Type', 'Satellite').capitalize()  # Default to Satellite

        # 讀取 Watchlist
        ws_watchlist = sheet.worksheet("Watchlist")
        watchlist_data = ws_watchlist.get_all_records()
        my_watchlist = []
        watchlist_type = {}
        
        for row in watchlist_data:
            symbol = row.get('Symbol')
            if symbol:
                symbol = symbol.upper().strip()
                my_watchlist.append(symbol)
                watchlist_type[symbol] = row.get('Type', 'Satellite').capitalize()

        # Merge Type dictionaries
        all_types = {**holdings_type, **watchlist_type}

        print(f"✅ Google Sheets 讀取成功: 持股{len(my_holdings)}檔 / 關注{len(my_watchlist)}檔")
        return my_holdings, my_watchlist, holdings_cost, all_types

    except Exception as e:
        print(f"❌ 讀取試算表失敗: {e}")
        return [], [], {}, {}

def log_history(data_list):
    """
    將每日分析結果寫入 History 分頁
    data_list: list of dict [{'date':..., 'symbol':..., 'price':..., 'score':..., 'signal':...}]
    """
    client = get_google_sheet_client()
    if not client: return

    try:
        sheet = client.open("My_Stock_Database")
        try:
            ws = sheet.worksheet("History")
        except:
            # 如果沒有 History 分頁，嘗試建立 (如果權限允許)
            print("⚠️ History 分頁不存在，嘗試建立...")
            ws = sheet.add_worksheet(title="History", rows=1000, cols=10)
            ws.append_row(["Date", "Symbol", "Price", "Score", "Signal", "Note"])
        
        # 準備寫入的資料
        rows_to_append = []
        for item in data_list:
            rows_to_append.append([
                item['date'],
                item['symbol'],
                item['price'],
                item['score'],
                item['signal'],
                item.get('note', '')
            ])
            
        if rows_to_append:
            ws.append_rows(rows_to_append)
            print(f"✅ 已寫入 {len(rows_to_append)} 筆歷史紀錄")
            
    except Exception as e:
        print(f"⚠️ 寫入歷史紀錄失敗: {e}")