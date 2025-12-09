from data_models import StockHealthCard, OverallStatus
from typing import Optional

def format_stock_report(card: StockHealthCard, news_summary: Optional[str] = None) -> str:
    """
    Formats a StockHealthCard into a readable string optimized for mobile (Telegram/LINE).
    
    Args:
        card: StockHealthCard containing analysis results
        news_summary: Optional news intelligence from Perplexity AI
    """
    # 1. Header
    status_emoji = {
        OverallStatus.PASS.value: "🟢",
        OverallStatus.WATCHLIST.value: "🟡",
        OverallStatus.REJECT.value: "🔴"
    }.get(card.overall_status, "⚪")
    
    header = f"{status_emoji} {card.symbol} | ${card.price:.2f} | {card.overall_status}"
    
    # 2. Tags Section
    all_tags = []
    all_tags.extend(card.quality_check.get('tags', []))
    all_tags.extend(card.valuation_check.get('tags', []))
    all_tags.extend(card.solvency_check.get('tags', []))
    all_tags.extend(card.technical_setup.get('tags', []))
    
    # Filter out "No Data" tags to keep it clean, unless it's the only info
    filtered_tags = [tag for tag in all_tags if "⚪" not in tag]
    if not filtered_tags and all_tags:
        filtered_tags = all_tags # Keep original if everything is empty
        
    tags_str = " | ".join(filtered_tags)
    
    # 3. Data Summary
    # Extract key metrics safely
    roe = card.quality_check.get('roe')
    roe_str = f"{roe*100:.1f}%" if roe is not None else "N/A"
    
    peg = card.valuation_check.get('peg_ratio')
    peg_str = f"{peg:.2f}" if peg is not None else "N/A"
    
    de = card.solvency_check.get('debt_to_equity')
    de_str = f"{de:.0f}%" if de is not None else "N/A"
    
    summary_line = f"📊 ROE: {roe_str} | PEG: {peg_str} | Debt/Eq: {de_str}"
    
    # 4. Prediction Section (Regime-Based Bootstrap Engine)
    prediction_section = ""
    if hasattr(card, 'predicted_return_1w') and card.predicted_return_1w is not None:
        pred_val = card.predicted_return_1w
        confidence = card.confidence_score if hasattr(card, 'confidence_score') and card.confidence_score else 0.5
        
        # Determine trend emoji and label
        if pred_val > 2.0:
            trend_emoji = "🚀"
            trend_label = "強勢看漲"
        elif pred_val > 0.5:
            trend_emoji = "📈"
            trend_label = "看漲"
        elif pred_val > -0.5:
            trend_emoji = "➡️"
            trend_label = "持平"
        elif pred_val > -2.0:
            trend_emoji = "📉"
            trend_label = "看跌"
        else:
            trend_emoji = "⚠️"
            trend_label = "強勢看跌"
        
        # Confidence level
        if confidence > 0.7:
            conf_label = "高"
        elif confidence > 0.5:
            conf_label = "中"
        else:
            conf_label = "低"
        
        pred_sign = "+" if pred_val >= 0 else ""
        prediction_section = f"\n🔮 AI預測: {trend_label} ({pred_sign}{pred_val:.2f}%) | 信心: {conf_label} ({confidence:.0%})"
    
    # 5. News Section
    news_section = ""
    if news_summary:
        news_section = f"\n\n📰 MARKET INTELLIGENCE:\n{news_summary}"
    
    # 5. Red Flags Section
    red_flags_section = ""
    if card.red_flags:
        red_flags_list = "\n".join([f"  - {flag}" for flag in card.red_flags])
        red_flags_section = f"\n\n⚠️ WARNINGS:\n{red_flags_list}"
        
    # 6. Construct Final Message
    report = f"""
{header}
{tags_str}
{summary_line}{prediction_section}{news_section}{red_flags_section}
""".strip()

    return report

def format_minimal_report(market_status, stock_cards):
    """
    生成極簡戰情摘要 (Sprint 4 Spec)
    只包含：Header, Action Items, Predictions
    """
    from config import Config # Lazy import to avoid circular dependency if any
    
    # 1. Header 區塊
    report = [f"🤖 【AI 投資戰情】"]
    
    # 市場氣象
    vix_val = market_status.get('vix')
    if isinstance(vix_val, (int, float)):
        vix_display = f"VIX {vix_val:.2f}"
    else:
        vix_display = f"VIX {vix_val}"
    
    # Robust handling for spy stage/trend
    spy_trend = "🌤️ 多頭" if market_status.get('is_bullish') else "⛈️ 空頭"
    if 'stage' in market_status: # Fallback to stage string if present
       spy_trend = "🌤️ 多頭" if "Bull" in market_status.get('stage', '') else "⛈️ 空頭"
        
    report.append(f"📊 市場: {spy_trend} | {vix_display}")
    
    # [Fix] 動態連結：只有當設定了 URL 才顯示，否則隱藏
    if Config.get("DASHBOARD_URL"):
        report.append(f"🔗 [點擊查看戰情室]({Config['DASHBOARD_URL']})")
    
    report.append("") # 空行分隔

    # 2. Body 區塊 (Action Items)
    # 只顯示 PASS (持股/買入) 和 WATCHLIST (觀察)
    # Check if stock_cards is empty or None
    if not stock_cards:
        report.append("💤 本日無重點關注標的")
        return "\n".join(report)

    target_stocks = [c for c in stock_cards if c.overall_status in ["PASS", "WATCHLIST"]]
    
    if not target_stocks:
        report.append("💤 本日無重點關注標的")
    
    for card in target_stocks:
        # 狀態圖示
        icon = "🟢" if card.overall_status == "PASS" else "🟡"
        if card.overall_status == "REJECT": icon = "🔴" # 以防萬一
        
        # 價格行
        report.append(f"{icon} {card.symbol} | ${card.price:.2f}")
        
        # 預測行 (如果有預測數據)
        if hasattr(card, 'predicted_return_1w') and card.predicted_return_1w is not None:
            pred_pct = card.predicted_return_1w # It is typically already in percentage (float) like 1.25 or 0.0125?
            # From main.py: card.predicted_return_1w = prediction.get('predicted_return_1w') which is * 100 in prediction_engine.
            # So card.predicted_return_1w is 1.25 for 1.25%.
            
            direction = "+" if pred_pct > 0 else ""
            
            # 信心度轉文字
            conf_str = "低"
            if card.confidence_score and card.confidence_score >= 0.7: conf_str = "高"
            elif card.confidence_score and card.confidence_score >= 0.5: conf_str = "中"
            
            report.append(f"🔮 預測: {direction}{pred_pct:.1f}% (信心: {conf_str})")
        
        # AI 觀點 (只取摘要)
        # Note: news_summary in main.py is currently passed as a STRING to format_stock_report.
        # But here we are iterating cards.
        # We need to rely on what's IN the card.
        # Currently main.py does NOT store the summary string back into the card object, 
        # it passes it separately to format_stock_report.
        # If we use this bulk formatter, we need to ensure the card has the summary attached.
        # Or we need to rely on `raw_data` if saved.
        # For now, I will implement as requested, but user needs to adhere to how main.py works.
        # Use getattr safely.
        if hasattr(card, 'news_summary_str'):
             # If main.py attaches the string (which already includes icons like 💡 or 📰)
             report.append(f"{card.news_summary_str}")
        elif hasattr(card, 'raw_data') and isinstance(card.raw_data, dict):
             # Try to find reason in raw structure if available
             pass
        
        report.append("") # 股票間空行

    # 3. Footer (已移除新聞列表與詳細財務指標)
    
    return "\n".join(report)
