import os
import argparse
import time
from market_data import get_market_regime
from garp_strategy import GARPStrategy
from news_agent import NewsAgent
from google_news_searcher import GoogleNewsSearcher
from prediction_engine import get_predicted_return
from report_formatter import format_stock_report, format_minimal_report
from notifier import send_line, send_telegram
from sheet_manager import get_stock_lists
from market_status import is_market_open, get_economic_events, get_earnings_calendar
from data_models import OverallStatus
from config import Config
from database_manager import DatabaseManager
from logger import logger # [NEW]

def run_analysis(mode="post_market", dry_run=False):
    logger.info(f"🚀 AI Stock Agent V2.1 (Cloud Integrated) 啟動中...")
    logger.info(f"   模式: {mode} | Dry Run: {dry_run}")
    
    # 0. Check Market Status
    market_is_open = is_market_open()
    if not market_is_open:
        logger.info("😴 今日美股休市，執行休市簡報模式。")
    
    # 0.1 Market Regime
    logger.info("📊 市場體質檢測中...")
    market_regime = get_market_regime()
    print(f"   SPY: ${market_regime['spy_price']:.2f} | Bullish: {market_regime['is_bullish']}")
    print(f"   VIX: {market_regime['vix']:.2f}")
    
    # 0.2 Market Outlook (Hybrid Mode)
    print("\n🔮 生成市場展望 (Hybrid Mode)...")
    
    print("   ├─ 1. 獲取真實經濟數據 (Finviz)...")
    economic_events = get_economic_events()
    earnings_calendar = get_earnings_calendar()
    
    hard_facts_parts = []
    if economic_events and "無" not in economic_events:
        hard_facts_parts.append(f"經濟數據:\n{economic_events}")
    if earnings_calendar and "無" not in earnings_calendar:
        hard_facts_parts.append(f"{earnings_calendar}")
    
    events_str = "\n\n".join(hard_facts_parts) if hard_facts_parts else "本週無重大財經事件。"
    
    print("   ├─ 2. 請求 AI 策略解讀...")
    news_agent = NewsAgent()
    searcher = GoogleNewsSearcher()
    
    try:
        ai_analysis = news_agent.get_market_outlook(events_data=events_str)
    except Exception as e:
        print(f"   ⚠️ AI 市場解讀失敗: {e}")
        ai_analysis = "市場解讀暫時無法取得"
    
    # [Start] Collection for Batch Reporting
    all_analyzed_cards = [] 
    
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
            
            # Helper function to process a list of symbols
            def process_list(symbol_list, list_name):
                if not symbol_list: return
                print(f"\n💼【{list_name}】")
                
                for symbol in symbol_list:
                    try:
                        print(f"\n🔍 分析: {symbol}")
                        
                        # A. GARP Analysis
                        card = strategy.analyze(symbol)
                        print(f"   ├─ 評級: {card.overall_status}")
                        
                        news_summary_str = None
                        should_analyze_depth = True
                        
                        # Optimization: Skip API calls for Watchlist rejects
                        if list_name == "Watchlist" and card.overall_status == OverallStatus.REJECT.value:
                            should_analyze_depth = False
                            
                        if should_analyze_depth:
                            # B. Prediction Engine
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
                            
                            # C. Google News & AI Commentary
                            print(f"   ├─ 搜尋新聞 (Google Facts)...")
                            try:
                                news_list = searcher.search_news(symbol, days=3)
                                
                                if news_list:
                                    print(f"      📄 找到 {len(news_list)} 則新聞，AI 分析中...")
                                    analysis_result = news_agent.analyze_news(symbol, news_list)
                                    
                                    if analysis_result:
                                        sentiment_emoji = "😃" if analysis_result['sentiment'] == "Positive" else ("😞" if analysis_result['sentiment'] == "Negative" else "😐")
                                        headlines = searcher.format_news_summary(news_list, max_articles=2)
                                        news_summary_str = f"💡 AI: {sentiment_emoji} {analysis_result['sentiment']}\n💬 {analysis_result['summary_reason']}\n{headlines}"
                                    else:
                                        news_summary_str = searcher.format_news_summary(news_list, max_articles=2)
                                else:
                                    print("      ⚠️ 無近期新聞")
                                    news_summary_str = "📰 近期無新聞"
                            except Exception as ne:
                                print(f"      ⚠️ 新聞模組錯誤: {ne}")
                                news_summary_str = "⚠️ 無法取得新聞"
                        else:
                            print(f"   ├─ 評級為 REJECT，跳過深度分析")
                            news_summary_str = "⛔ 基本面未達標，暫不進行 AI 新聞分析。"
                        
                        # Attach summary to card for format_minimal_report
                        card.news_summary_str = news_summary_str
                        
                        # Add to batch list
                        all_analyzed_cards.append(card)
                        
                        # Database: Save snapshot (Detailed Report)
                        report_detailed = format_stock_report(card, news_summary_str)
                        db.save_daily_snapshot(card, report_detailed)
                        print(f"   └─ ✅ 完成 (DB Saved)")
                        
                        time.sleep(1) # Rate limiting
                        
                    except Exception as e:
                        print(f"   └─ ❌ 錯誤: {e}")
                        import traceback
                        traceback.print_exc()

            # Process Lists
            if MY_HOLDINGS: process_list(MY_HOLDINGS, "Holdings")
            if MY_WATCHLIST: process_list(MY_WATCHLIST, "Watchlist")

    # 3. Generate Final Report (Minimal Version)
    print("\n📝 生成最終簡報 (Minimal Mode)...")
    minimal_report_content = format_minimal_report(market_regime, all_analyzed_cards)
    
    # 4. Send Report
    if dry_run:
        print("\n" + "=" * 60)
        print("📢 [Dry Run] 模擬發送報告內容：")
        print("=" * 60)
        print(minimal_report_content)
        print("=" * 60)
    else:
        print("\n📨 正在發送報告...")
        
        # Telegram
        if Config['TG_TOKEN']:
            print("   ├─ Telegram")
            send_telegram(minimal_report_content, Config['TG_TOKEN'], Config['TG_CHAT_ID'])
            
        # LINE
        if Config['LINE_TOKEN']:
            print("   └─ LINE")
            send_line(minimal_report_content, Config['LINE_TOKEN'], user_id=Config['LINE_USER_ID'], group_id=Config.get('LINE_GROUP_ID'))
    
    print("\n✅ 完成！")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, default='post_market', choices=['pre_market', 'post_market'])
    parser.add_argument('--dry-run', action='store_true', help='Run without sending network requests')
    args = parser.parse_args()
    run_analysis(args.mode, args.dry_run)
