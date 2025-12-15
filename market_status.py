import yfinance as yf
import pandas_market_calendars as mcal
from datetime import datetime
from finvizfinance.calendar import Calendar
from finvizfinance.earnings import Earnings
from constants import Emojis


def is_market_open() -> tuple[bool, str]:
    """
    Check if NYSE is open.
    Returns: (is_open, reason_if_closed)
    """
    try:
        nyse = mcal.get_calendar('NYSE')
        today = datetime.now()
        today_str = today.strftime('%Y-%m-%d')
        schedule = nyse.schedule(start_date=today_str, end_date=today_str)
        
        if not schedule.empty:
            return True, "Market Open"
            
        # If empty, determine why
        if today.weekday() >= 5: # 5=Sat, 6=Sun
            return False, "週末 (Weekend)"
            
        return False, "國定假日 (Holiday)"
        
    except Exception as e:
        print(f"⚠️ 休市檢查失敗: {e} (預設為開盤)")
        return True, "Check Failed (Default Open)"


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
    
def calculate_macro_status(market_regime: dict) -> str:
    """Based on VIX and Trend, return a macro status string."""
    vix = market_regime.get('vix', 20.0)
    is_bullish = market_regime.get('is_bullish', False)
    
    if is_bullish and vix < 20:
        return f"RISK_ON {Emojis.ROCKET}"
    elif not is_bullish and vix > 25:
        return f"RISK_OFF {Emojis.SHIELD}"
    elif not is_bullish:
        return f"DEFENSIVE {Emojis.SHIELD}"
    else:
        return f"NEUTRAL {Emojis.FAIR}"



def get_implied_erp(vix_price: float = None) -> float:
    """
    Calculate Implied Equity Risk Premium (ERP).
    Phase 15.2: Dynamic Risk Adjustment.
    
    Formula: ERP = Base_ERP + Sensitivity * (VIX - Base_VIX)
    Base_ERP = 4.5% (approx long term avg)
    Base_VIX = 15
    Sensitivity = 0.3% per VIX point (Estimated simplified model)
    """
    if vix_price is None:
        try:
             # Try fetch VIX if not provided
             vix = yf.Ticker("^VIX")
             hist = vix.history(period="1d")
             if not hist.empty:
                 vix_price = hist['Close'].iloc[-1]
             else:
                 vix_price = 20.0 # Safety default
        except:
             vix_price = 20.0
             
    base_erp = 0.045 # 4.5%
    base_vix = 15.0
    sensitivity = 0.003 # 0.3% per point
    
    adjustment = (vix_price - base_vix) * sensitivity
    implied_erp = base_erp + adjustment
    
    # Clamp (Min 3%, Max 10% for realistic WACC inputs)
    return max(0.03, min(0.10, implied_erp))


if __name__ == "__main__":
    print(f"Is Market Open: {is_market_open()}")
    print("Economic Events:\n", get_economic_events())
    print("Earnings Calendar:\n", get_earnings_calendar())
    print("Macro Status:", calculate_macro_status({'vix': 15, 'is_bullish': True}))
