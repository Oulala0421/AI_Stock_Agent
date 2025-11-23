import os
import argparse
import time
from market_data import get_market_regime
from garp_strategy import GARPStrategy
from news_agent import NewsAgent
from report_formatter import format_stock_report
from notifier import send_line, send_telegram
from sheet_manager import get_stock_lists
from market_status import is_market_open, get_economic_events
from data_models import OverallStatus
from config import Config

def run_analysis(mode="post_market", dry_run=False):
    """
    Main orchestration function for GARP + News Intelligence Agent.
    
    Workflow:
    1. Load Holdings & Watchlist from Google Sheets
    2. Initialize GARP Strategy + News Agent
    3. For each symbol:
       - Analyze with GARP strategy
       - Smart news fetching (PASS/WATCHLIST only)
       - Format & send report
    """
    print(f"🚀 AI Stock Agent (GARP + News) 啟動中...")
    print(f"   模式: {mode} | Dry Run: {dry_run}")
    
    # 0. Check Market Status
    market_is_open = is_market_open()
    if not market_is_open:
        print("😴 今日美股休市，執行休市簡報模式。")
    
    # 0.1 Market Regime Analysis (Always run)
    print("\n📊 市場體質檢測中...")
    market_regime = get_market_regime()
    print(f"   SPY: ${market_regime['spy_price']:.2f} | Bullish: {market_regime['is_bullish']}")
    print(f"   VIX: {market_regime['vix']:.2f}")
    
    # 0.2 Economic Calendar (Always run)
    econ_events = get_economic_events()
    
    # 1. Prepare Report Header
    title_suffix = "盤前分析" if mode == "pre_market" else "盤後日報"
    if not market_is_open:
        title_suffix += " (休市)"
    
    report_content = f"🤖 【AI 投資{title_suffix} - GARP版】 🤖\n"
    if not market_is_open:
        report_content += "😴 美股今日休市，提供市場概況。\n"
        
    report_content += f"📊 市場: VIX {market_regime['vix']:.2f} | SPY {'🔥多頭' if market_regime['is_bullish'] else '❄️空頭'}\n"
    report_content += f"📅 本週大事:\n{econ_events}\n"
    report_content += "=" * 40 + "\n"
    
    # 2. Analyze Stocks (Only if market is open)
    if market_is_open:
        # Load Stock Lists from Google Sheets
        print("\n📥 連接 Google Sheets...")
        MY_HOLDINGS, MY_WATCHLIST, MY_COSTS, STOCK_TYPES = get_stock_lists()
        
        if not MY_HOLDINGS and not MY_WATCHLIST:
            print("⚠️ 警告：持股及觀察清單為空或連線失敗")
            # Continue to send market report even if sheets fail
        else:
            print(f"✅ 載入完成: 持股 {len(MY_HOLDINGS)} 檔 | 觀察 {len(MY_WATCHLIST)} 檔")
            
            # Initialize Components
            strategy = GARPStrategy()
            news_agent = NewsAgent()
            
            # Analyze Holdings
            if MY_HOLDINGS:
                report_content += "\n💼 【我的持股監控】\n"
                for symbol in MY_HOLDINGS:
                    try:
                        print(f"\n🔍 分析持股: {symbol}")
                        
                        # Step 1: GARP Analysis
                        card = strategy.analyze(symbol)
                        print(f"   ├─ 評級: {card.overall_status}")
                        
                        # Step 2: Smart News Fetching (Cost Optimization)
                        news_summary = None
                        if card.overall_status in [OverallStatus.PASS.value, OverallStatus.WATCHLIST.value]:
                            print(f"   ├─ 獲取新聞...")
                            news_summary = news_agent.get_stock_news(symbol)
                        else:
                            print(f"   ├─ 跳過新聞 (REJECT 狀態)")
                        
                        # Step 3: Format Report
                        report = format_stock_report(card, news_summary)
                        
                        # Step 4: Add Cost Info
                        my_cost = MY_COSTS.get(symbol, 0)
                        if my_cost > 0:
                            report += f"\n💰 成本: ${my_cost}"
                        
                        report_content += f"{report}\n" + "-" * 40 + "\n"
                        print(f"   └─ ✅ 完成")
                        
                        # Rate Limiting
                        time.sleep(2)
                        
                    except Exception as e:
                        print(f"   └─ ❌ 錯誤: {e}")
                        report_content += f"⚠️ {symbol}: 分析失敗 ({e})\n" + "-" * 40 + "\n"
            
            # Analyze Watchlist
            if MY_WATCHLIST:
                report_content += "\n👀 【重點關注】\n"
                for symbol in MY_WATCHLIST:
                    if symbol in MY_HOLDINGS:
                        continue  # Skip duplicates
                    
                    try:
                        print(f"\n🔍 分析觀察股: {symbol}")
                        
                        # Step 1: GARP Analysis
                        card = strategy.analyze(symbol)
                        print(f"   ├─ 評級: {card.overall_status}")
                        
                        # Step 2: Smart News Fetching
                        news_summary = None
                        if card.overall_status in [OverallStatus.PASS.value, OverallStatus.WATCHLIST.value]:
                            print(f"   ├─ 獲取新聞...")
                            news_summary = news_agent.get_stock_news(symbol)
                        else:
                            print(f"   ├─ 跳過新聞 (REJECT 狀態)")
                        
                        # Step 3: Format Report
                        report = format_stock_report(card, news_summary)
                        report_content += f"{report}\n" + "-" * 40 + "\n"
                        print(f"   └─ ✅ 完成")
                        
                        # Rate Limiting
                        time.sleep(2)
                        
                    except Exception as e:
                        print(f"   └─ ❌ 錯誤: {e}")
                        report_content += f"⚠️ {symbol}: 分析失敗 ({e})\n" + "-" * 40 + "\n"
    else:
        report_content += "\n🏖️ 休市期間不進行個股分析。\n"
        report_content += "建議回顧上週持股表現或閱讀相關財經新聞。\n"
    
    # 3. Send or Display Report
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
            send_line(report_content, Config['LINE_TOKEN'], Config['LINE_USER_ID'])
    
    print("\n✅ 完成！")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='AI Stock Agent - GARP Strategy with News Intelligence')
    parser.add_argument('--mode', type=str, default='post_market', 
                        choices=['pre_market', 'post_market'], 
                        help='Execution mode: pre_market or post_market')
    parser.add_argument('--dry-run', action='store_true', 
                        help='Run without sending messages (print to console only)')
    args = parser.parse_args()
    
    run_analysis(args.mode, args.dry_run)