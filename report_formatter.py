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

    # 3.5 DCF Valuation Section
    dcf_section = ""
    dcf_data = card.valuation_check.get('dcf')
    if dcf_data and dcf_data.get('intrinsic_value'):
        intrinsic_val = dcf_data['intrinsic_value']
        discount_rate = dcf_data.get('discount_rate', 0.09)
        mos = card.valuation_check.get('margin_of_safety_dcf', 0.0)
        
        mos_str = f"+{mos:.1%}" if mos > 0 else f"{mos:.1%}"
        mos_icon = "✅" if mos > 0.15 else ("⚠️" if mos < -0.1 else "")
        
        analyst_target = card.valuation_check.get('fair_value')
        analyst_str = f"${analyst_target:.2f}" if analyst_target else "N/A"
        
        dcf_section = f"\n💰 估值分析 (DCF):\n   • 現價: ${card.price:.2f}\n   • AI 內在價值: ${intrinsic_val:.2f} (折現率: {discount_rate:.1%})\n   • 安全邊際: {mos_str} {mos_icon}\n   • 分析師目標: {analyst_str} (僅供參考)"
    
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
{summary_line}{dcf_section}{prediction_section}{news_section}{red_flags_section}
""".strip()

    return report

def format_minimal_report(market_status, stock_cards):
    """
    生成極簡戰情摘要 (Compact Layout for Mobile)
    Format:
    🤖 **AI 投資戰情** (MM/DD)
    📊 市場: 🌤️多頭 | VIX 14.5
    
    🟢 **NVDA** $120.00
       └─ 🚀 +2.5% (高) | 💰 Deep Value
       └─ 💡 營收超預期...
    """
    from config import Config
    from datetime import datetime
    
    # 1. Header 區塊
    today_str = datetime.now().strftime("%m/%d")
    report = [f"🤖 **AI 投資戰情** ({today_str})"]
    
    # 市場氣象
    vix_val = market_status.get('vix')
    if isinstance(vix_val, (int, float)):
        vix_display = f"VIX {vix_val:.1f}"
    else:
        vix_display = f"VIX {vix_val}"
    
    spy_trend = "🌤️ 多頭" if market_status.get('is_bullish') else "⛈️ 空頭"
    if 'stage' in market_status: 
       spy_trend = "🌤️ 多頭" if "Bull" in market_status.get('stage', '') else "⛈️ 空頭"
        
    report.append(f"📊 市場: {spy_trend} | {vix_display}")
    
    # 動態連結
    if Config.get("DASHBOARD_URL"):
        report.append(f"🔗 [點擊查看戰情室]({Config['DASHBOARD_URL']})")
    
    report.append("") # 空行分隔

    # 2. Body 區塊
    if not stock_cards:
        report.append("💤 本日無重點關注標的")
        return "\n".join(report)

    target_stocks = [c for c in stock_cards if c.overall_status in ["PASS", "WATCHLIST"]]
    
    if not target_stocks:
        report.append("💤 本日無重點關注標的")
    
    for card in target_stocks:
        # A. 第一行: 狀態圖示 + Symbol (Bold) + Price
        icon = "🟢" if card.overall_status == "PASS" else "🟡"
        if card.overall_status == "REJECT": icon = "🔴"
        
        # Telegram Markdown supports **bold**, but Line might not. 
        # We assume Telegram mainly or text-only fallback.
        header_line = f"{icon} **{card.symbol}** ${card.price:.2f}"
        report.append(header_line)
        
        # B. 第二行: 預測 + DCF Tag
        details_parts = []
        
        # 預測
        if hasattr(card, 'predicted_return_1w') and card.predicted_return_1w is not None:
            pred_pct = card.predicted_return_1w
            direction_emoji = "🚀" if pred_pct > 2.0 else ("📈" if pred_pct > 0.5 else ("📉" if pred_pct < -0.5 else "➡️"))
            direction_sign = "+" if pred_pct > 0 else ""
            
            # Confidence
            conf_str = "低"
            if card.confidence_score and card.confidence_score >= 0.7: conf_str = "高"
            elif card.confidence_score and card.confidence_score >= 0.5: conf_str = "中"
            
            details_parts.append(f"{direction_emoji} {direction_sign}{pred_pct:.1f}% ({conf_str})")
        
        # Deep Value Tag
        dcf_mos = card.valuation_check.get('margin_of_safety_dcf')
        if dcf_mos and dcf_mos > 0.15:
            details_parts.append(f"💰 Deep Value")
            
        if details_parts:
            report.append(f"   └─ {' | '.join(details_parts)}")
        
        # C. 第三行: AI 摘要
        # Try to get simplified summary
        summary_text = ""
        if hasattr(card, 'news_summary_str') and card.news_summary_str:
            # Extract just the text part if possible, removing extra newlines or headers
            # Original format: "💡 AI: 😃 Positive\n💬 reason..."
            # We want just "💡 reason..." or similar
            raw_summary = card.news_summary_str
            # Simple cleanup to make it one line if possible or short
            lines = raw_summary.split('\n')
            clean_lines = []
            for line in lines:
                if "AI:" in line: continue # Skip sentiment line to save space? Or keep emoji?
                # Actually user wants "💡 營收超預期..."
                # Let's keep the reason part.
                if line.strip():
                     clean_lines.append(line.strip())
            
            # Join and truncate if too long?
            full_text = " ".join(clean_lines)
            # Remove redundant emojis if any
            full_text = full_text.replace("💬", "").replace("💡", "").strip()
            summary_text = f"💡 {full_text}"
            
        if summary_text:
             report.append(f"   └─ {summary_text}")
        
        report.append("") # 股票間空行

    return "\n".join(report)

def format_private_portfolio_report(market_status, stock_cards):
    """
    生成私人投顧報告 (Personalized)
    包含：Risk Warnings (Concentration, Correlation)
    """
    from config import Config
    
    # Filter cards that have private notes
    cards_with_notes = [c for c in stock_cards if c.private_notes]
    
    if not cards_with_notes:
        return None # No private warnings, skip sending
        
    report = ["🕵️‍♂️ 【私人投資顧問報告】", ""]
    
    # 市場狀態摘要
    spy_trend = "🌤️ 多頭" if market_status.get('is_bullish') else "⛈️ 空頭"
    z_score_str = f"{market_status.get('z_score', 0.00):.2f}"
    report.append(f"📊 市場狀態: {spy_trend} (Z-Score: {z_score_str})")
    report.append("")
    
    report.append("🚨 風險警示 (針對您的持倉):")
    
    for i, card in enumerate(cards_with_notes, 1):
        status_emoji = {
            "PASS": "🟢", "WATCHLIST": "🟡", "REJECT": "🔴"
        }.get(card.overall_status, "⚪")
        
        report.append(f"{i}. {card.symbol} ({status_emoji} {card.overall_status})")
        
        for note in card.private_notes:
             report.append(f"   {note}")
             
        # Add a small suggestion logic
        if "集中度過高" in str(card.private_notes) or "高度連動" in str(card.private_notes):
            report.append(f"   💡 建議: 減量買進或觀察")
        elif "低" in str(card.private_notes) and "相關性" in str(card.private_notes):
             report.append(f"   ✅ 建議: 可作為分散配置")

        report.append("")
        
    return "\n".join(report)
