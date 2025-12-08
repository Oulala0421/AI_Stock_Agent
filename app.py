"""
AI Stock Agent - War Room Dashboard

Sprint 3: Transform cold JSON data into intuitive investment insights

Architecture:
- MongoDB: Historical data storage
- Streamlit: Real-time dashboard
- Caching: @st.cache_resource for connection pooling
- UI: Custom CSS + Grid Layout implementation for high-fidelity cards

Author: Senior Frontend Engineer (Streamlit Specialist)
Date: 2025-12-08
"""

import streamlit as st
import os
from datetime import datetime
from pymongo import MongoClient, DESCENDING
import pandas as pd
import yfinance as yf

# Page configuration
st.set_page_config(
    page_title="AI Stock Agent - War Room",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Mobile-First UI/UX
st.markdown("""
<style>
    /* ========== Mobile-First: Remove Streamlit Padding ========== */
    .block-container {
        padding-top: 1rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 100% !important;
    }
    
    /* ========== Global Fonts ========== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* ========== Responsive Column Behavior ========== */
    /* Force stacking on mobile */
    @media (max-width: 768px) {
        div[data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }
        
        /* Enlarge fonts on mobile */
        h1 { font-size: 1.8rem !important; }
        h2 { font-size: 1.5rem !important; }
        h3 { font-size: 1.3rem !important; }
        
        /* Card containers need more breathing room */
        .stMarkdown > div {
            margin-bottom: 1rem !important;
        }
    }
    
    /* Desktop: maintain 3-column layout */
    @media (min-width: 769px) {
        div[data-testid="column"] {
            padding: 0 0.5rem !important;
        }
    }

    /* ========== Metric Containers (Top KPIs) ========== */
    .metric-container {
        background-color: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #eee;
        min-height: 120px;
    }
    
    .metric-container .label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        opacity: 0.7;
        font-weight: 600;
    }
    
    .metric-container .value {
        font-size: 2rem;
        font-weight: 700;
        margin: 0.5rem 0;
    }
    
    /* Mobile: Larger metric values */
    @media (max-width: 768px) {
        .metric-container .value {
            font-size: 2.5rem !important;
        }
    }
    
    /* ========== Hide Streamlit Branding ========== */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* ========== Progress Bar Styling ========== */
    .stProgress > div > div > div {
        background-color: #34a853;
        height: 8px;
        border-radius: 4px;
    }
    
    /* ========== Expander Tweaks ========== */
    .stExpander {
        border-radius: 0 0 12px 12px !important;
        border: 1px solid #eee !important;
        border-top: none !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-top: -8px !important;
    }
    
    div[data-testid="stExpanderDetails"] {
        background-color: #fafafa;
        border-radius: 0 0 12px 12px;
        padding: 1rem;
    }
    
    /* ========== Touch-Friendly: Increase tap targets ========== */
    @media (max-width: 768px) {
        button {
            min-height: 44px !important;
            font-size: 1rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def init_mongo_connection():
    """
    Initialize MongoDB connection with caching
    """
    uri = os.getenv("MONGODB_URI")
    
    if not uri and hasattr(st, 'secrets') and "MONGODB_URI" in st.secrets:
        uri = st.secrets["MONGODB_URI"]
    
    if not uri:
        st.error("⚠️ MONGODB_URI not found in environment or secrets")
        return None
    
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        # Test connection
        client.admin.command('ping')
        return client
    except Exception as e:
        st.error(f"❌ MongoDB connection failed: {e}")
        return None


def get_latest_stocks(limit=50):
    """
    Fetch latest stock analysis from MongoDB
    """
    client = init_mongo_connection()
    if not client:
        return []
    
    db = client['stock_agent']
    collection = db['daily_snapshots']
    
    # Get latest snapshot for each stock
    pipeline = [
        {"$sort": {"date": -1, "created_at": -1}},
        {"$group": {
            "_id": "$symbol",
            "latest": {"$first": "$$ROOT"}
        }},
        {"$replaceRoot": {"newRoot": "$latest"}},
        {"$sort": {"created_at": -1}},
        {"$limit": limit}
    ]
    
    stocks = list(collection.aggregate(pipeline))
    return stocks


def get_market_overview():
    """
    Get SPY and VIX data for market overview using yfinance
    """
    try:
        spy = yf.Ticker("SPY")
        vix = yf.Ticker("^VIX")
        
        spy_info = spy.history(period="2d")
        vix_info = vix.history(period="1d")
        
        if len(spy_info) >= 2:
            current_price = spy_info['Close'].iloc[-1]
            prev_price = spy_info['Close'].iloc[-2]
            change_pct = ((current_price - prev_price) / prev_price) * 100
        else:
            current_price = spy_info['Close'].iloc[-1] if len(spy_info) > 0 else 0
            change_pct = 0
        
        vix_current = vix_info['Close'].iloc[-1] if len(vix_info) > 0 else 0
        
        return {
            "spy_price": float(current_price),
            "spy_change": float(change_pct),
            "vix": float(vix_current)
        }
    except Exception as e:
        # Fallback to placeholder if API fails
        return {
            "spy_price": 0.0,
            "spy_change": 0.0,
            "vix": 0.0
        }


def render_sidebar():
    """
    Render sidebar with system status
    """
    st.sidebar.title("📊 AI Stock Agent")
    st.sidebar.markdown("### War Room")
    
    # System status
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔧 系統狀態")
    
    client = init_mongo_connection()
    if client:
        st.sidebar.success("✅ Database Connected")
        
        # Get stock count
        db = client['stock_agent']
        count = db['daily_snapshots'].count_documents({})
        st.sidebar.metric("📈 總記錄數", count)
        
        # Last update time
        latest = db['daily_snapshots'].find_one(sort=[("created_at", DESCENDING)])
        if latest and 'created_at' in latest:
            last_time = latest.get('created_at')
            if isinstance(last_time, datetime):
                time_str = last_time.strftime('%m/%d %H:%M')
                st.sidebar.info(f"🕒 最新: {time_str}")
    else:
        st.sidebar.error("❌ Database Disconnected")
    
    # Manual refresh button
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 重新整理", use_container_width=True):
        st.cache_resource.clear()
        st.rerun()


def render_market_kpis():
    """
    Render top-level market KPIs (SPY, VIX)
    """
    st.markdown("## 📈 市場概況")
    
    market_data = get_market_overview()
    stocks = get_latest_stocks()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-container">
            <div class="label">SPY (S&P 500)</div>
            <div class="value" style="font-size: 2rem;">${market_data['spy_price']:.2f}</div>
            <div style="color: {'red' if market_data['spy_change'] < 0 else 'green'};">
                {market_data['spy_change']:+.2f}%
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        vix = market_data['vix']
        vix_color = "#c5221f" if vix > 20 else "#137333"
        vix_text = "⚠️ 高波動" if vix > 20 else "✅ 穩定"
        
        st.markdown(f"""
        <div class="metric-container">
            <div class="label">VIX (恐慌指數)</div>
            <div class="value" style="font-size: 2rem; color: {vix_color};">{vix:.2f}</div>
            <div>{vix_text}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        bullish_count = len([s for s in stocks if s.get('status') in ['PASS', 'WATCHLIST']])
        st.markdown(f"""
        <div class="metric-container">
            <div class="label">監控股票</div>
            <div class="value" style="font-size: 2rem;">{len(stocks)}</div>
            <div>🟢 {bullish_count} 持有中</div>
        </div>
        """, unsafe_allow_html=True)


def generate_card_html(stock):
    """
    Generate the HTML for a single stock card using Visual Specs
    """
    raw_data = stock.get('raw_data', {})
    symbol = stock.get('symbol', 'N/A')
    price = stock.get('price', 0.0)
    status = stock.get('status', 'UNKNOWN')
    
    # Prediction data
    pred_1w = raw_data.get('predicted_return_1w')
    confidence = raw_data.get('confidence_score')
    summary = raw_data.get('summary_reason', '無分析數據')
    
    # Determine Style Class
    if status == 'PASS':
        card_class = "card-pass"
        status_label = "做多 (PASS)"
        progress_color = "#34a853"
    elif status == 'REJECT':
        card_class = "card-reject"
        status_label = "避開 (REJECT)"
        progress_color = "#ea4335"
    else:  # WATCHLIST
        card_class = "card-watchlist"
        status_label = "觀察 (WATCH)"
        progress_color = "#fbbc04"
    
    # Format Metrics with None handling
    if pred_1w is not None:
        prediction_text = f"{pred_1w:+.1f}% Upside" if pred_1w > 0 else f"{pred_1w:+.1f}% Downside"
        prediction_color = "green" if pred_1w > 0 else "red"
    else:
        prediction_text = "N/A"
        prediction_color = "gray"
    
    # Handle confidence None
    confidence_pct = f"{confidence:.0%}" if confidence is not None else "N/A"
    confidence_width = confidence * 100 if confidence is not None else 0
        
    ai_rating = "Bullish" if status == 'PASS' else ("Bearish" if status == 'REJECT' else "Neutral")
    
    # Generate HTML
    html = f"""
    <div class="stock-card {card_class}">
        <div class="card-header">
            <div>
                <div class="stock-symbol">{symbol} <span style="font-size: 0.8rem; opacity: 0.7; font-weight: 400;">{status_label}</span></div>
            </div>
            <div class="stock-price">${price:.2f}</div>
        </div>
        
        <div class="card-body">
            <div class="metric-box">
                <span class="label">AI 評價</span>
                <span class="value">{ai_rating}</span>
                <div class="progress-container">
                    <div class="progress-bar" style="width: {confidence_width}%; background-color: {progress_color};"></div>
                </div>
                <div class="confidence-text">信心分數: {confidence_pct}</div>
            </div>
            
            <div class="metric-box" style="align-items: flex-end;">
                <span class="label">一周目標</span>
                <span class="value" style="color: {prediction_color};">{prediction_text}</span>
            </div>
        </div>
        
        <div class="card-footer">
            💡 {summary[:80] if len(summary) <= 80 else summary[:77] + '...'}
        </div>
    </div>
    """
    return html


def render_stock_card_native(stock):
    """
    Render stock card using Streamlit native components + CSS
    """
    raw_data = stock.get('raw_data', {})
    symbol = stock.get('symbol', 'N/A')
    price = stock.get('price', 0.0)
    status = stock.get('status', 'UNKNOWN')
    
    # Prediction data
    pred_1w = raw_data.get('predicted_return_1w')
    confidence = raw_data.get('confidence_score')
    summary = raw_data.get('summary_reason', '無分析數據')
    
    # Determine色彩
    if status == 'PASS':
        bg_color = "#e6f4ea"
        text_color = "#137333"
        status_emoji = "🟢"
        status_label = "做多"
    elif status == 'REJECT':
        bg_color = "#fce8e6"
        text_color = "#c5221f"
        status_emoji = "🔴"
        status_label = "避開"
    else:
        bg_color = "#fef7e0"
        text_color = "#b06000"
        status_emoji = "🟡"
        status_label = "觀察"
    
    # Container with background
    container_style = f"""
        background-color: {bg_color};
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(0,0,0,0.1);
        margin-bottom: 8px;
    """
    
    st.markdown(f'<div style="{container_style}">', unsafe_allow_html=True)
    
    # Header
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"<h3 style='color: {text_color}; margin: 0;'>{status_emoji} {symbol}</h3>", unsafe_allow_html=True)
        st.markdown(f"<small style='color: {text_color}; opacity: 0.7;'>{status_label}</small>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div style='text-align: right; font-size: 1.2rem; font-weight: 600; color: {text_color};'>${price:.2f}</div>", unsafe_allow_html=True)
    
    # AI Rating
    ai_rating = "Bullish" if status == 'PASS' else ("Bearish" if status == 'REJECT' else "Neutral")
    st.markdown(f"<div style='margin-top: 15px; color: {text_color}; font-weight: 600;'>AI 評價: {ai_rating}</div>", unsafe_allow_html=True)
    
    # Confidence
    if confidence is not None:
        st.progress(confidence, text=f"信心分數: {confidence:.0%}")
    
    # Prediction
    if pred_1w is not None:
        pred_text = f"+{pred_1w:.1f}%" if pred_1w > 0 else f"{pred_1w:.1f}%"
        pred_color = "green" if pred_1w > 0 else "red"
        st.markdown(f"<div style='color: {pred_color}; font-weight: 600;'>一周目標: {pred_text}</div>", unsafe_allow_html=True)
    
    # Summary
    st.markdown(f"<div style='margin-top: 10px; padding: 10px; background-color: rgba(255,255,255,0.4); border-radius: 6px; color: {text_color};'>💡 {summary[:80] if len(summary) <= 80 else summary[:77] + '...'}</div>", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_stock_grid(stocks):
    """
    Render stocks in a responsive grid using st.columns
    """
    if not stocks:
        return
        
    # Chunk stocks into groups of 3 for the grid
    cols_per_row = 3
    for i in range(0, len(stocks), cols_per_row):
        cols = st.columns(cols_per_row)
        batch = stocks[i:i+cols_per_row]
        
        for idx, stock in enumerate(batch):
            with cols[idx]:
                # Render native Streamlit card
                render_stock_card_native(stock)
                
                # Render Details Expander (Sits visually inside/below card due to CSS)
                raw_data = stock.get('raw_data', {})
                with st.expander("📊 詳細數據", expanded=False):
                    q = raw_data.get('quality_check', {})
                    v = raw_data.get('valuation_check', {})
                    
                    st.markdown("**Core Metrics**")
                    if q: st.markdown(f"- ROE: `{q.get('roe', 'N/A')}`")
                    if v: st.markdown(f"- PEG: `{v.get('peg_ratio', 'N/A')}`")
                    
                    red_flags = raw_data.get('red_flags', [])
                    if red_flags:
                        st.markdown("**⚠️ Risks**")
                        for flag in red_flags:
                            st.markdown(f"- {flag}")


def render_stock_lists():
    """
    Render categorized stock lists
    """
    stocks = get_latest_stocks()
    
    if not stocks:
        st.warning("📭 目前無股票資料")
        st.info("💡 執行 `python main.py` 來生成分析資料")
        return
    
    # Categorize stocks
    bullish_stocks = [s for s in stocks if s.get('status') in ['PASS', 'WATCHLIST']]
    bearish_stocks = [s for s in stocks if s.get('status') == 'REJECT']
    
    # Bullish section
    if bullish_stocks:
        st.markdown("### 🟢 持股 / 建議續抱")
        render_stock_grid(bullish_stocks)
        st.markdown("---")
    
    # Bearish section
    if bearish_stocks:
        st.markdown("### 🔴 建議避開 / 賣出")
        render_stock_grid(bearish_stocks)
        st.markdown("---")


def main():
    """
    Main dashboard entry point
    """
    render_sidebar()
    
    st.title("📊 AI Stock Agent - 戰情室")
    render_market_kpis()
    
    st.markdown("---")
    render_stock_lists()


if __name__ == "__main__":
    main()
