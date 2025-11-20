import os
import time
from google import genai
from finvizfinance.quote import finvizfinance
from finvizfinance.screener.overview import Overview
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from tenacity import retry, stop_after_attempt, wait_exponential
from config import Config

GEMINI_API_KEY = Config['GEMINI_API_KEY']
TOTAL_CAPITAL = Config['TOTAL_CAPITAL']
MAX_RISK_PCT = Config['MAX_RISK_PCT']

def get_market_news(symbol):
    try:
        stock = finvizfinance(symbol)
        news_df = stock.ticker_news()
        headlines = news_df[['Date', 'Title']].head(5)
        
        analyzer = SentimentIntensityAnalyzer()
        total_score = 0
        text = ""
        for _, row in headlines.iterrows():
            clean_title = row['Title'].replace("&#39;", "'").replace("&quot;", '"')
            text += f"• {clean_title}\n"
            total_score += analyzer.polarity_scores(row['Title'])['compound']
            
        avg_score = total_score / len(headlines) if not headlines.empty else 0
        return text, avg_score
    except:
        return "無新聞數據", 0

def get_fundamentals(symbol, is_etf=False):
    if is_etf: 
        return {"target": "N/A", "recom": "N/A", "roe": "N/A", "pe": "N/A"}
        
    try:
        stock = finvizfinance(symbol)
        fund = stock.ticker_fundament()
        return {
            "target": fund.get('Target Price', 'N/A'),
            "recom": fund.get('Recom', 'N/A'),
            "roe": fund.get('ROE', 'N/A'),
            "pe": fund.get('P/E', 'N/A')
        }
    except:
        return {"target": "N/A", "recom": "N/A", "roe": "N/A", "pe": "N/A"}

def scan_market_opportunities():
    try:
        print("🔍 掃描市場超跌機會...")
        foverview = Overview()
        filters_dict = {
            'Index': 'S&P 500', 
            'RSI (14)': 'Oversold (30)',
            'Average Volume': 'Over 500K'
        }
        foverview.set_filter(signal='', filters_dict=filters_dict)
        df = foverview.screener_view()
        if not df.empty:
            return df.head(3)['Ticker'].tolist()
        return []
    except:
        return []

def calculate_confidence_score(market_regime, quality_data, technical_data, sentiment_score):
    """
    計算戰鬥力總分 (0-100)
    Formula: (Market * 0.3) + (Quality * 0.3) + (Technical * 0.2) + (Sentiment * 0.2)
    """
    score = 0
    
    # A. 市場濾網 (30%)
    market_score = 0
    if market_regime['is_bullish']: market_score += 15
    if market_regime['vix'] < 20: market_score += 15
    elif market_regime['vix'] > 30: market_score -= 10
    score += market_score
    
    # B. 個股體質 (30%)
    quality_score = 0
    if quality_data['dual_momentum']: quality_score += 10
    
    # ROE > 15% 或 ETF
    try:
        roe_val = float(quality_data['roe'].strip('%')) if isinstance(quality_data['roe'], str) and quality_data['roe'] != 'N/A' else 0
        if roe_val > 15 or quality_data['is_etf']: quality_score += 10
    except: pass
    
    # 安全邊際
    try:
        target = float(quality_data['target'])
        price = float(technical_data['price']) if 'price' in technical_data else 0
        if price > 0 and price < target * 0.9: quality_score += 10
    except: pass 
    
    score += quality_score

    # C. 技術時機 (20%)
    tech_score = 0
    rsi = technical_data['rsi']
    if rsi < 35 or technical_data.get('is_oversold_bb', False): tech_score += 20
    if rsi > 70: tech_score -= 10
    score += tech_score
    
    # D. AI 輿情 (20%)
    # sentiment_score is -1 to 1. Map to 0 to 20.
    # (-1 -> 0, 0 -> 10, 1 -> 20)
    sent_mapped = (sentiment_score + 1) * 10
    score += sent_mapped

    # 一票否決 (這裡簡單示範，若有 fraud_risk 則歸零)
    if quality_data.get('fraud_risk'): score = 0
    
    return max(0, min(100, score))

def calculate_position_size(price, atr, confidence_score):
    if atr == 0: return 0, 0, 0
    
    # 凱利公式權重
    kelly_pct = 0
    if confidence_score >= 80: kelly_pct = 1.0      # 🟢 強力買進
    elif confidence_score >= 60: kelly_pct = 0.5    # 🟡 分批佈局
    elif confidence_score >= 40: kelly_pct = 0.0    # ⚪ 觀望/持有
    else: kelly_pct = 0.0                           # 🔴 減碼/避險

    stop_loss_dist = atr * 2
    stop_loss_price = price - stop_loss_dist
    
    # 基礎風險金額
    base_risk_amount = TOTAL_CAPITAL * MAX_RISK_PCT
    
    # 根據信心分數調整風險
    adjusted_risk_amount = base_risk_amount * kelly_pct
    
    if stop_loss_dist == 0: return 0, 0, 0
    
    shares = int(adjusted_risk_amount / stop_loss_dist)
    position_value = shares * price
    
    # 單筆上限 30%
    if position_value > TOTAL_CAPITAL * 0.3:
        shares = int((TOTAL_CAPITAL * 0.3) / price)
        position_value = shares * price
        
    return shares, position_value, stop_loss_price

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def _call_gemini_api(client, prompt):
    response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
    return response.text

def generate_ai_briefing(symbol, market_data, news_text, sentiment_score, fundamentals, role, mode="post_market"):
    if not GEMINI_API_KEY: return "⚠️ 未設定 Gemini API Key"
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        time_context = "美股盤前" if mode == "pre_market" else "美股盤後"
        trend_emoji = "🔥" if market_data['trend']['dual_momentum']['is_bullish'] else "❄️"
        
        prompt = f"""
        Role: 量化金融系統架構師 (Quant Architect)
        Task: 為 {symbol} 撰寫 {time_context} 投資快報。
        
        【嚴格規範】
        1. ❌ 嚴禁使用 Markdown 粗體 (**)，LINE 會顯示亂碼。
        2. ✅ 必須使用 Emoji (📈, 🛡️, 💡) 區隔段落。
        3. ✅ 字數限制：180 字以內。
        4. ✅ 敘事結構：【前因 (Cause)】 -> 【後果 (Effect)】。

        【輸入數據】
        • 現價: ${market_data['price']:.2f}
        • RSI: {market_data['momentum']['rsi']:.1f}
        • 趨勢: {trend_emoji} 雙重動能
        • 新聞: {news_text}
        
        【輸出範例】
        📈 市場解讀：
        受到...影響(前因)，導致股價...。
        
        🛡️ 風險提示：
        若跌破...，可能引發...。
        
        💡 操作建議：
        基於雙重動能策略，建議...。
        """
        
        text = _call_gemini_api(client, prompt)
        return text.replace("*", "")
    except Exception as e:
        print(f"⚠️ AI 生成最終失敗 {symbol}: {e}")
        return "AI 分析暫時無法使用 (連線繁忙)"