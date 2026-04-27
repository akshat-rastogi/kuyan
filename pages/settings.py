"""
KUYAN - Monthly Net Worth Tracker
Settings Page Module - Main settings page with tabs
Copyright (c) 2025 mycloudcondo inc.
Licensed under MIT License - see LICENSE file for details
"""

import streamlit as st
from database import Database
from pages.accounts_settings import accounts_settings
from pages.backup_restore_settings import backup_restore_settings
from pages.currencies_settings import currencies_settings
from pages.commodities_settings import commodities_settings
from pages.mortgage_settings import mortgage_settings
from pages.owners_settings import owners_settings

def settings(db: Database):
    """
    Render the main settings page with tabs for different settings sections.
    
    Args:
        db: Database instance
        accounts_settings: Function to render accounts page
        commodities_settings: Function to render commodities page
        currencies_settings: Function to render currencies page
        owners_settings: Function to render owners page
        mortgage_settings: Function to render mortgage settings page
    """
    st.title("⚙️ Settings")
    
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
    
    # Create tabs for the settings pages
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["🏦 Accounts", "🥇 Commodities", "💱 Currencies", "👥 Owners", "🏠 Mortgage", "☁️ Backup & Restore"]
    )
    
    # Only render content in active tab to avoid key conflicts
    # Streamlit tabs render all content, so we need to ensure unique keys
    with tab1:
        accounts_settings(db, key_prefix="accounts_")
    
    with tab2:
        commodities_settings(db, key_prefix="commodities_")
    
    with tab3:
        currencies_settings(db, key_prefix="currencies_")
    
    with tab4:
        owners_settings(db, key_prefix="owners_")
    
    with tab5:
        mortgage_settings(db, key_prefix="mortgage_settings_")

    with tab6:
        backup_restore_settings(db, key_prefix="backup_restore_")
