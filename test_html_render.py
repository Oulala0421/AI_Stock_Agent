"""
Quick test to diagnose HTML rendering issue
"""
import streamlit as st

st.set_page_config(page_title="HTML Test", layout="wide")

# Test 1: Simple HTML
st.markdown("## Test 1: Simple HTML")
st.markdown("""
<div style="background-color: #e6f4ea; padding: 20px; border-radius: 12px;">
    <h3>Test Card</h3>
    <p>This should render as HTML</p>
</div>
""", unsafe_allow_html=True)

# Test 2: Card-like structure
st.markdown("## Test 2: Card Structure")
symbol = "TEST"
price = 123.45
html = f"""
<div style="background-color: #fce8e6; padding: 20px; border-radius: 12px; margin: 10px 0;">
    <div style="display: flex; justify-content: space-between;">
        <div style="font-size: 1.4rem; font-weight: 700;">{symbol}</div>
        <div style="font-size: 1.1rem;">${price:.2f}</div>
    </div>
</div>
"""
st.markdown(html, unsafe_allow_html=True)

# Test 3: Check what user sees
st.markdown("## Test 3: Raw HTML Display")
st.code(html, language="html")
