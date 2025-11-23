import os
import argparse
import time
from market_data import get_market_regime
from garp_strategy import GARPStrategy
from report_formatter import format_stock_report
from notifier import send_line, send_telegram
from sheet_manager import get_stock_lists
from market_status import is_market_open, get_economic_events
from config import Config

def run_analysis(mode="post_market", dry_run=False):
    print(f"🚀 系統啟動中... 模式: {mode} (Dry Run: {dry_run})")
    
    # 0. 休市檢測
    if not is_market_open() and not dry_run:
        print("😴 今日美股休市，停止分析。")
        msg = "📢 【系統通知】\n今日美股休市，暫停發送日報。"
        if Config['TG_TOKEN']: send_telegram(msg, Config['TG_TOKEN'], Config['TG_CHAT_ID'])
        return

    # 0.1 市場體質檢測
    market_regime = get_market_regime()
    print(f"📊 市場狀態: SPY=${market_regime['spy_price']:.2f} (Bullish={market_regime['is_bullish']}), VIX={market_regime['vix']:.2f}")

    # 0.2 經濟日曆
    econ_events = get_economic_events()

    # 1. 從 Google Sheets 獲取清單
    print("📥 連線 Google Sheets...")
    MY_HOLDINGS, MY_WATCHLIST, MY_COSTS, STOCK_TYPES = get_stock_lists()
    
    if not MY_HOLDINGS and not MY_WATCHLIST:
        print("⚠️ 警告：清單為空或連線失敗")
        return

    title_suffix = "盤前分析" if mode == "pre_market" else "盤後日報"
    
    # 初始化報告容器
    report_content = f"🤖 【AI 投資{title_suffix} (GARP版)】 🤖\n"
    report_content += f"📊 市場: VIX {market_regime['vix']:.2f} | SPY {'🔥多頭' if market_regime['is_bullish'] else '❄️空頭'}\n"
    report_content += f"📅 本週大事:\n{econ_events}\n================\n"

    # Initialize Strategy
    strategy = GARPStrategy()

    # 1. 持股檢測
    if MY_HOLDINGS:
        report_content += "\n💼 【我的持股監控】\n"
        for symbol in MY_HOLDINGS:
            try:
                print(f"🔍 Analyzing Holding: {symbol}...")
                card = strategy.analyze(symbol)
                report = format_stock_report(card)
                
                # Add Cost Info if available
                my_cost = MY_COSTS.get(symbol, 0)
                if my_cost > 0:
                    report += f"\n💰 成本: ${my_cost}"
                
                report_content += f"{report}\n----------------\n"
                time.sleep(1) # Rate limit
            except Exception as e:
                print(f"❌ Error analyzing {symbol}: {e}")
                report_content += f"⚠️ {symbol}: 分析失敗 ({e})\n----------------\n"

    # 2. 關注清單
    if MY_WATCHLIST:
        report_content += "\n👀 【重點關注】\n"
        for symbol in MY_WATCHLIST:
            if symbol in MY_HOLDINGS: continue
            try:
                print(f"🔍 Analyzing Watchlist: {symbol}...")
                card = strategy.analyze(symbol)
                report = format_stock_report(card)
                report_content += f"{report}\n----------------\n"
                time.sleep(1)
            except Exception as e:
                print(f"❌ Error analyzing {symbol}: {e}")
                report_content += f"⚠️ {symbol}: 分析失敗 ({e})\n----------------\n"

    # 5. 發送或顯示
    if dry_run:
        print("\n📢 [Dry Run] 模擬發送報告內容：")
        print(report_content)
    else:
        print("\n📨 正在發送...")
        if Config['TG_TOKEN']:
            print(" -> Telegram")
            send_telegram(report_content, Config['TG_TOKEN'], Config['TG_CHAT_ID'])
            
        if Config['LINE_TOKEN']:
            print(" -> LINE")
            send_line(report_content, Config['LINE_TOKEN'], Config['LINE_USER_ID'])
    
    print("✅ 完成！")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='AI Stock Agent')
    parser.add_argument('--mode', type=str, default='post_market', choices=['pre_market', 'post_market'], help='Execution mode: pre_market or post_market')
    parser.add_argument('--dry-run', action='store_true', help='Run without sending messages')
    args = parser.parse_args()
    run_analysis(args.mode, args.dry_run)