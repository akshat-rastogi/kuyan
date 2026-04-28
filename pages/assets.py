"""
KUYAN - Monthly Net Worth Tracker
Assets Page Module - Assets management page with tabs
Licensed under MIT License - see LICENSE file for details
"""

import streamlit as st
from database import Database
from pages.currencies_settings import currencies_settings
from pages.commodities_settings import commodities_settings
from pages.properties_mortgages_settings import properties_mortgages_settings

def assets(db: Database):
    """
    Render the assets page with tabs for currencies, commodities, and properties.
    
    Args:
        db: Database instance
    """
    st.title("💎 Assets")
    
    # Custom CSS to make tabs larger (similar to dashboard)
    st.markdown("""
        <style>
        div[data-baseweb="tab-list"] {
            gap: 8px !important;
        }
        div[data-baseweb="tab-list"] button {
            height: 50px !important;
            padding: 12px 20px !important;
        }
        div[data-baseweb="tab-list"] button[role="tab"] * {
            font-size: 24px !important;
            font-weight: 600 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Create tabs for the assets pages
    tab1, tab2, tab3 = st.tabs(
        ["💱 Currencies", "🥇 Commodities", "🏘️ Properties"]
    )
    
    # Only render content in active tab to avoid key conflicts
    # Streamlit tabs render all content, so we need to ensure unique keys
    with tab1:
        currencies_settings(db, key_prefix="currencies_")
    
    with tab2:
        commodities_settings(db, key_prefix="commodities_")
    
    with tab3:
        properties_mortgages_settings(db, key_prefix="properties_mortgages_")

# Made with Bob
