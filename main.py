import os
import argparse
from market_data import fetch_and_analyze, get_market_regime
from strategy import get_market_news, get_fundamentals, generate_ai_briefing, scan_market_opportunities, calculate_position_size, calculate_confidence_score
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
    report_private = f"🤖 【AI 投資{title_suffix} - 私密版】 🤖\n"
    report_private += f"📊 市場: VIX {market_regime['vix']:.2f} | SPY {'🔥多頭' if market_regime['is_bullish'] else '❄️空頭'}\n"
    report_private += f"📅 本週大事:\n{econ_events}\n================\n"
    
    report_public = f"🤖 【AI 投資{title_suffix} - 市場版】 🤖\n"
    report_public += f"📊 市場情緒: {'😰 恐慌' if market_regime['vix']>25 else '😊 貪婪' if market_regime['vix']<15 else '😐 中性'}\n"
    report_public += f"📅 本週大事:\n{econ_events}\n================\n"

    # 1. 持股檢測 (只給 Private)
    if MY_HOLDINGS:
        report_private += "\n💼 【我的持股監控】\n"
        for symbol in MY_HOLDINGS:
            data = fetch_and_analyze(symbol)
            if not data: continue
            
            news_text, sentiment = get_market_news(symbol)
            fund = get_fundamentals(symbol, is_etf=data['is_etf'])
            
            # 計算戰鬥力分數
            quality_data = {
                "dual_momentum": data['trend']['dual_momentum']['is_bullish'],
                "roe": fund['roe'],
                "is_etf": data['is_etf'],
                "target": fund['target'],
                "fraud_risk": False
            }
            
            technical_data = data['momentum']
            technical_data['price'] = data['price']
            
            conf_score = calculate_confidence_score(market_regime, quality_data, technical_data, sentiment)
            
            # 生成 AI 簡報
            ai_text = generate_ai_briefing(symbol, data, news_text, sentiment, fund, "HOLDING", mode)
            
            # 計算倉位
            shares, amount, stop_loss, signal = calculate_position_size(data['price'], data['volatility']['atr'], conf_score)
            my_cost = MY_COSTS.get(symbol, 0)
            
            # 私密版詳細數據
            report_private += f"🔸 {symbol} (分:{conf_score:.0f} | ${data['price']:.2f})\n"
            report_private += ai_text + "\n"
            report_private += f"💰 成本: ${my_cost} | 🛡️ 停損: ${stop_loss:.2f}\n"
            report_private += f"💡 建議: {'加碼' if conf_score>=60 else '持有' if conf_score>=40 else '減碼'} (${amount:.0f})\n"
            report_private += "----------------\n"

    # 2. 關注清單 (Public & Private)
    if MY_WATCHLIST:
        public_section_header = "\n👀 【重點關注】\n"
        report_private += public_section_header
        report_public += public_section_header
        
        for symbol in MY_WATCHLIST:
            if symbol in MY_HOLDINGS: continue

            data = fetch_and_analyze(symbol)
            if not data: continue
            
            news_text, sentiment = get_market_news(symbol)
            fund = get_fundamentals(symbol, is_etf=data['is_etf'])
            
            quality_data = {
                "dual_momentum": data['trend']['dual_momentum']['is_bullish'],
                "roe": fund['roe'],
                "is_etf": data['is_etf'],
                "target": fund['target'],
                "fraud_risk": False
            }
            
            technical_data = data['momentum']
            technical_data['price'] = data['price']
            
            conf_score = calculate_confidence_score(market_regime, quality_data, technical_data, sentiment)
            
            ai_text = generate_ai_briefing(symbol, data, news_text, sentiment, fund, "WATCHLIST", mode)
            
            # 公開版內容 (去敏感化)
            trend_icon = "🔥" if data['trend']['dual_momentum']['is_bullish'] else "❄️"
            public_content = f"🔹 {symbol} {trend_icon}\n{ai_text}\n----------------\n"
            report_public += public_content
            
            # 私密版內容 (含分數與建議)
            private_content = f"🔹 {symbol} (分:{conf_score:.0f} | ${data['price']:.2f})\n{ai_text}\n"
            shares, amount, stop_loss, signal = calculate_position_size(data['price'], data['volatility']['atr'], conf_score)
            private_content += f"💡 凱利: ${amount:.0f} ({shares}股)\n----------------\n"
            report_private += private_content

    # 3. 市場掃描 (僅 Post-Market 執行)
    if mode == "post_market":
        discovery_section = "\n🔍 【AI 自動淘金 (超跌股)】\n"
        discovered = scan_market_opportunities()
        
        if discovered:
            for symbol in discovered:
                if symbol in MY_HOLDINGS or symbol in MY_WATCHLIST: continue
                data = fetch_and_analyze(symbol)
                if not data: continue
                
                # 簡化版處理
                fund = get_fundamentals(symbol, is_etf=data['is_etf'])
                ai_text = generate_ai_briefing(symbol, data, "", 0, fund, "DISCOVERY", mode)
                
                content = f"🚀 {symbol} (RSI: {data['momentum']['rsi']:.1f})\n{ai_text}\n----------------\n"
                report_private += discovery_section + content
                report_public += discovery_section + content
                discovery_section = "" # 清空標題以免重複
        else:
            msg = "今日無顯著超跌標的。\n"
            report_private += discovery_section + msg
            report_public += discovery_section + msg
    else:
        print("⏩ Pre-market 模式跳過市場掃描")

    # 5. 發送或顯示
    if dry_run:
        print("\n📢 [Dry Run] 模擬發送報告內容：")
        print("\n--- 私密版報告 (Telegram) ---")
        print(report_private)
        print("\n--- 市場版報告 (LINE) ---")
        print(report_public)
    else:
        print("\n📨 正在發送...")
        if Config['TG_TOKEN']:
            print(" -> Telegram (私密)")
            send_telegram(report_private, Config['TG_TOKEN'], Config['TG_CHAT_ID'])
            
        if Config['LINE_TOKEN']:
            print(" -> LINE (公開)")
            send_line(report_public, Config['LINE_TOKEN'], Config['LINE_USER_ID'])
    
    print("✅ 完成！")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='AI Stock Agent')
    parser.add_argument('--mode', type=str, default='post_market', choices=['pre_market', 'post_market'], help='Execution mode: pre_market or post_market')
    parser.add_argument('--dry-run', action='store_true', help='Run without sending messages')
    args = parser.parse_args()
    run_analysis(args.mode, args.dry_run)