"""
AI Stock Agent - War Room Dashboard
Sprint 4: Interactive Command Center & Visualization

Features:
- Real-time MongoDB Connection (Atlas)
- Interactive Sidebar Filters (Search, Status)
- Sparkline Trend Visualization
- Responsive Grid Layout
- Deep Dive Analysis Expanders
"""

import streamlit as st
import os
import matplotlib
matplotlib.use('Agg') # [Fix] For headless server stability
import matplotlib.pyplot as plt
from datetime import datetime
from pymongo import MongoClient, DESCENDING
import pandas as pd
import yfinance as yf
import io

# Page configuration
st.set_page_config(
    page_title="AI Stock Agent - War Room",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium UI
# Custom CSS for Premium UI
CUSTOM_CSS = r"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Remove padding */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
    }
    
    /* Status Badges - Adaptive Text Color */
    .badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 5px;
    }
    
    .badge-pass { background-color: rgba(6, 95, 70, 0.2); color: #10b981; border: 1px solid #10b981; }
    .badge-watch { background-color: rgba(146, 64, 14, 0.2); color: #f59e0b; border: 1px solid #f59e0b; }
    .badge-reject { background-color: rgba(153, 27, 27, 0.2); color: #ef4444; border: 1px solid #ef4444; }
    .badge-unknown { background-color: rgba(107, 114, 128, 0.2); color: #6b7280; border: 1px solid #6b7280; } /* Gray */
    
    .badge-tag { background-color: var(--secondary-background-color); color: var(--text-color); border: 1px solid var(--primary-color); opacity: 0.8; }
    
    /* Metrics Header - Adaptive */
    .kpi-card {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    .kpi-label { font-size: 0.875rem; color: var(--text-color); opacity: 0.8; font-weight: 500; }
    .kpi-value { font-size: 2rem; font-weight: 700; color: var(--text-color); margin: 0.5rem 0; }
    
    /* Stock Card Container - Adaptive */
    .stock-card-container {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 16px;
        padding: 0;
        overflow: hidden;
        transition: transform 0.2s, box-shadow 0.2s;
        margin-bottom: 1rem;
    }
    .stock-card-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    
    .card-header {
        padding: 1.25rem;
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        background-color: rgba(128, 128, 128, 0.05);
        border-bottom: 1px solid rgba(128, 128, 128, 0.1);
    }
    
    .card-body { padding: 1.25rem; }
    
    .price-large { font-size: 1.5rem; font-weight: 700; color: var(--text-color); }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* header {visibility: hidden;}  <-- Removed to keep Sidebar Toggle visible */
    
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


import certifi

@st.cache_resource
def init_mongo_connection():
    uri = os.getenv("MONGODB_URI")
    if not uri and hasattr(st, 'secrets') and "MONGODB_URI" in st.secrets:
        uri = st.secrets["MONGODB_URI"]
    
    if not uri:
        st.error("⚠️ MONGODB_URI not found.")
        return None
    
    try:
        # [Fix] Use certifi for correct CA bundle
        client = MongoClient(uri, 
                             serverSelectionTimeoutMS=5000,
                             tlsCAFile=certifi.where())
        client.admin.command('ping')
        return client
    except Exception as e:
        import ssl
        st.sidebar.error(f"❌ DB Error: {e}")
        st.sidebar.warning(f"🔍 Debug Info: Python SSL: {ssl.OPENSSL_VERSION}")
        return None


@st.cache_data(ttl=60)
def get_market_data():
    """Fetch SPY/VIX (Cached)"""
    try:
        spy = yf.Ticker("SPY").history(period="2d")
        vix = yf.Ticker("^VIX").history(period="1d")
        
        spy_px = spy['Close'].iloc[-1] if not spy.empty else 0
        spy_prev = spy['Close'].iloc[-2] if len(spy) > 1 else spy_px
        spy_chg = ((spy_px - spy_prev) / spy_prev * 100) if spy_prev else 0
        
        vix_px = vix['Close'].iloc[-1] if not vix.empty else 0
        
        return {"spy": spy_px, "spy_chg": spy_chg, "vix": vix_px}
    except:
        return {"spy": 0, "spy_chg": 0, "vix": 0}


@st.cache_data(ttl=300)
def get_data_with_history(limit=50):
    """
    Fetch stocks with 7-day price history array (Cached)
    """
    client = init_mongo_connection()
    if not client: return []
    
    db = client['stock_agent']
    pipeline = [
        {"$sort": {"date": -1, "created_at": -1}}, # Ensure latest date first
        {
            "$group": {
                "_id": "$symbol",
                "latest": {"$first": "$$ROOT"},
                "prices": {"$push": "$price"}
            }
        },
        {
            "$project": {
                "latest": 1,
                "sparkline": {"$slice": ["$prices", 7]}
            }
        },
        {"$replaceRoot": {"newRoot": {"$mergeObjects": ["$latest", {"sparkline": "$sparkline"}]}}},
        {"$sort": {"overall_status": 1}},
    ]
    # Convert cursor to list for caching
    return list(db['daily_snapshots'].aggregate(pipeline))


def render_sparkline(prices, color_code):
    """Generate a mini matplotlib plot"""
    if not prices or len(prices) < 2: return None
    
    # Reverse to chronological order for plotting
    data = prices[::-1]
    
    fig, ax = plt.subplots(figsize=(2, 0.5))
    ax.plot(data, color=color_code, linewidth=2)
    ax.axis('off')
    
    # Save to BytesIO
    buf = io.BytesIO()
    plt.savefig(buf, format='png', transparent=True, bbox_inches='tight', pad_inches=0)
    return buf.getvalue()


def main():
    # --- Sidebar ---
    st.sidebar.title("🦅 AI 戰情室")
    st.sidebar.markdown("---")
    
    # Status
    client = init_mongo_connection()
    status_color = "green" if client else "red"
    status_text = "連線正常" if client else "斷線"
    st.sidebar.caption(f"DB Status: :{status_color}[{status_text}]")
    
    # Filters
    st.sidebar.header("🔍 篩選")
    search_query = st.sidebar.text_input("搜尋代號", placeholder="e.g. NVDA").upper()
    
    all_statuses = ["PASS", "WATCHLIST", "REJECT", "UNKNOWN"]
    selected_statuses = st.sidebar.multiselect(
        "顯示狀態",
        options=all_statuses,
        default=["PASS", "WATCHLIST"] # Default show good ones
    )
    
    if st.sidebar.button("🔄 刷新數據", type="primary"):
        st.cache_resource.clear()
        st.rerun()

    # --- Main Content ---
    
    # 1. Market KPIs
    mkt = get_market_data()
    c1, c2, c3 = st.columns(3)
    
    # 1. Market KPIs
    mkt = get_market_data()
    
    # Calculate Proxy Z-Score from VIX if not available from DB
    # Normal VIX ~15-20. Low < 12 (Greed), High > 25 (Fear). 
    # Approx Z = (Current - 18) / 5 (Rough proxy)
    if 'z_score' not in mkt:
         mkt['z_score'] = (mkt['vix'] - 18) / 6.0
         mkt['z_source'] = "VIX Proxy"
    
    z_score = mkt['z_score']
    
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        color = "green" if mkt['spy_chg'] >= 0 else "red"
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">S&P 500 (SPY)</div>
            <div class="kpi-value">${mkt['spy']:.2f}</div>
            <div style="color: {color}; font-weight: 600;">{mkt['spy_chg']:+.2f}%</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        v_color = "#ef4444" if mkt['vix'] > 20 else "#10b981"
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">VIX (恐慌指數)</div>
            <div class="kpi-value" style="color: {v_color};">{mkt['vix']:.2f}</div>
            <div class="kpi-label">{'⚠️ 風險偏高' if mkt['vix'] > 20 else '✅ 市場穩定'}</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        # Sentiment Gauge
        # Z > 1 Greed (Red/Orange?), Z < -1 Fear (Green? "Buy fear")
        # Warren Buffett: "Fearful when others are greedy"
        # High Z-Score (Greedy) -> Red Warning
        # Low Z-Score (Fear) -> Green Opportunity
        
        sent_color = "#3b82f6" # Neutral Blue
        sent_text = "Neutral"
        if z_score > 1.0:
            sent_color = "#ef4444" # Red (Danger)
            sent_text = "Extreme Greed"
        elif z_score < -1.0:
             sent_color = "#10b981" # Green (Opportunity)
             sent_text = "Extreme Fear"
        
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">市場情緒 (Z-Score)</div>
            <div class="kpi-value" style="color: {sent_color};">{z_score:+.2f}</div>
            <div class="kpi-label">{sent_text}</div>
        </div>
        """, unsafe_allow_html=True)

    # 2. Stock Grid
    raw_stocks = get_data_with_history()
    
    # Apply Filters
    filtered_stocks = []
    for s in raw_stocks:
        if search_query and search_query not in s.get('symbol', ''):
            continue
        
        # [Fix] Changed to inclusive filter logic
        s_status = s.get('overall_status', 'UNKNOWN')
        if s_status not in selected_statuses:
            continue
            
        filtered_stocks.append(s)
    
    # Count
    pass_count = len([s for s in filtered_stocks if s.get('overall_status') == 'PASS'])
    with c4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">篩選後監控</div>
            <div class="kpi-value">{len(filtered_stocks)} <span style="font-size:1rem; color:#6b7280;">檔</span></div>
            <div style="color: #10b981; font-weight: 600;">🟢 {pass_count} 檔強勢</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Private Mode Toggle (Sidebar)
    show_private = st.sidebar.checkbox("🕵️‍♂️ 顯示私人風控警示", value=False)

    st.markdown("### 📋 監控清單")
    
    # Render Grid
    cols = st.columns(3)
    for idx, stock in enumerate(filtered_stocks):
        with cols[idx % 3]:
            # Data extraction
            symbol = stock.get('symbol')
            price = stock.get('price', 0)
            status = stock.get('overall_status', 'UNKNOWN')
            
            # [Fix] Handle nested raw_data from MongoDB
            raw_data = stock.get('raw_data', {})
            
            pred_1w = stock.get('predicted_return_1w')
            if pred_1w is None: pred_1w = raw_data.get('predicted_return_1w')
            
            conf = stock.get('confidence_score')
            if conf is None: conf = raw_data.get('confidence_score')
            
            sparkline = stock.get('sparkline', [])
            
            # Styles
            if status == 'PASS':
                border_color = "#10b981" # Green
                badge_class = "badge-pass"
            elif status == 'WATCHLIST':
                border_color = "#f59e0b" # Amber
                badge_class = "badge-watch"
            elif status == 'REJECT':
                border_color = "#ef4444" # Red
                badge_class = "badge-reject"
            else:
                # [Fix] Default style for UNKNOWN
                border_color = "#9ca3af" # Gray
                badge_class = "badge-unknown" # Correct gray badge 
            
            # Card HTML Header
            st.markdown(f"""
            <div class="stock-card-container" style="border-top: 4px solid {border_color};">
                <div class="card-header">
                    <div>
                        <div style="font-size: 1.25rem; font-weight: 700;">{symbol}</div>
                        <span class="badge {badge_class}">{status}</span>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 0.75rem; color: #6b7280;">現價 (Price)</div>
                        <div class="price-large">${price:.2f}</div>
                    </div>
                </div>
                <div class="card-body">
            """, unsafe_allow_html=True)

            # === Private Risk Alerts ===
            if show_private:
                # Private notes are often lists of strings
                p_notes = stock.get('private_notes', []) 
                if not p_notes and 'private_notes' in raw_data:
                    p_notes = raw_data['private_notes']
                
                if p_notes:
                    for note in p_notes:
                        st.error(f"🕵️‍♂️ {note}", icon="⚠️")
            
            # Prediction Row
            c_a, c_b = st.columns(2)
            with c_a:
                if pred_1w is not None:
                    p_color = "green" if pred_1w > 0 else "red"
                    st.metric("一週預測", f"{pred_1w:+.1f}%", help="Monte Carlo Simulation")
                else:
                    st.write("N/A")
            with c_b:
                if conf:
                    st.metric("信心分數", f"{conf:.0%}")
                    
            # Sparkline
            if len(sparkline) > 1:
                st.caption("14日走勢 (2週)")
                st.line_chart(pd.DataFrame(sparkline[::-1], columns=['Price']), height=50, use_container_width=True)

            # [Feature] Tabs for detailed view
            tab_ai, tab_val, tab_fund, tab_tech, tab_news = st.expander(f"💡 AI 分析與詳細數據", expanded=False).tabs(["🧠 AI", "💎 估值(DCF)", "📊 基本面", "📉 技術", "📰 新聞"])
            
            # Pre-fetch news summary
            news_summary = stock.get('news_summary_str')

            with tab_ai:
                full_report = stock.get('report', '尚無分析報告')
                if "📰 MARKET INTELLIGENCE:" in full_report:
                    clean_report = full_report.split("📰 MARKET INTELLIGENCE:")[0].strip()
                else:
                    clean_report = full_report
                
                st.markdown(clean_report)
            
            with tab_val:
                # === Deep Value Tab ===
                vc = raw_data.get('valuation_check', {})
                dcf_data = vc.get('dcf', {})
                
                intrinsic = dcf_data.get('intrinsic_value')
                mos = vc.get('margin_of_safety_dcf')
                
                st.caption("Sentiment-Adjusted DCF Model")
                
                if intrinsic:
                    col_v1, col_v2 = st.columns(2)
                    with col_v1:
                        st.metric("AI 內在價值", f"${intrinsic:.2f}")
                        st.metric("折現率 (Adj)", f"{dcf_data.get('discount_rate', 0):.1%}")
                    
                    with col_v2:
                        mos_color = "normal"
                        if mos and mos > 0.15: mos_color = "off" # Streamlit doesn't really have green metric color easily without delta
                        st.metric("安全邊際 (MoS)", f"{mos:+.1%}", delta_color="normal" if (mos and mos > 0) else "inverse")
                        st.metric("情緒罰分", f"{dcf_data.get('sentiment_penalty', 0):.1%}")

                    # Visual Comparison
                    # Simple Progress bar to show Price relative to Intrinsic
                    # 0% .... Price .... Intrinsic (if undervalued)
                    st.write("---")
                    st.caption("價格 vs 價值")
                    
                    if mos > 0:
                        st.success(f"低估 {mos:.1%}")
                        st.progress(min(1.0, price / intrinsic))
                    else:
                        st.warning(f"溢價 {-mos:.1%}")
                        # Inverted progress is hard, just show full
                        st.progress(1.0)
                        
                else:
                    st.info("尚無 DCF 數據 (可能是負現金流或資料不足)")
                    
                st.markdown("---")
                fair_val = vc.get('fair_value')
                st.markdown(f"**分析師目標均價**: ${fair_val:.2f}" if fair_val is not None else "**分析師目標均價**: N/A")
                peg = vc.get('peg_ratio')
                st.markdown(f"**PEG Ratio**: {peg:.2f}" if peg is not None else "**PEG Ratio**: N/A")
            
            with tab_fund:
                # Extract Fundamental Data
                solvency = raw_data.get('solvency_check', {})
                quality = raw_data.get('quality_check', {})
                
                f1, f2 = st.columns(2)
                with f1:
                    st.markdown("**💰 償債能力**")
                    debt_eq = solvency.get('debt_to_equity')
                    d_color = "red" if debt_eq and debt_eq > 200 else "green"
                    st.markdown(f"- 負債權益比: :{d_color}[{debt_eq}%]" if debt_eq else "- 負債權益比: N/A")
                    st.markdown(f"- 流動比率: {solvency.get('current_ratio', 'N/A')}")
                
                with f2:
                    st.markdown("**💎 獲利品質**")
                    roe = quality.get('roe')
                    r_color = "green" if roe and roe > 0.15 else "orange"
                    st.markdown(f"- ROE: :{r_color}[{roe:.1%}]" if roe else "- ROE: N/A")
                    st.markdown(f"- 毛利率: {quality.get('gross_margin', 'N/A')}")
                    
            with tab_tech:
                # Extract Technical Data
                technical = raw_data.get('technical_setup', {})
                volatility = raw_data.get('volatility', {})  
                
                t1, t2 = st.columns(2)
                with t1:
                    st.markdown("**📈 趨勢與動能**")
                    rsi = technical.get('rsi')
                    rsi_val = f"{rsi:.1f}" if rsi else "N/A"
                    r_col = "red" if rsi and rsi > 70 else "green" if rsi and rsi < 30 else "gray"
                    st.markdown(f"- RSI (14): :{r_col}[{rsi_val}]")
                    st.markdown(f"- 趨勢狀態: {technical.get('trend_status', 'N/A')}")
                
                with t2:
                    st.markdown("**🌊 波動率**")
                    # Assuming ATR or Risk Range logic
                    mc_min = stock.get('monte_carlo_min')
                    mc_max = stock.get('monte_carlo_max')
                    if mc_min:
                        st.markdown(f"- 1W Range: ${mc_min:.1f} - ${mc_max:.1f}")
                    
                # Tags
                st.markdown("---")
                tags = raw_data.get('solvency_check', {}).get('tags', []) + \
                       raw_data.get('quality_check', {}).get('tags', []) + \
                       raw_data.get('valuation_check', {}).get('tags', []) + \
                       raw_data.get('technical_setup', {}).get('tags', [])
                
                if tags:
                    st.markdown("**🏷️ 標籤:** " + " ".join([f"`{t}`" for t in tags]))
                    
            with tab_news:
                if news_summary:
                    st.info(f"📰 **最新新聞摘要**: {news_summary}")
                else:
                    st.write("暫無新聞分析")
                
                # Check for News Agent Analysis
                news_analysis = raw_data.get('advanced_metrics', {}).get('news_analysis', {})
                if news_analysis:
                    score = news_analysis.get('score') # Might vary by version
                    if not score: score = news_analysis.get('sentiment_score')
                    st.metric("新聞情緒分數", f"{score}/100" if score else "N/A")

            st.markdown("</div></div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
