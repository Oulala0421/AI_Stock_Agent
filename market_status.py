import pandas_market_calendars as mcal
from datetime import datetime, timedelta
from finvizfinance.calendar import Calendar

def is_market_open():
    """
    檢查美股 (NYSE) 今天是否開盤
    """
    try:
        nyse = mcal.get_calendar('NYSE')
        today = datetime.now().strftime('%Y-%m-%d')
        schedule = nyse.schedule(start_date=today, end_date=today)
        return not schedule.empty
    except Exception as e:
        print(f"⚠️ 休市檢查失敗: {e} (預設為開盤)")
        return True

def get_economic_events():
    """
    獲取本週重要經濟數據 (CPI, FOMC, Nonfarm, PPI)
    """
    try:
        cal = Calendar()
        df = cal.calendar()
        
        if df.empty:
            return "本週無重大經濟數據發布 (或無法取得數據)。"
            
        if 'Impact' not in df.columns:
            return "無法解析經濟日曆格式。"
        
        # 篩選高重要性事件 (Impact = High) 且是本週的
        important_events = df[df['Impact'] == 'High']
        
        if important_events.empty:
            return "本週無重大經濟數據發布。"
            
        events_str = ""
        for _, row in important_events.iterrows():
            time_str = row['Time']
            event_name = row['Event']
            date_str = row['Date']
            # 簡單格式化
            events_str += f"• {date_str} {time_str}: {event_name}\n"
            
        return events_str.strip()
    except Exception as e:
        print(f"⚠️ 無法獲取經濟日曆: {e}")
        return "經濟日曆暫時無法讀取"

if __name__ == "__main__":
    print(f"Is Market Open: {is_market_open()}")
    print("Economic Events:\n", get_economic_events())
