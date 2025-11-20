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

def calculate_confidence_score(market_regime, quality_data, technical_data, sentiment_score, stock_type="Satellite"):
    """
    計算分數 (0-100) - Core/Satellite 雙公式系統 (Refined for Long-Term Tactical Timing)
    
    改進:
    - RSI百分位取代絕對值 (適應不同波動股票)
    - MA50趨勢確認 (金叉/死叉)
    - 估值懲罰機制 (防止追高)
    - Satellite增加獲利信號
    
    Core: 15% trend + 35% value + 35% quality + 15% cost
    Satellite: 20% trend + 30% quality + 25% value + 20% technical + 5% sentiment
    """
    score = 0
    
    if stock_type == "Core":
        # === Core Formula: Buy Quality on Dips, Hold Forever ===
        
        # A. 趨勢健康度 (15%) - 多重時間框架
        trend_score = 0
        if market_regime['is_bullish']: trend_score += 8  # 長期趨勢
        if market_regime.get('ma50_above_ma200', False): trend_score += 4  # 中期金叉
        if technical_data.get('is_above_ma200', True): trend_score += 3  # 個股趨勢
        score += trend_score
        
        # B. 品質 (35%) - ETF/Stock Quality
        quality_score = 0
        
        if quality_data['is_etf']:
            quality_score += 20  # ETF基礎分
            if quality_data['dual_momentum']: quality_score += 10
            quality_score += 5  # 費用率 placeholder
        else:
            # 非ETF的Core持股
            if quality_data['dual_momentum']: quality_score += 15
            try:
                roe_val = float(quality_data['roe'].strip('%')) if isinstance(quality_data['roe'], str) and quality_data['roe'] != 'N/A' else 0
                if roe_val > 20: quality_score += 15
                elif roe_val > 15: quality_score += 10
            except: pass
            quality_score += 5
        
        score += quality_score
        
        # C. 價格吸引力 (35%) - **核心重點:相對價值**
        value_score = 0
        
        # RSI百分位 (0-1,越低越便宜)
        rsi_percentile = technical_data.get('rsi_percentile', 0.5)
        if rsi_percentile < 0.25: value_score += 20  # 處於過去1年最低25%
        elif rsi_percentile < 0.40: value_score += 12
        elif rsi_percentile < 0.55: value_score += 5
        
        # 布林帶位置
        bb_position = technical_data.get('bb_position', 0.5)
        if bb_position < 0.3: value_score += 10  # 接近下軌
        elif bb_position < 0.5: value_score += 5
        
        # VIX恐慌買入機會
        if market_regime['vix'] > 25: value_score += 5  # 市場恐慌時加碼
        
        score += value_score
        
        # D. 成本效率 (15%)
        cost_score = 10  # 基礎分
        try:
            target = float(quality_data['target'])
            price = float(technical_data.get('price', 0))
            if price > 0 and target > 0:
                if price < target * 0.95: cost_score += 5  # 低於目標價5%以上
        except:
            pass
        score += cost_score
        
    else:  # Satellite
        # === Satellite Formula: Quality Growth at Fair Price ===
        
        # A. 趨勢確認 (20%) - 嚴格多重時間框架
        trend_score = 0
        if market_regime['is_bullish']: trend_score += 10  # 大盤多頭
        if market_regime.get('ma50_above_ma200', False): trend_score += 5  # 金叉
        if quality_data.get('dual_momentum', False): trend_score += 5  # 個股動能
        
        # VIX恐慌懲罰(選股期不買恐慌)
        if market_regime['vix'] > 30: trend_score -= 10
        elif market_regime['vix'] > 25: trend_score -= 5
        
        score += trend_score
        
        # B. 品質 (30%) - 成長潛力
        quality_score = 0
        if quality_data.get('dual_momentum', False): quality_score += 10
        
        # ROE高標準
        try:
            roe_val = float(quality_data['roe'].strip('%')) if isinstance(quality_data['roe'], str) and quality_data['roe'] != 'N/A' else 0
            if roe_val > 25: quality_score += 15  # 超優質
            elif roe_val > 20: quality_score += 10
            elif roe_val > 15: quality_score += 5
        except: pass
        
        # 營收成長 (placeholder,未來可加)
        quality_score += 5
        
        score += quality_score
        
        # C. 估值安全邊際 (25%) - **防止追高的關鍵**
        valuation_score = 0
        try:
            target = float(quality_data['target'])
            price = float(technical_data.get('price', 0))
            if price > 0 and target > 0:
                discount = (target - price) / target
                
                if discount > 0.25: valuation_score += 25  # 深度折價
                elif discount > 0.15: valuation_score += 15
                elif discount > 0.05: valuation_score += 5
                elif discount < -0.10: valuation_score -= 15  # **估值過高懲罰**
                elif discount < 0: valuation_score -= 5
        except:
            valuation_score += 5  # 無目標價給中性分
        
        score += valuation_score
        
        # D. 技術時機 (20%) - **相對便宜而非絕對超賣**
        tech_score = 0
        rsi = technical_data.get('rsi', 50)
        rsi_percentile = technical_data.get('rsi_percentile', 0.5)
        
        # RSI百分位 (相對評估)
        if rsi_percentile < 0.20: tech_score += 12  # 過去1年最低20%
        elif rsi_percentile < 0.35: tech_score += 8
        elif rsi_percentile < 0.50: tech_score += 4
        
        # 超買懲罰 (獲利信號)
        if rsi > 75: tech_score -= 10  # 極度超買
        elif rsi > 70: tech_score -= 5
        
        # 布林帶位置
        if technical_data.get('is_oversold_bb', False): tech_score += 8
        
        score += tech_score
        
        # E. 輿情 (5%) - 降低權重
        sent_mapped = (sentiment_score + 1) * 2.5  # -1~1 -> 0~5
        score += sent_mapped
    
    # 一票否決 (Universal)
    if quality_data.get('fraud_risk'): score = 0
    
    return max(0, min(100, score))

def calculate_position_size(price, atr, confidence_score, stock_type="Satellite", available_pool=0):
    """
    計算建議倉位 - Core/Satellite 差異化策略
    
    Core: DCA 精神，緩慢定期加碼 (15%-20% of available pool)
    Satellite: 信心驅動，彈性調整 (15%-35% of available pool)
    
    Returns: (shares, position_value, stop_loss_price, signal)
    """
    if atr == 0 or available_pool <= 0: 
        return 0, 0, 0, "HOLD"
    
    pools = Config['CAPITAL_ALLOCATION']
    limits = Config['POSITION_LIMITS']
    
    # 計算停損價
    stop_loss_dist = atr * 2
    stop_loss_price = price - stop_loss_dist
    
    # Type-specific logic
    if stock_type == "Core":
        # Core: Conservative DCA approach
        core_pool = pools.get('core_pool', 10200)
        max_position = core_pool * limits.get('core_max_pct', 0.30)
        
        if confidence_score >= 65:
            kelly_pct = 0.20  # 20% of available pool
            signal = "BUY"
        elif confidence_score >= 55:
            kelly_pct = 0.15  # 15% of available pool
            signal = "ACCUMULATE"
        else:
            kelly_pct = 0.0
            signal = "HOLD"
            
        position_value = min(available_pool * kelly_pct, max_position)
    
    else:  # Satellite
        # Satellite: Confidence-driven flexible sizing
        satellite_pool = pools.get('satellite_pool', 6800)
        max_position = satellite_pool * limits.get('satellite_max_pct', 0.25)
        
        if confidence_score >= 70:
            kelly_pct = 0.35  # 35% of available pool - high conviction
            signal = "BUY"
        elif confidence_score >= 65:
            kelly_pct = 0.25  # 25% of available pool
            signal = "ACCUMULATE"
        elif confidence_score >= 50:
            kelly_pct = 0.15  # 15% of available pool - cautious add
            signal = "HOLD"
        else:
            kelly_pct = 0.0
            signal = "REDUCE" if confidence_score < 40 else "HOLD"
        
        position_value = min(available_pool * kelly_pct, max_position)
    
    if position_value < price:  # Can't afford even 1 share
        return 0, 0, stop_loss_price, "HOLD"
    
    shares = int(position_value / price)
    actual_value = shares * price
    
    return shares, actual_value, stop_loss_price, signal

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
        print(f"⚠️ AI 生成最終失敗 {symbol}")
        print(f"   錯誤類型: {type(e).__name__}")
        print(f"   錯誤訊息: {str(e)}")
        if "quota" in str(e).lower():
            print(f"💡 提示: Gemini API quota 可能已用盡，請檢查 Google Cloud Console")
        elif "invalid" in str(e).lower() or "auth" in str(e).lower():
            print(f"💡 提示: API Key 可能無效，請檢查 GEMINI_API_KEY 設定")
        return "AI 分析暫時無法使用 (連線繁忙)"