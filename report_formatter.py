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
