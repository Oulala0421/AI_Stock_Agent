import os
import argparse
import time
from market_data import get_market_regime
from garp_strategy import GARPStrategy
# V2 architecture is now the default
from news_agent import NewsAgent
from report_formatter import format_stock_report
from notifier import send_line, send_telegram
from sheet_manager import get_stock_lists
from market_status import is_market_open, get_economic_events, get_earnings_calendar
from data_models import OverallStatus
from config import Config
from database_manager import DatabaseManager

def run_analysis(mode="post_market", dry_run=False):
    print(f"🚀 AI Stock Agent V2 (GARP + News) 啟動中...")
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
    ai_analysis = news_agent.get_market_outlook(events_data=events_str)
    
    # Combine for Report
    market_outlook_section = f"""📅 **本週重要財經事件 (Hard Facts)**:
{events_str}

🧠 **AI 策略解讀 (Opinion)**:
{ai_analysis}""".strip()
    
    # 1. Prepare Report Header
    title_suffix = "盤前分析" if mode == "pre_market" else "盤後日報"
    if not market_is_open: title_suffix += " (休市)"
    
    report_content = f"⚠️ 程式還在修改中，看看就好 ⚠️\n🤖 【AI 投資{title_suffix} - GARP V2】 🤖\n"
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
                        card = strategy.analyze(symbol)
                        print(f"   ├─ 評級: {card.overall_status}")
                        
                        news_summary = None
                        if card.overall_status in [OverallStatus.PASS.value, OverallStatus.WATCHLIST.value]:
                            print(f"   ├─ 獲取新聞...")
                            news_summary = news_agent.get_stock_news(symbol)
                        else:
                            print(f"   ├─ 跳過新聞 (REJECT)")
                        
                        # Format report
                        report = format_stock_report(card, news_summary)
                        
                        # Database: Save snapshot and check status change
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
                        if my_cost > 0: report += f"\n💰 成本: ${my_cost}"
                        
                        report_content += f"{report}{status_indicator}\n" + "-" * 40 + "\n"
                        print(f"   └─ ✅ 完成")
                        time.sleep(2)
                    except Exception as e:
                        print(f"   └─ ❌ 錯誤: {e}")
                        report_content += f"⚠️ {symbol}: 分析失敗\n" + "-" * 40 + "\n"
            
            # Analyze Watchlist (Similar logic)
            if MY_WATCHLIST:
                report_content += "\n👀 【重點關注】\n"
                for symbol in MY_WATCHLIST:
                    if symbol in MY_HOLDINGS: continue
                    try:
                        print(f"\n🔍 分析觀察股: {symbol}")
                        card = strategy.analyze(symbol)
                        print(f"   ├─ 評級: {card.overall_status}")
                        
                        news_summary = None
                        if card.overall_status in [OverallStatus.PASS.value, OverallStatus.WATCHLIST.value]:
                            print(f"   ├─ 獲取新聞...")
                            news_summary = news_agent.get_stock_news(symbol)
                        else:
                            print(f"   ├─ 跳過新聞 (REJECT)")
                        
                        # Format report
                        report = format_stock_report(card, news_summary)
                        
                        # Database: Save snapshot and check status change
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
                        
                        report_content += f"{report}{status_indicator}\n" + "-" * 40 + "\n"
                        print(f"   └─ ✅ 完成")
                        time.sleep(2)
                    except Exception as e:
                        print(f"   └─ ❌ 錯誤: {e}")
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
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    run_analysis(args.mode, args.dry_run)
