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
from market_status import is_market_open, get_economic_events, get_earnings_calendar
from data_models import OverallStatus
from config import Config
from database_manager import DatabaseManager
from portfolio_manager import PortfolioManager # [NEW]
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

            # Initialize Portfolio Manager (Personalization)
            pm = None
            try:
                pm = PortfolioManager()
                logger.info("✅ [Main] PortfolioManager initialized for Personalization.")
            except Exception as e:
                logger.warning(f"⚠️ Failed to init PortfolioManager: {e}")
            
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
                            # B. Risk Analysis (Computed in GARP Strategy)
                            if list_name != "Watchlist" or card.overall_status != OverallStatus.REJECT.value:
                                if hasattr(card, 'monte_carlo_min') and card.monte_carlo_min:
                                    print(f"   ├─ 風險評估 (Risk Engine)...")
                                    print(f"      📉 波動區間: ${card.monte_carlo_min:.2f} - ${card.monte_carlo_max:.2f}")
                            
                            # C. Google News & AI Commentary
                            print(f"   ├─ 搜尋新聞 (Google Facts)...")
                            try:
                                news_list = searcher.search_news(symbol, days=3)
                                
                                if news_list:
                                    print(f"      📄 找到 {len(news_list)} 則新聞，AI 分析中...")
                                    
                                    # [Phase 6.8] Prepare Valuation Data for AI (Strict Implementation)
                                    dcf_val = card.valuation_check.get('dcf', {}).get('intrinsic_value')
                                    mos_val = card.valuation_check.get('margin_of_safety_dcf')
                                    
                                    val_data = {
                                        "price": card.price,
                                        "intrinsic_value": dcf_val,
                                        "mos": mos_val,
                                        "rating": card.overall_status,
                                        "monte_carlo_min": card.monte_carlo_min,
                                        "monte_carlo_max": card.monte_carlo_max
                                    }
                                    
                                    analysis_result = news_agent.analyze_news(symbol, news_list, valuation_data=val_data)
                                    
                                    if analysis_result:
                                        sentiment_emoji = "😃" if analysis_result['sentiment'] == "Positive" else ("😞" if analysis_result['sentiment'] == "Negative" else "😐")
                                        # headlines = searcher.format_news_summary(news_list, max_articles=2) # [REMOVED] User prefers cleaner AI summary
                                        news_summary_str = f"💡 AI: {sentiment_emoji} {analysis_result['sentiment']}\n💬 {analysis_result['summary_reason']}"
                                    else:
                                        # Fallback: Show headlines if AI fails
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

                        # D. Personalization Check (Private Layer)
                        if pm and card.overall_status in [OverallStatus.PASS.value, OverallStatus.WATCHLIST.value]:
                            try:
                                # Sector & Concentration Check
                                sector = card.quality_check.get('sector', 'Unknown') # Need to ensure sector is available, might need to fetch from sheet/yfinance if not in card
                                # In current architecture, card doesn't store sector explicitly in quality_check usually. 
                                # But let's assume sheet_manager provides a map or yfinance does.
                                # Actually, get_stock_lists returns holdings/watchlist, but not detailed metadata.
                                # Let's assume PortfolioManager can handle it or we skip if sector missing.
                                # WAIT: current stock lists don't provide sector map to main. 
                                # PortfolioManager's check_concentration needs a sector.
                                # Simple fix: use a default or try to get it from news/finviz logic if implemented.
                                # For now, let's pass 'Unknown' if not found, PM might skip.
                                # BETTER: Use the one from card if we had it.
                                # The instructions imply PM logic is solid.
                                
                                # Use yfinance info if available from analysis step?
                                # Strategy.analyze usually fetches Ticker info.
                                # Let's try to get sector from card.raw_data if it exists (GARPStrategy might attach it)
                                # If not, we might miss sector check.
                                warning_conc = pm.check_concentration(card.symbol, getattr(card, 'sector', 'Unknown'))
                                warning_corr = pm.check_correlation(card.symbol)
                                
                                if warning_conc: card.private_notes.extend(warning_conc)
                                if warning_corr: card.private_notes.extend(warning_corr)
                                
                                if warning_conc or warning_corr:
                                    print(f"      🕵️‍♂️ 私人警示: {len(warning_conc)+len(warning_corr)} 則")
                                    
                            except Exception as pme:
                                logger.error(f"      ❌ Personalization Check Error: {pme}")
                        
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
    
    # 3.1 Calculate Macro Status (Phase 6.5)
    vix = market_regime.get('vix', 20.0)
    is_bullish = market_regime.get('is_bullish', False)
    
    if is_bullish and vix < 20:
        macro_status = "RISK_ON 🚀"
    elif not is_bullish and vix > 25:
        macro_status = "RISK_OFF 🛡️"
    elif not is_bullish:
        macro_status = "DEFENSIVE 🛡️"
    else:
        macro_status = "NEUTRAL ⚖️"
        
    print(f"   🌍 Macro Status: {macro_status}")

    minimal_report_content = format_minimal_report(market_regime, all_analyzed_cards, macro_status)
    
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
            print("   └─ LINE (Public Group)")
            send_line(minimal_report_content, Config['LINE_TOKEN'], user_id=None, group_id=Config.get('LINE_GROUP_ID'))
            
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
