import sys
import os
from unittest.mock import MagicMock

# Mock Streamlit
sys.modules['streamlit'] = MagicMock()
import streamlit as st
st.sidebar = MagicMock()
st.columns = MagicMock(return_value=[MagicMock(), MagicMock(), MagicMock(), MagicMock()])
st.expander = MagicMock()

# Add path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import get_market_data, render_sparkline

def test_market_data():
    print("Testing get_market_data...")
    try:
        data = get_market_data()
        print(f"Market Data: {data}")
        if 'z_score' not in data:
            # Manually simulate the fallback logic in app.py
            vix = data.get('vix', 20)
            z = (vix - 18) / 6.0
            print(f"Fallback Z-Score Calc: {z}")
        else:
            print(f"Z-Score found: {data['z_score']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_market_data()
    print("Verification Script Complete")
