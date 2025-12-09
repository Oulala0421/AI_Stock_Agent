import os
import argparse
import time
from market_data import get_market_regime
from garp_strategy import GARPStrategy
from news_agent import NewsAgent
from google_news_searcher import GoogleNewsSearcher
from prediction_engine import get_predicted_return
from report_formatter import format_stock_report
from notifier import send_line, send_telegram
from sheet_manager import get_stock_lists
from market_status import is_market_open, get_economic_events, get_earnings_calendar
from data_models import OverallStatus
from config import Config
from database_manager import DatabaseManager

def run_analysis(mode="post_market", dry_run=False):
    print(f"🚀 AI Stock Agent V2.1 (Cloud Integrated) 啟動中...")
    print(f"   模式: {mode} | Dry Run: {dry_run}")
    
    # 0. Check Market Status
    market_is_open = is_market_open()
    if not market_is_open:
        print("😴 今日美股休市，執行休市簡報模式。")
    
    # 0.1 Market Regime
    print("\n📊 市場體質檢測中...")
    market_regime = get_market_regime()
    print(f"   SPY: ${market_regime['spy_price']:.2f} | Bullish: {market_regime['is_bullish']}")
    print(f"   VIX: {market_regime['vix']:.2f}")
    
    # 0.2 Market Outlook (Fact-Opinion Decoupled Logic)
    print("\n🔮 生成市場展望 (Hybrid Mode)...")
    
    # Step A: Get Hard Facts (Code)
    print("   ├─ 1. 獲取真實經濟數據 (Finviz)...")
    economic_events = get_economic_events()
    earnings_calendar = get_earnings_calendar()
    
    # Combine hard facts
    hard_facts_parts = []
    if economic_events and "無" not in economic_events:
        hard_facts_parts.append(f"經濟數據:\n{economic_events}")
    if earnings_calendar and "無" not in earnings_calendar:
        hard_facts_parts.append(f"{earnings_calendar}")
    
    events_str = "\n\n".join(hard_facts_parts) if hard_facts_parts else "本週無重大財經事件。"
    
    # Step B: Get AI Opinion (LLM)
    print("   ├─ 2. 請求 AI 策略解讀...")
    news_agent = NewsAgent()
    searcher = GoogleNewsSearcher()  # Initialize factual news searcher
    
    try:
        ai_analysis = news_agent.get_market_outlook(events_data=events_str)
    except Exception as e:
        print(f"   ⚠️ AI 市場解讀失敗: {e}")
        ai_analysis = "市場解讀暫時無法取得"
    
    # Combine for Report
    market_outlook_section = f"""📅 **本週重要財經事件 (Hard Facts)**:
{events_str}

🧠 **AI 策略解讀 (Opinion)**:
{ai_analysis}""".strip()
    
    # 1. Prepare Report Header
    title_suffix = "盤前分析" if mode == "pre_market" else "盤後日報"
    if not market_is_open: title_suffix += " (休市)"
    
    report_content = f"⚠️ 程式還在修改中，看看就好 ⚠️\n🤖 【AI 投資{title_suffix} - GARP V2.1】 🤖\n"
    if not market_is_open:
        report_content += "😴 美股今日休市，提供市場前瞻。\n"
        
    report_content += f"📊 市場: VIX {market_regime['vix']:.2f} | SPY {'🔥多頭' if market_regime['is_bullish'] else '❄️空頭'}\n"
    report_content += f"{market_outlook_section}\n"
    report_content += "=" * 40 + "\n"
    
    # 2. Analyze Stocks (Only if market is open)
    if market_is_open:
        print("\n📥 連接 Google Sheets...")
        MY_HOLDINGS, MY_WATCHLIST, MY_COSTS, STOCK_TYPES = get_stock_lists()
        
        if not MY_HOLDINGS and not MY_WATCHLIST:
            print("⚠️ 警告：清單為空或連線失敗")
        else:
            print(f"✅ 載入完成: 持股 {len(MY_HOLDINGS)} 檔 | 觀察 {len(MY_WATCHLIST)} 檔")
            strategy = GARPStrategy()
            
            # Initialize Database (Singleton)
            db = DatabaseManager()
            if db.enabled:
                print("✅ [Main] MongoDB functionality enabled.")
            else:
                print("⚠️  [Main] Running without database storage.")
            
            # Analyze Holdings
            if MY_HOLDINGS:
                report_content += "\n💼 【我的持股監控】\n"
                for symbol in MY_HOLDINGS:
                    try:
                        print(f"\n🔍 分析持股: {symbol}")
                        
                        # A. GARP Analysis
                        card = strategy.analyze(symbol)
                        print(f"   ├─ 評級: {card.overall_status}")
                        
                        news_summary_str = None
                        
                        # Only spend API credits on stocks that are NOT REJECT scenarios
                        # OR if it's already in our holdings (we care about our money)
                        should_analyze_depth = True 
                        
                        if should_analyze_depth:
                            # B. Prediction Engine (New!)
                            # Check if card passed basic filters or if checking for specific reasons
                            # For holding, we always check prediction if possible
                            print(f"   ├─ 執行價格預測 (Monte Carlo)...")
                            try:
                                prediction = get_predicted_return(symbol)
                                if prediction:
                                    card.predicted_return_1w = prediction.get('predicted_return_1w')
                                    card.predicted_return_1m = prediction.get('predicted_return_1m')
                                    card.confidence_score = prediction.get('confidence_score')
                                    card.monte_carlo_min = prediction.get('monte_carlo_min')
                                    card.monte_carlo_max = prediction.get('monte_carlo_max')
                                    print(f"      🎯 預測: {card.predicted_return_1w:+.1f}% (信心: {card.confidence_score:.0%})")
                            except Exception as pe:
                                print(f"      ⚠️ 預測引擎錯誤: {pe}")
                            
                            # C. Google News & AI Commentary (New!)
                            print(f"   ├─ 搜尋新聞 (Google Facts)...")
                            try:
                                news_list = searcher.search_news(symbol, days=3)
                                
                                if news_list:
                                    print(f"      📄 找到 {len(news_list)} 則新聞，AI 分析中...")
                                    analysis_result = news_agent.analyze_news(symbol, news_list)
                                    
                                    if analysis_result:
                                        # Construct readable summary for the report
                                        sentiment_emoji = "😃" if analysis_result['sentiment'] == "Positive" else ("😞" if analysis_result['sentiment'] == "Negative" else "😐")
                                        
                                        # Format headlines
                                        headlines = searcher.format_news_summary(news_list, max_articles=2)
                                        
                                        news_summary_str = f"""💡 AI 觀點: {sentiment_emoji} {analysis_result['sentiment']} / {analysis_result['prediction']}
💬 分析: {analysis_result['summary_reason']}
{headlines}"""
                                    else:
                                        news_summary_str = searcher.format_news_summary(news_list, max_articles=3)
                                else:
                                    print("      ⚠️ 無近期新聞")
                                    news_summary_str = "📰 近 3 日無重大新聞"
                            except Exception as ne:
                                print(f"      ⚠️ 新聞模組錯誤: {ne}")
                                news_summary_str = "⚠️ 無法取得新聞"
                        
                        # Format report
                        report = format_stock_report(card, news_summary_str)
                        
                        # Database: Save snapshot
                        db.save_daily_snapshot(card, report)
                        status_change = db.get_status_change(symbol, card.overall_status)
                        
                        # Add status change indicator
                        status_indicator = ""
                        if status_change == "UPGRADE":
                            status_indicator = " [🚀 評級調升!]"
                        elif status_change == "DOWNGRADE":
                            status_indicator = " [⚠️ 評級調降]"
                        elif status_change == "NEW":
                            status_indicator = " [🆕 新增追蹤]"
                        
                        # Add cost info
                        my_cost = MY_COSTS.get(symbol, 0)
                        if my_cost > 0: 
                            # ROI Calculation
                            roi = ((card.price - my_cost) / my_cost) * 100
                            roi_emoji = "🔥" if roi > 0 else "💸"
                            report += f"\n💰 成本: ${my_cost} | 損益: {roi_emoji} {roi:+.2f}%"
                        
                        report_content += f"{report}{status_indicator}\n" + "-" * 40 + "\n"
                        print(f"   └─ ✅ 完成")
                        time.sleep(1) # Be nice to APIs
                        
                    except Exception as e:
                        print(f"   └─ ❌ 錯誤: {e}")
                        import traceback
                        traceback.print_exc()
                        report_content += f"⚠️ {symbol}: 分析失敗 ({e})\n" + "-" * 40 + "\n"
            
            # Analyze Watchlist (Similar logic)
            if MY_WATCHLIST:
                report_content += "\n👀 【重點關注】\n"
                for symbol in MY_WATCHLIST:
                    if symbol in MY_HOLDINGS: continue
                    try:
                        print(f"\n🔍 分析觀察股: {symbol}")
                        
                        # A. GARP Analysis
                        card = strategy.analyze(symbol)
                        print(f"   ├─ 評級: {card.overall_status}")
                        
                        news_summary_str = None
                        
                        # Logic: Analyze depth only if it's NOT a straight REJECT
                        # This saves API costs and time
                        if card.overall_status != OverallStatus.REJECT.value:
                            
                            # B. Prediction Engine
                            print(f"   ├─ 執行價格預測...")
                            try:
                                prediction = get_predicted_return(symbol)
                                if prediction:
                                    card.predicted_return_1w = prediction.get('predicted_return_1w')
                                    card.confidence_score = prediction.get('confidence_score')
                            except Exception as pe:
                                print(f"      ⚠️ 預測引擎錯誤: {pe}")
                            
                            # C. Google News
                            print(f"   ├─ 搜尋新聞...")
                            try:
                                news_list = searcher.search_news(symbol, days=3)
                                
                                if news_list:
                                    # For watchlist, max 2 articles, simpler analysis
                                    analysis_result = news_agent.analyze_news(symbol, news_list)
                                    if analysis_result:
                                        sentiment_emoji = "😃" if analysis_result['sentiment'] == "Positive" else ("😞" if analysis_result['sentiment'] == "Negative" else "😐")
                                        headlines = searcher.format_news_summary(news_list, max_articles=2)
                                        news_summary_str = f"💡 AI: {sentiment_emoji} {analysis_result['sentiment']}\n💬 {analysis_result['summary_reason']}\n{headlines}"
                                    else:
                                        news_summary_str = searcher.format_news_summary(news_list, max_articles=2)
                                else:
                                    news_summary_str = "📰 近期無新聞"
                            except Exception as ne:
                                print(f"      ⚠️ 新聞模組錯誤: {ne}")
                        else:
                            print(f"   ├─ 評級為 REJECT，跳過深度分析")
                            news_summary_str = "⛔ 基本面未達標，暫不進行 AI 新聞分析。"
                        
                        # Format report
                        report = format_stock_report(card, news_summary_str)
                        
                        # Database
                        db.save_daily_snapshot(card, report)
                        status_change = db.get_status_change(symbol, card.overall_status)
                        
                        status_indicator = ""
                        if status_change == "UPGRADE": status_indicator = " [🚀 評級調升!]"
                        elif status_change == "DOWNGRADE": status_indicator = " [⚠️ 評級調降]"
                        
                        report_content += f"{report}{status_indicator}\n" + "-" * 40 + "\n"
                        print(f"   └─ ✅ 完成")
                        time.sleep(1)
                        
                    except Exception as e:
                        print(f"   └─ ❌ 錯誤: {e}")
                        report_content += f"⚠️ {symbol}: 分析失敗\n" + "-" * 40 + "\n"
    else:
        report_content += "\n🏖️ 休市期間不進行個股分析。\n"
    
    # 3. Send Report
    if dry_run:
        print("\n" + "=" * 60)
        print("📢 [Dry Run] 模擬發送報告內容：")
        print("=" * 60)
        print(report_content)
        print("=" * 60)
    else:
        print("\n📨 正在發送報告...")
        if Config['TG_TOKEN']:
            print("   ├─ Telegram")
            send_telegram(report_content, Config['TG_TOKEN'], Config['TG_CHAT_ID'])
        if Config['LINE_TOKEN']:
            print("   └─ LINE")
            send_line(report_content, Config['LINE_TOKEN'], user_id=Config['LINE_USER_ID'], group_id=Config.get('LINE_GROUP_ID'))
    
    print("\n✅ 完成！")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, default='post_market', choices=['pre_market', 'post_market'])
    parser.add_argument('--dry-run', action='store_true', help='Run without sending network requests')
    args = parser.parse_args()
    run_analysis(args.mode, args.dry_run)
