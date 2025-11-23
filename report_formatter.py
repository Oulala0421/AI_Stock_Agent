from data_models import StockHealthCard, OverallStatus

def format_stock_report(card: StockHealthCard) -> str:
    """
    Formats a StockHealthCard into a readable string optimized for mobile (Telegram/LINE).
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
    
    # 3. Red Flags Section
    red_flags_section = ""
    if card.red_flags:
        red_flags_list = "\n".join([f"  - {flag}" for flag in card.red_flags])
        red_flags_section = f"\n⚠️ WARNINGS:\n{red_flags_list}"
        
    # 4. Data Summary
    # Extract key metrics safely
    roe = card.quality_check.get('roe')
    roe_str = f"{roe*100:.1f}%" if roe is not None else "N/A"
    
    peg = card.valuation_check.get('peg_ratio')
    peg_str = f"{peg:.2f}" if peg is not None else "N/A"
    
    de = card.solvency_check.get('debt_to_equity')
    de_str = f"{de:.0f}%" if de is not None else "N/A"
    
    summary_line = f"📊 ROE: {roe_str} | PEG: {peg_str} | Debt/Eq: {de_str}"
    
    # 5. Construct Final Message
    report = f"""
{header}
{tags_str}
{summary_line}{red_flags_section}
""".strip()

    return report
