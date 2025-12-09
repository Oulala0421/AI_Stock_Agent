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
        color: #1f2937;
    }
    
    /* Remove padding */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
    }
    
    /* Status Badges */
    .badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 5px;
    }
    
    .badge-pass { background-color: #d1fae5; color: #065f46; }
    .badge-watch { background-color: #fef3c7; color: #92400e; }
    .badge-reject { background-color: #fee2e2; color: #991b1b; }
    
    .badge-tag { background-color: #f3f4f6; color: #374151; border: 1px solid #e5e7eb; }
    
    /* Metrics Header */
    .kpi-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    .kpi-label { font-size: 0.875rem; color: #6b7280; font-weight: 500; }
    .kpi-value { font-size: 2rem; font-weight: 700; color: #111827; margin: 0.5rem 0; }
    
    /* Stock Card Container */
    .stock-card-container {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 0;
        overflow: hidden;
        transition: transform 0.2s, box-shadow 0.2s;
        margin-bottom: 1rem;
    }
    .stock-card-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    }
    
    .card-header {
        padding: 1.25rem;
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        background: #f9fafb;
        border-bottom: 1px solid #f3f4f6;
    }
    
    .card-body { padding: 1.25rem; }
    
    .price-large { font-size: 1.5rem; font-weight: 700; color: #111827; }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
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
        # Use certifi for SSL context to fix handshake errors
        client = MongoClient(uri, 
                             serverSelectionTimeoutMS=5000,
                             tlsCAFile=certifi.where())
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
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
    
    status_filter = st.sidebar.multiselect(
        "不顯示狀態",
        options=["PASS", "WATCHLIST", "REJECT"],
        default=["REJECT"] # Default hide rejects to keep it clean
    )
    
    if st.sidebar.button("🔄 刷新數據", type="primary"):
        st.cache_resource.clear()
        st.rerun()

    # --- Main Content ---
    
    # 1. Market KPIs
    mkt = get_market_data()
    c1, c2, c3 = st.columns(3)
    
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

    # 2. Stock Grid
    raw_stocks = get_data_with_history()
    
    # Apply Filters
    filtered_stocks = []
    for s in raw_stocks:
        if search_query and search_query not in s.get('symbol', ''):
            continue
        if s.get('overall_status') in status_filter:
            continue
        filtered_stocks.append(s)
    
    # Count
    pass_count = len([s for s in filtered_stocks if s.get('overall_status') == 'PASS'])
    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">篩選後監控</div>
            <div class="kpi-value">{len(filtered_stocks)} <span style="font-size:1rem; color:#6b7280;">檔</span></div>
            <div style="color: #10b981; font-weight: 600;">🟢 {pass_count} 檔強勢</div>
        </div>
        """, unsafe_allow_html=True)

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
                chart_color = "green"
            elif status == 'WATCHLIST':
                border_color = "#f59e0b" # Amber
                badge_class = "badge-watch"
                chart_color = "orange"
            else:
                border_color = "#ef4444" # Red
                badge_class = "badge-reject"
                chart_color = "red"
            
            # Card HTML Header
            st.markdown(f"""
            <div class="stock-card-container" style="border-top: 4px solid {border_color};">
                <div class="card-header">
                    <div>
                        <div style="font-size: 1.25rem; font-weight: 700;">{symbol}</div>
                        <span class="badge {badge_class}">{status}</span>
                    </div>
                    <div class="price-large">${price:.2f}</div>
                </div>
                <div class="card-body">
            """, unsafe_allow_html=True)
            
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
                st.caption("7日走勢")
                st.line_chart(pd.DataFrame(sparkline[::-1], columns=['Price']), height=50, use_container_width=True)

            # Details & News
            with st.expander("💡 AI 分析與總結"):
                news_summary = stock.get('news_summary_str')
                if news_summary:
                    st.info(news_summary)
                else:
                    st.write("暫無新聞分析")
                
                # Tech Tags
                st.markdown("---")
                # Try to get tags from raw dictionary if available, relying on flat structure??
                # Wait, database manager flattens it? 
                # StockHealthCard stores checks as DICTS in MongoDB.
                # E.g. solvency_check: {tags: [...]}
                
                solvency = stock.get('solvency_check', {})
                quality = stock.get('quality_check', {})
                val = stock.get('valuation_check', {})
                
                all_tags = (solvency.get('tags', []) + 
                           quality.get('tags', []) + 
                           val.get('tags', []))
                
                if all_tags:
                    st.markdown(" ".join([f"`{t}`" for t in all_tags]))

            st.markdown("</div></div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
