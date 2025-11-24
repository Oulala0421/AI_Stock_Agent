import pandas_market_calendars as mcal
from datetime import datetime
from finvizfinance.calendar import Calendar
from finvizfinance.earnings import Earnings


def is_market_open() -> bool:
    """檢查美股 (NYSE) 今天是否開盤"""
    try:
        nyse = mcal.get_calendar('NYSE')
        today = datetime.now().strftime('%Y-%m-%d')
        schedule = nyse.schedule(start_date=today, end_date=today)
        return not schedule.empty
    except Exception as e:
        print(f"⚠️ 休市檢查失敗: {e} (預設為開盤)")
        return True


def get_economic_events() -> str:
    """獲取本週重要經濟數據 (CPI, FOMC, Nonfarm, PPI)"""
    try:
        cal = Calendar()
        df = cal.calendar()
        if df.empty:
            return "本週無重大經濟數據發布 (或無法取得資料)。"
        if 'Impact' not in df.columns:
            return "無法解析經濟日曆格式。"
        important_events = df[df['Impact'] == 'High']
        if important_events.empty:
            return "本週無重大經濟數據發布。"
        events_str = ""
        for _, row in important_events.iterrows():
            time_str = row.get('Time', '')
            event_name = row.get('Event', '')
            date_str = row.get('Date', '')
            events_str += f"• {date_str} {time_str}: {event_name}\n"
        return events_str.strip()
    except Exception as e:
        print(f"⚠️ 無法獲取經濟日曆: {e}")
        return "經濟日曆暫時無法讀取"


def get_earnings_calendar() -> str:
    """獲取未來 7 天（Next Week）S&P 500 成分股的財報資訊。
    使用 finvizfinance.earnings.Earnings 並設定 period='Next Week'。
    回傳格式示例："[11/20] NVDA (NVIDIA)；[11/21] AAPL (Apple)"。
    """
    try:
        earnings = Earnings(period='Next Week')
        # partition_days 返回 dict，key=日期，value=DataFrame
        earnings_dict = earnings.partition_days(mode='overview')
        if not earnings_dict or len(earnings_dict) == 0:
            return "未來 7 天無 S&P 500 成分股財報。"
        
        lines = []
        for date_key, df in earnings_dict.items():
            # date_key 格式如 'Dec 01/a'，提取月份和日期
            try:
                date_parts = date_key.split('/')
                date_str_raw = date_parts[0].strip()  # 'Dec 01'
                dt = datetime.strptime(date_str_raw, "%b %d")
                dt = dt.replace(year=datetime.now().year)
                date_str = dt.strftime("%m/%d")
            except Exception:
                date_str = date_key
            
            # 遍歷該日期的所有公司
            if df is not None and not df.empty:
                for _, row in df.iterrows():
                    ticker = row.get('Ticker') or row.get('Symbol') or ''
                    company = row.get('Company') or ''
                    line = f"[{date_str}] {ticker} ({company})" if company else f"[{date_str}] {ticker}"
                    lines.append(line)
        
        if not lines:
            return "未來 7 天無 S&P 500 成分股財報。"
        return "未來 7 天財報: " + "；".join(lines[:10])  # 限制最多10個以免過長
    except Exception as e:
        print(f"⚠️ 獲取財報日曆失敗: {e}")
        return "財報日曆暫時無法讀取"

if __name__ == "__main__":
    print(f"Is Market Open: {is_market_open()}")
    print("Economic Events:\n", get_economic_events())
    print("Earnings Calendar:\n", get_earnings_calendar())
