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

def format_minimal_report(market_status, stock_cards, macro_status: Optional[str] = "NEUTRAL"):
    """
    生成極簡戰情摘要 (Tactical Tree Layout)
    Format:
    🤖 **AI 投資戰情** (MM/DD)
    📊 市場: 🌤️多頭 | VIX 14.5
    🌍 宏觀: RISK_ON
    
    🟢 **NVDA** $120.00
       └─ 💰 AI估值: $135.00 (MoS +12%)
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
    
    spy_trend = "🌤️多頭" if market_status.get('is_bullish') else "⛈️空頭"
    if 'stage' in market_status and "Bull" in market_status.get('stage', ''): 
       spy_trend = "🌤️多頭"
    elif 'stage' in market_status and "Bear" in market_status.get('stage', ''):
       spy_trend = "⛈️空頭"
        
    report.append(f"📊 市場: {spy_trend} | {vix_display}")
    
    # 宏觀狀態 (New)
    if macro_status:
        report.append(f"🌍 宏觀: {macro_status}")
    
    # 動態連結
    if Config.get("DASHBOARD_URL"):
        report.append(f"🔗 [戰情室]({Config['DASHBOARD_URL']})")
    
    report.append("") # 空行分隔

    # 2. Body 區塊
    if not stock_cards:
        report.append("💤 本日無重點關注標的")
        return "\n".join(report)

    target_stocks = [c for c in stock_cards if c.overall_status in ["PASS", "WATCHLIST"]]
    
    if not target_stocks:
        report.append("💤 本日無重點關注標的")
    
    for card in target_stocks:
        # A. 第一行: 標題 (Symbol + Rating)
        # Rating Emoji
        rating_map = {
            "PASS": "🟢",
            "WATCHLIST": "🟡",
            "REJECT": "🔴"
        }
        icon = rating_map.get(card.overall_status, "⚪")
        header_line = f"{icon} **{card.symbol}**"
        report.append(header_line)
        
        # B. 第二行: 硬數據 (Price | DCF | Range)
        line2_parts = []
        line2_parts.append(f"現價: ${card.price:.2f}") # Actually user example: "現價: $458". I'll use .2f generally to be safe.
        
        dcf_data = card.valuation_check.get('dcf', {})
        intrinsic_val = dcf_data.get('intrinsic_value') if dcf_data else None
        
        if intrinsic_val and intrinsic_val > 0:
            # Calculate MoS for display and logic
            mos_dcf = (intrinsic_val - card.price) / card.price
            if card.price > intrinsic_val: # Stock is trading at a premium to intrinsic value
                val_str = f"💰 DCF估值: ${intrinsic_val:.0f} (溢價 {-mos_dcf:.0%})" # Display positive premium
            else: # Stock is trading at a discount to intrinsic value
                val_str = f"💰 DCF估值: ${intrinsic_val:.0f} (低估 {mos_dcf:.0%})" # Display positive discount
            line2_parts.append(val_str)
        else:
            line2_parts.append("💰 DCF: N/A")
            mos_dcf = 0.0 # Initialize for later use in line C

        if card.monte_carlo_min is not None and card.monte_carlo_max is not None:
            line2_parts.append(f"區間 ${card.monte_carlo_min:.0f}-${card.monte_carlo_max:.0f}")
        
        report.append(" | ".join(line2_parts))

        # C. 第三行: 短評 (Logic Rule)
        # 3.1 Valuation Status
        # mos < -0.2 -> ⚠️嚴重高估
        # mos < -0.1 -> 高估 (User said "高估" but let's use emoji if possible? No emoji in user spec for this one?)
        # User spec: mos < -0.1 -> "高估". Let's add emoji 🔸? Or just text. User example has "⚠️嚴重高估".
        
        val_status = "⚖️合理"
        if mos_dcf < -0.2:
            val_status = "⚠️嚴重高估"
        elif mos_dcf < -0.1:
            val_status = "🔸高估" # Add orange diamond for consistency
        elif mos_dcf > 0.2:
            val_status = "✅深度低估"
        elif mos_dcf > 0.1:
            val_status = "🔹低估" # Blue diamond
            
        # 3.2 Market Mood (Z-Score)
        z_score_match = 0.0
        for tag in card.valuation_check.get('tags', []):
            if "Z=" in tag:
                match = re.search(r"Z=([-\d\.]+)", tag)
                if match:
                    z_score_match = float(match.group(1))
                    break
        
        mood_status = "☁️情緒中性"
        if z_score_match > 1.5:
            mood_status = "🔥市場過熱"
        elif z_score_match < -1.5:
            mood_status = "❄️市場恐慌"
            
        line3 = f"   📊 {val_status} | {mood_status} (Z={z_score_match:.1f})"
        report.append(line3)

        # D. 第四行: AI 分析
        news_analysis = card.advanced_metrics.get('news_analysis')
        if news_analysis:
            summary = news_analysis.get('summary_reason', '暫無分析')
            # Ensure "🗣️ 分析：" prefix and clean format
            clean_summary = summary.replace("1. ", "").replace("2. ", "").replace("3. ", "")
            # Remove any potential "Analysis:" prefixes from AI
            clean_summary = clean_summary.replace("分析：", "").replace("Analysis:", "").strip()
            
            report.append(f"   🗣️ 分析：{clean_summary}")
        else:
            report.append(f"   🗣️ 分析：暫無 AI 觀點")
            
        report.append("") # Spacer

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
