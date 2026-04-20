"""
KUYAN - Monthly Net Worth Tracker
Sidebar Module - Handles sidebar navigation and related functionality
Copyright (c) 2025 mycloudcondo inc.
Licensed under MIT License - see LICENSE file for details
"""

import streamlit as st
import os
from version import __version__
from database import Database


def sidebar(is_sandbox):
    """
    Render the sidebar with navigation buttons and logo.
    
    Args:
        is_sandbox (bool): Whether the app is running in sandbox mode
        
    Returns:
        str: The selected page/navigation state
    """
    with st.sidebar:
        # Logo - centered, 55% of previous size (27.5% of sidebar width)
        col1, col2, col3 = st.columns([0.3625, 0.275, 0.3625])
        with col2:
            st.image("assets/logo.png", width="stretch")

        # Centered title and captions
        st.markdown("<h1 style='text-align: center;'>KUYAN</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 0.875rem; color: gray;'>Monthly Net Worth Tracker</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; font-size: 0.875rem; color: gray;'>v{__version__}</p><br/><br/>", unsafe_allow_html=True)


        # Initialize navigation in session state
        if "settings_nav" not in st.session_state:
            st.session_state.settings_nav = None

        # Navigation buttons - Dashboard, Accounts, History, and Exchange Rates
        if st.button("📊 Dashboard", width="stretch"):
            st.session_state.settings_nav = None
            st.rerun()
        
        if st.button("📜 History", width="stretch"):
            st.session_state.settings_nav = "History"
            st.rerun()

        if st.button("💰 Update Accounts", width="stretch"):
            st.session_state.settings_nav = "Accounts"
            st.rerun()

        if st.button("💹 Exchange Rates", width="stretch"):
            st.session_state.settings_nav = "Exchange Rates"
            st.rerun()

        st.divider()

        # Settings section - moved to bottom
        if st.button("⚙️ Settings", width="stretch"):
            st.session_state.settings_nav = "Settings"
            st.rerun()

        page = st.session_state.settings_nav

        # Sandbox reset button
        if is_sandbox:
            st.divider()
            if st.button("Reset Sandbox", type="secondary", width="stretch"):
                show_reset_confirmation()

        return page


@st.dialog("Reset Sandbox Confirmation")
def show_reset_confirmation():
    """Show confirmation dialog for sandbox reset"""
    st.warning("⚠️ This will reset all sandbox data to the original sample data.")
    st.write("All current snapshots, owners, and accounts in the sandbox will be replaced.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Yes, Reset", width="stretch", type="primary"):
            reset_sandbox()
            st.session_state.sandbox_reset = True
            st.rerun()
    with col2:
        if st.button("❌ Cancel", width="stretch"):
            st.rerun()


def reset_sandbox():
    """Reset the sandbox database to initial sample data"""
    # Clear cache to force database reload
    st.cache_resource.clear()

    # Recreate sandbox database with fresh sample data
    db_path = "kuyan-sandbox.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    # Create new database and seed
    fresh_db = Database(db_path=db_path)
    fresh_db.seed_sample_data()

