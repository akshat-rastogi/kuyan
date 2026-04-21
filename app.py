"""
KUYAN - Monthly Net Worth Tracker
Copyright (c) 2025 mycloudcondo inc.
Licensed under MIT License - see LICENSE file for details
"""

import streamlit as st
from database import Database
from pages.sidebar import sidebar
from version import __version__
from pages.history import history
from pages.dashboard import dashboard
from pages.update_balances import update_balances
from pages.exchange_rates import exchange_rates
from pages.settings import settings
from helper import (
    get_default_currency,
    inject_custom_css,
)
from components import (
    render_sandbox_banner,
    set_globals
)

# Detect sandbox mode from query parameters
query_params = st.query_params
is_sandbox = query_params.get("mode") == "sandbox"

# Page config
st.set_page_config(
    page_title="KUYAN - Net Worth Tracker" + (" [SANDBOX]" if is_sandbox else ""),
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items=None
)

# Hide default Streamlit navigation
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)


# Initialize database (sandbox or production)
@st.cache_resource
def init_db(sandbox_mode=False, _cache_version=1):
    db_path = "kuyan-sandbox.db" if sandbox_mode else "kuyan.db"

    db = Database(db_path=db_path)

    # Create sandbox database with sample data if it doesn't exist
    if sandbox_mode:
        # Check if database is empty (no accounts)
        accounts = db.get_accounts()
        if len(accounts) == 0:
            db.seed_sample_data()

    return db


# Clear cache on rerun if requested
if st.session_state.get('clear_cache', False):
    init_db.clear()
    st.session_state.clear_cache = False

db = init_db(sandbox_mode=is_sandbox, _cache_version=4)

# Set global variables for components module
set_globals(db, is_sandbox)


# ===== CONSTANTS =====
MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

# ===== EXPORT DASHBOARD WIDGET =====

# Main app
    
    # cols[0] is the spacer column (empty)


def main():
    # Inject custom CSS for button styling
    inject_custom_css()

    # Render sandbox banner if in sandbox mode
    render_sandbox_banner()

    # Show toast if sandbox was just reset
    if st.session_state.get('sandbox_reset', False):
        st.toast("Sandbox reset successfully!", icon="🔄")
        st.session_state.sandbox_reset = False

    # Initialize session state
    if "base_currency" not in st.session_state:
        # Set default to first enabled currency
        default_currency = get_default_currency(db)
        st.session_state.base_currency = default_currency

    # Render sidebar and get selected page
    selected_page = sidebar(is_sandbox)

    # Route to the appropriate page based on navigation
    if selected_page == "Settings":
        settings(db=db)
    elif selected_page == "Exchange Rates":
        exchange_rates(db=db)
    elif selected_page == "Accounts":
        update_balances(db=db)
    elif selected_page == "History":
        st.title("📜 History")
        history(db=db)
    else:
        # Default: Dashboard Overview
        st.title("📊 Dashboard")
        dashboard(db=db)


if __name__ == "__main__":
    main()
