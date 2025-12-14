import os
import argparse
import time
from market_data import get_market_regime
from garp_strategy import GARPStrategy
from news_agent import NewsAgent
from google_news_searcher import GoogleNewsSearcher
from report_formatter import format_stock_report, format_minimal_report, format_private_portfolio_report # [NEW]
from notifier import send_line, send_telegram, send_private_line # [NEW]
from sheet_manager import get_stock_lists
from market_status import is_market_open, get_economic_events, get_earnings_calendar, calculate_macro_status
from data_models import OverallStatus
from config import Config
from database_manager import DatabaseManager
from portfolio_manager import PortfolioManager # [NEW]
from logger import logger # [NEW]
from analysis_engine import AnalysisEngine # [NEW]

def run_analysis(mode="post_market", dry_run=False):
    logger.info(f"🚀 AI Stock Agent V2.1 (Cloud Integrated) 啟動中...")
    logger.info(f"   模式: {mode} | Dry Run: {dry_run}")
    
    # 0. Check Market Status
    # Returns (is_open, reason)
    market_status_tuple = is_market_open()
    market_is_open, close_reason = market_status_tuple
    
    # [Verification] Force open for dry-run
    if dry_run: 
        logger.info("🔧 Dry Run Mode: Forcing market status to OPEN")
        market_is_open = True
        close_reason = "Dry Run Force Open"
        market_status_tuple = (True, "Dry Run Force Open")
        
    if not market_is_open:
        logger.info(f"😴 今日美股休市 ({close_reason})")
        
        # User Request: "If closed, only send morning message once"
        # If this is post_market (evening) and market is closed, SKIP entirely.
        if mode == "post_market":
            logger.info("🛑 Post-Market & Closed -> Skipping Report (Only sending Morning/Pre-Market notification).")
            return
            
        logger.info("   執行休市簡報模式 (Morning/Pre-Market)...")
    
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
    
    # Feature Flags
    enable_searcher = bool(Config.get('SERPAPI_API_KEY'))
    enable_ai = bool(Config.get('GEMINI_API_KEY'))
    
    if not enable_searcher:
        logger.warning("⚠️ SERPAPI_KEY missing. Search features disabled.")
    if not enable_ai:
        logger.warning("⚠️ GEMINI_API_KEY missing. AI features disabled.")

    print("   ├─ 2. 請求 AI 策略解讀...")
    news_agent = NewsAgent() if enable_ai else None
    searcher = GoogleNewsSearcher() if enable_searcher else None
    
    try:
        if enable_ai and enable_searcher:
            ai_analysis = news_agent.get_market_outlook(events_data=events_str)
        else:
            ai_analysis = "AI 模組未啟用 (Missing Keys)"
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

            # Initialize Portfolio Manager (Personalization)
            pm = None
            try:
                pm = PortfolioManager()
                logger.info("✅ [Main] PortfolioManager initialized for Personalization.")
            except Exception as e:
                logger.warning(f"⚠️ Failed to init PortfolioManager: {e}")
            
            # Initialize AnalysisEngine
            engine = AnalysisEngine(strategy, news_agent, searcher, db, pm)
            
            # Process Lists
            if MY_HOLDINGS:
                results = engine.process_list(MY_HOLDINGS, "Holdings")
                all_analyzed_cards.extend(results)
                
            if MY_WATCHLIST:
                results = engine.process_list(MY_WATCHLIST, "Watchlist")
                all_analyzed_cards.extend(results)

    # 3. Generate Final Report (Minimal Version)
    print("\n📝 生成最終簡報 (Minimal Mode)...")
    
    # 3.1 Calculate Macro Status (Phase 6.5)
    # 3.1 Calculate Macro Status (Phase 6.5) - Now Consolidated
    macro_status = calculate_macro_status(market_regime)
        
    print(f"   🌍 Macro Status: {macro_status}")

    # Pass market_is_open flag to handle Market Closed scenario gracefully
    # Pass market_is_open tuple to handle Market Closed scenario gracefully with reason
    minimal_report_content = format_minimal_report(market_regime, all_analyzed_cards, macro_status, market_is_open=market_status_tuple)
    
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
        if Config.get('TG_TOKEN'):
            print("   ├─ Telegram")
            send_telegram(minimal_report_content, Config.get('TG_TOKEN'), Config.get('TG_CHAT_ID'))
            
        # LINE
        if Config.get('LINE_TOKEN'):
            print("   └─ LINE (Public Group)")
            send_line(minimal_report_content, Config.get('LINE_TOKEN'), user_id=None, group_id=Config.get('LINE_GROUP_ID'))
            
            # Send Private Report if user_id exists
            if Config.get('LINE_USER_ID'):
                private_report_content = format_private_portfolio_report(market_regime, all_analyzed_cards)
                if private_report_content:
                    print("   └─ LINE (Private Report)")
                    send_private_line(private_report_content, Config['LINE_TOKEN'], Config['LINE_USER_ID'])
                else:
                    print("   └─ LINE (Private): No warnings to report.")
    
    print("\n✅ 完成！")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, default='post_market', choices=['pre_market', 'post_market'])
    parser.add_argument('--dry-run', action='store_true', help='Run without sending network requests')
    args = parser.parse_args()
    run_analysis(args.mode, args.dry_run)
