from database_manager import DatabaseManager

def check_raw():
    db = DatabaseManager()
    data = db.get_latest_stock_data("VOO") # Using VOO as it was updated
    if data:
        raw = data.get('raw_data', {})
        sl = raw.get('sparkline')
        print(f"Sparkline in Root: {data.get('sparkline')}")
        print(f"Sparkline in Raw: {sl}")
        print(f"Len: {len(sl) if sl else 0}")
    else:
        print("No data")

if __name__ == "__main__":
    check_raw()
