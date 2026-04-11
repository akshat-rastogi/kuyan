"""
KUYAN - Monthly Net Worth Tracker
Copyright (c) 2025 mycloudcondo inc.
Licensed under MIT License - see LICENSE file for details
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
from io import StringIO
from dateutil.relativedelta import relativedelta
from database import Database
from currency import CurrencyConverter
from version import __version__
import json
import os


# Detect sandbox mode from query parameters
query_params = st.query_params
is_sandbox = query_params.get("mode") == "sandbox"

# Page config
st.set_page_config(
    page_title="KUYAN - Net Worth Tracker" + (" [SANDBOX]" if is_sandbox else ""),
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)


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


db = init_db(sandbox_mode=is_sandbox, _cache_version=4)


# ===== CONSTANTS =====
MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


# ===== HELPER FUNCTIONS =====

def get_default_currency():
    """Get the default base currency (first enabled currency)"""
    codes = db.get_currency_codes()
    return codes[0] if codes else "CAD"


def get_rates_from_snapshot(snapshot):
    """Extract exchange rates from a snapshot, returning empty dict if not present"""
    return json.loads(snapshot["exchange_rates"]) if snapshot.get("exchange_rates") else {}


def show_success_toast(item_type):
    """
    Display success toast if an item was just added

    Args:
        item_type: Type of item (e.g., 'account', 'currency', 'owner')
    """
    state_key = f'{item_type}_added'
    name_key = f'added_{item_type}_name'
    code_key = f'added_{item_type}_code'

    if st.session_state.get(state_key, False):
        # Try to get name first, fall back to code
        item_name = st.session_state.get(name_key, st.session_state.get(code_key, ''))
        icons = {'account': '🏦', 'currency': '💱', 'owner': '👥'}
        icon = icons.get(item_type, '✅')
        st.toast(f"{item_type.capitalize()} '{item_name}' added successfully!", icon=icon)
        st.session_state[state_key] = False


def apply_chart_theme(fig, colors, xaxis_title=None, yaxis_title=None, show_legend=False, legend_title=""):
    """
    Apply consistent KUYAN theme styling to a Plotly chart

    Args:
        fig: Plotly figure object
        colors: Theme colors dictionary from get_theme_colors()
        xaxis_title: Optional x-axis title
        yaxis_title: Optional y-axis title
        show_legend: Whether to show legend
        legend_title: Title for legend (if show_legend=True)
    """
    layout_config = {
        'xaxis': dict(
            showline=True,
            linewidth=2,
            linecolor=colors['plot_axis'],
            mirror=False,
            showgrid=True,
            gridwidth=1,
            gridcolor=colors['plot_grid'],
            title_font=dict(size=14, family='Arial, sans-serif', color=colors['plot_text'], weight='bold'),
            showspikes=True,
            spikecolor=colors['plot_axis'],
            spikethickness=1
        ),
        'yaxis': dict(
            showline=True,
            linewidth=2,
            linecolor=colors['plot_axis'],
            mirror=False,
            showgrid=True,
            gridwidth=1,
            gridcolor=colors['plot_grid'],
            title_font=dict(size=14, family='Arial, sans-serif', color=colors['plot_text'], weight='bold'),
            showspikes=True,
            spikecolor=colors['plot_axis'],
            spikethickness=1
        ),
        'plot_bgcolor': colors['plot_bg'],
        'paper_bgcolor': colors['plot_bg'],
        'font': dict(color=colors['plot_text']),
        'title_font': dict(color=colors['text_primary']),
        'hoverlabel': dict(
            bgcolor=colors['surface'],
            font_size=13,
            font_family="Arial, sans-serif",
            font_color=colors['text_primary']
        ),
        'hovermode': 'x unified'
    }

    if xaxis_title:
        layout_config['xaxis']['title'] = xaxis_title
    if yaxis_title:
        layout_config['yaxis']['title'] = yaxis_title

    if show_legend:
        layout_config['legend'] = dict(
            title=dict(text=legend_title, font=dict(weight='bold', color=colors['text_primary'])),
            bgcolor=colors['surface'],
            bordercolor=colors['border'],
            borderwidth=1,
            font=dict(color=colors['text_primary'])
        )

    fig.update_layout(**layout_config)
    return fig


# Custom CSS for button styling
def inject_custom_css():
    """Inject custom CSS to override default Streamlit button colors"""
    st.markdown("""
        <style>
        /* Primary button styling - Blue-Gray color */
        button[kind="primary"] {
            background-color: #6B7C93 !important;
            border-color: #6B7C93 !important;
        }
        button[kind="primary"]:hover {
            background-color: #5B6D82 !important;
            border-color: #5B6D82 !important;
        }
        button[kind="primary"]:active {
            background-color: #4B5D72 !important;
            border-color: #4B5D72 !important;
        }

        /* Reduce divider padding in sidebar */
        section[data-testid="stSidebar"] hr {
            margin-top: 0.5rem !important;
            margin-bottom: 0.5rem !important;
        }

        /* Ensure sidebar overlays on top of sandbox banner */
        section[data-testid="stSidebar"] {
            z-index: 1000001 !important;
        }

        /* Left-align sidebar buttons */
        section[data-testid="stSidebar"] button[kind="secondary"],
        section[data-testid="stSidebar"] button[kind="primary"] {
            text-align: left !important;
            justify-content: flex-start !important;
        }
        section[data-testid="stSidebar"] button[kind="secondary"] p,
        section[data-testid="stSidebar"] button[kind="primary"] p {
            text-align: left !important;
        }

        /* Hide all image hover elements in sidebar */
        section[data-testid="stSidebar"] button[data-testid="stBaseButton-elementToolbar"] {
            display: none !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stElementToolbar"] {
            display: none !important;
        }
        section[data-testid="stSidebar"] .st-emotion-cache-1v0mbdj {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)


# Sandbox mode floating banner
def render_sandbox_banner():
    """Render a floating top banner for sandbox mode"""
    if is_sandbox:
        st.markdown("""
        <div style="
            position: fixed;
            top: 0;
            left: 50px;
            right: 0;
            background: #fef9f3;
            color: #7a6f5d;
            padding: 10px 20px;
            text-align: center;
            font-size: 15px;
            z-index: 1000000;
            border-bottom: 1px solid #e8dcc8;
        ">
            Sandbox Mode
        </div>
        <div style="height: 40px;"></div>
        """, unsafe_allow_html=True)


# ===== THEME COLOR SYSTEM =====
# Comprehensive color palette that works elegantly with Streamlit's native theme detection

def is_dark_theme():
    """Detect if the active theme is dark using Streamlit's native theme detection"""
    try:
        return st.context.theme.type == "dark"
    except:
        # Fallback if st.context.theme is not available
        return False

def get_theme_colors():
    """
    Returns a comprehensive color palette based on the active Streamlit theme.
    Uses native st.context.theme for elegant theme detection.
    """
    is_dark = is_dark_theme()

    if is_dark:
        return {
            # Backgrounds
            'bg_primary': '#0E1117',      # Main background
            'bg_secondary': '#262730',    # Cards, containers
            'bg_tertiary': '#1E1E1E',     # Tables, alternating rows

            # Text colors
            'text_primary': '#FAFAFA',    # Main text
            'text_secondary': '#A3A8B8',  # Secondary text
            'text_muted': '#6C7A89',      # Muted/disabled text

            # Accent colors
            'accent_primary': '#6B7C93',  # Primary accent (Blue-Gray)
            'accent_secondary': '#0068C9', # Secondary accent (Streamlit blue)

            # UI Elements
            'border': '#3D3D3D',          # Borders, dividers
            'surface': '#262730',         # Elevated surfaces
            'surface_hover': '#31333C',   # Hover states

            # Chart colors
            'plot_bg': '#0E1117',         # Plot background
            'plot_grid': '#2D2D2D',       # Grid lines
            'plot_axis': '#6C7A89',       # Axis lines
            'plot_text': '#FAFAFA',       # Chart text

            # Table colors
            'table_row_even': '#262730',  # Even rows
            'table_row_odd': '#0E1117',   # Odd rows
            'table_header': '#31333C',    # Table headers
        }
    else:
        return {
            # Backgrounds
            'bg_primary': '#FFFFFF',      # Main background
            'bg_secondary': '#F0F2F6',    # Cards, containers
            'bg_tertiary': '#FAFAFA',     # Tables, alternating rows

            # Text colors
            'text_primary': '#262730',    # Main text
            'text_secondary': '#6C7A89',  # Secondary text
            'text_muted': '#A3A8B8',      # Muted/disabled text

            # Accent colors
            'accent_primary': '#6B7C93',  # Primary accent (Blue-Gray)
            'accent_secondary': '#0068C9', # Secondary accent (Streamlit blue)

            # UI Elements
            'border': '#E0E0E0',          # Borders, dividers
            'surface': '#FFFFFF',         # Elevated surfaces
            'surface_hover': '#F0F2F6',   # Hover states

            # Chart colors
            'plot_bg': '#FFFFFF',         # Plot background
            'plot_grid': '#E0E0E0',       # Grid lines
            'plot_axis': '#6C7A89',       # Axis lines
            'plot_text': '#262730',       # Chart text

            # Table colors
            'table_row_even': '#FFFFFF',  # Even rows
            'table_row_odd': '#F8F9FA',   # Odd rows
            'table_header': '#F0F2F6',    # Table headers
        }


# ===== REUSABLE TABLE COMPONENT =====
# Provides consistent table styling across the app

def render_data_table(data, columns=None, hide_index=True):
    """
    Render a styled dataframe with consistent theme-aware formatting.

    Args:
        data: List of dictionaries or pandas DataFrame
        columns: Optional list of column names to display (in order)
        hide_index: Whether to hide the index column (default: True)

    Returns:
        Displays the styled dataframe
    """
    import pandas as pd

    # Convert to DataFrame if needed
    if not isinstance(data, pd.DataFrame):
        df = pd.DataFrame(data)
    else:
        df = data

    # Select and order columns if specified
    if columns:
        df = df[columns]

    # Apply alternating row colors using theme palette
    colors = get_theme_colors()
    styled_df = df.style.apply(
        lambda x: [f'background-color: {colors["table_row_even"]}' if i % 2 == 0
                   else f'background-color: {colors["table_row_odd"]}' for i in range(len(x))],
        axis=0
    )

    st.dataframe(styled_df, width="stretch", hide_index=hide_index)


# ===== REUSABLE CURRENCY SELECTOR COMPONENT =====
# Provides consistent currency selection across the app

def render_currency_selector(label="Select Currency", default_index=0, key=None):
    """
    Render a currency selector dropdown with consistent formatting.

    Args:
        label: Label for the dropdown (default: "Select Currency")
        default_index: Index of default selection (defaults to first currency)
        key: Unique key for the selectbox (required if multiple selectors on same page)

    Returns:
        str: Selected currency code
    """
    # Get enabled currencies from database
    enabled_currencies = db.get_currency_codes()

    # Ensure default_index is valid
    if default_index >= len(enabled_currencies):
        default_index = 0

    selected = st.selectbox(
        label,
        options=enabled_currencies,
        index=default_index,
        key=key
    )
    return selected


# Sidebar
def render_sidebar():
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

        # Navigation buttons - Dashboard, Reminder, and Exchange Rates grouped together
        if st.button("📊 Dashboard", width="stretch"):
            st.session_state.settings_nav = None
            st.rerun()

        if st.button("🔔 Reminder", width="stretch"):
            st.session_state.settings_nav = "Reminder"
            st.rerun()

        if st.button("💹 Exchange Rates", width="stretch"):
            st.session_state.settings_nav = "Exchange Rates"
            st.rerun()

        if st.button("🏠 Mortgage", width="stretch"):
            st.session_state.settings_nav = "Mortgage"
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
    if is_sandbox:
        # Clear cache to force database reload
        st.cache_resource.clear()

        # Recreate sandbox database with fresh sample data
        db_path = "kuyan-sandbox.db"
        if os.path.exists(db_path):
            os.remove(db_path)

        # Create new database and seed
        fresh_db = Database(db_path=db_path)
        fresh_db.seed_sample_data()


# Helper functions
def has_multiple_currencies() -> bool:
    """
    Check if exchange rate functionality should be enabled.
    
    Exchange rates are enabled when:
    - At least 1 currency AND 1 commodity is available, OR
    - At least 2 currencies without any commodity, OR
    - Both currency and commodity counts are more than 2
    """
    currency_count = db.get_currency_count()
    commodity_count = db.get_commodity_count()
    
    # Case 1: At least 1 currency and 1 commodity
    if currency_count >= 1 and commodity_count >= 1:
        return True
    
    # Case 2: At least 2 currencies without any commodity
    if currency_count >= 2 and commodity_count == 0:
        return True
    
    # Case 3: Both currency and commodity are more than 2
    if currency_count >= 2 and commodity_count >= 2:
        return True
    
    return False


def get_currency_symbol(currency):
    """Get currency symbol for display"""
    symbols = {
        "AUD": "A$",
        "BGN": "лв",
        "BRL": "R$",
        "CAD": "CA$",
        "CHF": "CHF",
        "CNY": "¥",
        "CZK": "Kč",
        "DKK": "kr",
        "EUR": "€",
        "GBP": "£",
        "HKD": "HK$",
        "HUF": "Ft",
        "IDR": "Rp",
        "ILS": "₪",
        "INR": "₹",
        "ISK": "kr",
        "JPY": "¥",
        "KRW": "₩",
        "MXN": "MX$",
        "MYR": "RM",
        "NOK": "kr",
        "NZD": "NZ$",
        "PHP": "₱",
        "PLN": "zł",
        "RON": "lei",
        "RUB": "₽",
        "SEK": "kr",
        "SGD": "S$",
        "THB": "฿",
        "TRY": "₺",
        "USD": "US$",
        "ZAR": "R"
    }
    return symbols.get(currency, currency)


def get_converted_value(amount, from_currency, to_currency, rates):
    """Convert amount using exchange rates"""
    if not rates:
        return amount
    return CurrencyConverter.convert(amount, from_currency, to_currency, rates)


def calculate_total_net_worth(snapshots, base_currency):
    """Calculate total net worth from snapshots in base currency"""
    if not snapshots:
        return 0.0

    total = 0.0
    rates = None
    
    # Get exchange rates from first snapshot (all snapshots from same date should have same rates)
    for snapshot in snapshots:
        if snapshot.get("exchange_rates"):
            rates = json.loads(snapshot["exchange_rates"])
            break
    
    # Fetch commodity prices if there are commodity accounts
    commodity_accounts = [s for s in snapshots if s.get("account_type") == "Commodity"]
    commodity_prices = {}
    commodity_configs = {}
    
    if commodity_accounts and rates:
        # Get snapshot date and unique commodities
        snapshot_date_str = snapshots[0].get("snapshot_date")
        commodity_list = [s.get("commodity") for s in commodity_accounts if s.get("commodity")]
        unique_commodities = list(set([c for c in commodity_list if c is not None]))
        
        # Get enabled currencies from database
        enabled_currencies = db.get_currency_codes()
        
        # Fetch commodity prices for the snapshot date (prices are per troy ounce)
        if unique_commodities:
            commodity_prices = CurrencyConverter.get_commodity_prices(
                unique_commodities,
                enabled_currencies,
                date=snapshot_date_str
            ) or {}
            
            # If historical prices not available, try to get latest prices as fallback
            # Check if any commodity is missing prices for any enabled currency
            needs_fallback = False
            for commodity in unique_commodities:
                if commodity not in commodity_prices:
                    needs_fallback = True
                    break
                for currency in enabled_currencies:
                    if currency not in commodity_prices.get(commodity, {}):
                        needs_fallback = True
                        break
                if needs_fallback:
                    break
            
            if needs_fallback:
                latest_prices = CurrencyConverter.get_commodity_prices(
                    unique_commodities,
                    enabled_currencies,
                    date=None  # Get latest prices
                ) or {}
                
                # Merge latest prices for missing commodities/currencies
                for commodity in unique_commodities:
                    if commodity not in commodity_prices:
                        commodity_prices[commodity] = {}
                    if commodity in latest_prices:
                        for currency in enabled_currencies:
                            if currency not in commodity_prices[commodity] and currency in latest_prices[commodity]:
                                commodity_prices[commodity][currency] = latest_prices[commodity][currency]
            
            # Get commodity configurations to know the units
            commodity_configs = {c['name']: c for c in db.get_commodities()}

    for snapshot in snapshots:
        is_commodity = snapshot.get("account_type") == "Commodity"
        
        if is_commodity:
            # For commodity accounts: quantity * price per unit in target currency
            commodity_name = snapshot.get("commodity")
            quantity = snapshot["balance"]
            
            # Get commodity price in base currency (API returns price per troy ounce)
            if commodity_name and commodity_name in commodity_prices:
                price_per_ounce = commodity_prices[commodity_name].get(base_currency, 0)
                
                # Get the unit for this commodity from database
                commodity_unit = "ounce"  # Default to ounce
                if commodity_name in commodity_configs:
                    commodity_unit = commodity_configs[commodity_name].get('unit', 'ounce')
                
                # Convert price from per-ounce to per-unit
                price_per_unit = CurrencyConverter.convert_commodity_unit(
                    price_per_ounce,
                    "ounce",  # API always returns per troy ounce
                    commodity_unit  # Convert to the commodity's configured unit
                )
                
                # Calculate total value: quantity * price per unit
                converted = quantity * price_per_unit
            else:
                # Fallback: if no price available, use 0
                converted = 0.0
        else:
            # For regular accounts: use currency conversion
            if rates:
                converted = get_converted_value(
                    snapshot["balance"],
                    snapshot["currency"],
                    base_currency,
                    rates
                )
            else:
                converted = snapshot["balance"]
        
        total += converted

    return total


# Page: Dashboard
def page_dashboard():    
    # Get default base currency (first enabled currency)
    default_currency = get_default_currency()
    base_currency = st.session_state.get("base_currency", default_currency)

    # Get latest snapshots
    latest_snapshots = db.get_latest_snapshots()

    if not latest_snapshots:
        st.info("No data available. Add accounts and create your first monthly snapshot!")
        return

    # Get enabled currencies
    enabled_currencies = db.get_currencies()

    # Calculate current net worth in all enabled currencies
    net_worths = {}
    for currency in enabled_currencies:
        net_worths[currency['code']] = calculate_total_net_worth(latest_snapshots, currency['code'])

    # Display current net worth in all currencies with flags
    st.subheader("Current Net Worth")

    # Get theme colors for metric cards
    colors = get_theme_colors()

    # Smart row distribution to prevent wrapping
    # 1-4 currencies: 1 row (up to 4 columns)
    # 5-6 currencies: 2 rows (3 columns each)
    # 7-9 currencies: 3 rows (3 columns each)
    num_currencies = len(enabled_currencies)

    if num_currencies <= 4:
        rows = [enabled_currencies]  # All in one row
    elif num_currencies <= 6:
        # Split into 2 rows of 3 each
        mid = (num_currencies + 1) // 2
        rows = [enabled_currencies[:mid], enabled_currencies[mid:]]
    else:
        # Split into 3 rows of 3 each
        third = (num_currencies + 2) // 3
        rows = [
            enabled_currencies[:third],
            enabled_currencies[third:third*2],
            enabled_currencies[third*2:]
        ]

    # Render each row
    for row_currencies in rows:
        cols = st.columns(len(row_currencies))

        for idx, currency in enumerate(row_currencies):
            with cols[idx]:
                curr_symbol = get_currency_symbol(currency['code'])
                net_worth = net_worths[currency['code']]

                st.markdown(f"""
                <div style="background-color: {colors['bg_secondary']}; padding: 20px; border-radius: 10px; border-left: 5px solid {currency['color']};">
                    <p style="margin: 0; font-size: 14px; color: {colors['text_secondary']};">{currency['flag_emoji']} {currency['code']}</p>
                    <p style="margin: 0; font-size: 28px; font-weight: bold; color: {colors['text_primary']};">{curr_symbol}{net_worth:,.2f}</p>
                </div>
                """, unsafe_allow_html=True)

        # Add small spacing between rows
        if row_currencies != rows[-1]:
            st.write("")

    st.divider()

    # Account breakdown table
    col_header, col_currency = st.columns([3, 1])
    with col_header:
        st.subheader("Account Breakdown")
        st.caption("Currency conversions use exchange rates from the 1st of the snapshot month")
    with col_currency:
        base_currency = render_currency_selector(
            label="Select Currency",
            default_index=0,
            key="currency_selector"
        )
        # Update session state for other pages
        st.session_state.base_currency = base_currency

    if latest_snapshots:
        rates = json.loads(latest_snapshots[0]["exchange_rates"]) if latest_snapshots[0].get("exchange_rates") else {}
        
        # Fetch commodity prices for the snapshot date
        snapshot_date_str = latest_snapshots[0]["snapshot_date"]
        commodity_accounts = [s for s in latest_snapshots if s["account_type"] == "Commodity"]
        commodity_prices = {}
        commodity_configs = {}
        
        if commodity_accounts:
            # Get unique commodities and enabled currencies
            commodity_list = [s.get("commodity") for s in commodity_accounts if s.get("commodity")]
            unique_commodities = list(set([c for c in commodity_list if c is not None]))  # Remove duplicates and None
            enabled_currencies = db.get_currency_codes()
            
            # Fetch commodity prices for the snapshot date (prices are per troy ounce)
            commodity_prices = CurrencyConverter.get_commodity_prices(
                unique_commodities,
                enabled_currencies,
                date=snapshot_date_str
            ) or {}
            
            # Get commodity configurations to know the units
            commodity_configs = {c['name']: c for c in db.get_commodities()}

        breakdown_data = []
        total_converted = 0.0

        for snapshot in latest_snapshots:
            is_commodity = snapshot["account_type"] == "Commodity"
            
            if is_commodity:
                # For commodity accounts: quantity * price per unit in target currency
                commodity_name = snapshot.get("commodity")
                quantity = snapshot["balance"]
                
                # Get commodity price in base currency (API returns price per troy ounce)
                if commodity_name and commodity_name in commodity_prices:
                    price_per_ounce = commodity_prices[commodity_name].get(base_currency, 0)
                    
                    # Get the unit for this commodity from database
                    commodity_unit = "ounce"  # Default to ounce
                    if commodity_name in commodity_configs:
                        commodity_unit = commodity_configs[commodity_name].get('unit', 'ounce')
                    
                    # Convert price from per-ounce to per-unit
                    price_per_unit = CurrencyConverter.convert_commodity_unit(
                        price_per_ounce,
                        "ounce",  # API always returns per troy ounce
                        commodity_unit  # Convert to the commodity's configured unit
                    )
                    
                    # Calculate total value: quantity * price per unit
                    converted_value = quantity * price_per_unit
                else:
                    # Fallback: if no price available, use 0
                    converted_value = 0.0
                    
            else:
                # For regular accounts: use currency conversion
                converted_value = get_converted_value(
                    snapshot["balance"],
                    snapshot["currency"],
                    base_currency,
                    rates
                )
            
            total_converted += converted_value

            # For commodity accounts, show commodity name instead of currency
            native_currency_display = snapshot.get("commodity", snapshot["currency"]) if is_commodity else snapshot["currency"]
            
            # For commodity accounts, show balance without currency symbol (just the amount with unit)
            if is_commodity:
                # Extract unit from account name (e.g., "Gold (ounce)" -> "ounce")
                account_name = snapshot["name"]
                unit = "units"
                if "(" in account_name and ")" in account_name:
                    unit = account_name[account_name.rfind("(")+1:account_name.rfind(")")]
                native_balance_display = f"{snapshot['balance']:,.2f} {unit}"
            else:
                native_balance_display = f"{get_currency_symbol(snapshot['currency'])}{snapshot['balance']:,.2f}"
            
            breakdown_data.append({
                "Account": snapshot["name"],
                "Owner": snapshot["owner"],
                "Type": snapshot["account_type"],
                "Native Currency": native_currency_display,
                "Native Balance": native_balance_display,
                f"{base_currency} Value": f"{get_currency_symbol(base_currency)}{converted_value:,.2f}"
            })

        # Get theme colors
        colors = get_theme_colors()
        
        # Use Streamlit's native expander with custom styling for the header
        # Create a styled header that looks like the total row
        st.markdown(f"""
        <style>
        div[data-testid="stExpander"] {{
            border: none;
            box-shadow: none;
        }}
        div[data-testid="stExpander"] > div:first-child {{
            padding: 15px;
            background-color: {colors['bg_secondary']};
            border-top: 2px solid {colors['border']};
            border-radius: 5px;
        }}
        div[data-testid="stExpander"] > div:first-child:hover {{
            opacity: 0.9;
        }}
        </style>
        """, unsafe_allow_html=True)
        
        # Create expander with styled label showing total
        with st.expander(f"**TOTAL {base_currency}** — {get_currency_symbol(base_currency)}{total_converted:,.2f}", expanded=False):
            # Display account breakdown table
            render_data_table(breakdown_data)

    st.divider()

    snapshot_dates = db.get_all_snapshot_dates()

    if len(snapshot_dates) > 1:
        # Create two columns for side-by-side graphs
        graph_col1, graph_col2 = st.columns(2)
        
        # Left column: Net Worth Over Time
        with graph_col1:
            # Net worth over time with currency selector
            st.markdown("#### Net Worth Over Time")

            # Currency selector
            selected_currency = render_currency_selector(
                label="Select Currency",
                default_index=0,
                key="networth_currency_selector"
            )

        # Right column: Currency Holdings Growth header and baseline selector
        with graph_col2:
            st.markdown("#### Currency Holdings Growth (Normalized)")
            
            # Baseline month selector
            # Convert dates to month labels for display (descending order - newest first)
            month_labels = [datetime.fromisoformat(d).strftime("%b %Y") for d in snapshot_dates]
            baseline_month_label = st.selectbox(
                "Baseline Month (100%)",
                options=month_labels,
                index=len(month_labels) - 1,  # Default to oldest month
                key="baseline_month_selector"
            )
            # Get the index of selected baseline (adjusted for reversed loop below)
            baseline_index = len(month_labels) - 1 - month_labels.index(baseline_month_label)

        # Collect data for selected currency
        history_data = []

        for snapshot_date in reversed(snapshot_dates):
            snapshots = db.get_snapshots_by_date(date.fromisoformat(snapshot_date))
            net_worth = calculate_total_net_worth(snapshots, selected_currency)

            # Use month label instead of full date (uppercase month, year on next line)
            dt = datetime.fromisoformat(snapshot_date)
            month_label = f"{dt.strftime('%b').upper()}<br>{dt.year}"
            history_data.append({
                "Month": month_label,
                "Net Worth": net_worth,
                "Date": snapshot_date  # Keep actual date for proper sorting
            })

        df_history = pd.DataFrame(history_data)
        # Sort by actual date to ensure chronological order
        df_history = df_history.sort_values('Date')

        # Build dynamic currency color map from database
        color_map = {}
        for curr in db.get_currencies():
            color_map[curr['code']] = curr['color']

        currency_symbol = get_currency_symbol(selected_currency)

        fig_line = px.line(
            df_history,
            x="Month",
            y="Net Worth",
            title=f"Total Net Worth in {selected_currency}",
            markers=True
        )

        # Apply color based on selected currency
        fig_line.update_traces(
            line_color=color_map[selected_currency],
            line=dict(width=3),
            marker=dict(size=8),
            hovertemplate=f'Net Worth: {currency_symbol}' + '%{y:,.2f}<br>' +
                         '<extra></extra>'
        )

        # Get theme colors
        colors = get_theme_colors()

        fig_line.update_layout(
            xaxis_title="Month",
            yaxis_title=f"Net Worth ({selected_currency})",
            hovermode="x unified",
            xaxis=dict(
                showline=True,
                linewidth=2,
                linecolor=colors['plot_axis'],
                mirror=False,
                showgrid=True,
                gridwidth=1,
                gridcolor=colors['plot_grid'],
                title_font=dict(size=14, family='Arial, sans-serif', color=colors['plot_text'], weight='bold'),
                showspikes=True,
                spikecolor=colors['plot_axis'],
                spikethickness=1,
                type='category',  # Treat as categorical to preserve order
                categoryorder='array',  # Use array order
                categoryarray=df_history['Month'].tolist()  # Explicit order from sorted data
            ),
            yaxis=dict(
                showline=True,
                linewidth=2,
                linecolor=colors['plot_axis'],
                mirror=False,
                showgrid=True,
                gridwidth=1,
                gridcolor=colors['plot_grid'],
                title_font=dict(size=14, family='Arial, sans-serif', color=colors['plot_text'], weight='bold'),
                showspikes=True,
                spikecolor=colors['plot_axis'],
                spikethickness=1
            ),
            plot_bgcolor=colors['plot_bg'],
            paper_bgcolor=colors['plot_bg'],
            font=dict(color=colors['plot_text']),
            title_font=dict(color=colors['text_primary']),
            hoverlabel=dict(
                bgcolor=colors['surface'],
                font_size=13,
                font_family="Arial, sans-serif",
                font_color=colors['text_primary']
            )
        )
        
        # Collect data for amounts held in each currency
        currency_split_data = []
        baseline_holdings = {}

        # Get all enabled currencies dynamically
        enabled_currency_codes = db.get_currency_codes()

        for i, snapshot_date in enumerate(reversed(snapshot_dates)):
            snapshots = db.get_snapshots_by_date(date.fromisoformat(snapshot_date))

            # Calculate totals for each currency (not converted) - dynamically initialize
            currency_totals = {curr: 0.0 for curr in enabled_currency_codes}

            for snapshot in snapshots:
                curr = snapshot["currency"]
                balance = snapshot["balance"]
                if curr in currency_totals:
                    currency_totals[curr] += balance

            # Store baseline values from selected month
            if i == baseline_index:
                for curr in enabled_currency_codes:
                    baseline_holdings[curr] = currency_totals[curr] if currency_totals[curr] > 0 else 1

            # Calculate percentage relative to baseline for each currency
            if baseline_holdings:  # Only calculate if baseline is set
                for currency, total in currency_totals.items():
                    pct = (total / baseline_holdings[currency] * 100) if baseline_holdings[currency] > 0 else 100
                    # Use month label instead of full date (uppercase month, year on next line)
                    dt = datetime.fromisoformat(snapshot_date)
                    month_label = f"{dt.strftime('%b').upper()}<br>{dt.year}"
                    currency_split_data.append({
                        "Month": month_label,
                        "Currency": currency,
                        "Growth %": pct
                    })

        df_currency_split = pd.DataFrame(currency_split_data)

        fig_split = px.line(
            df_currency_split,
            x="Month",
            y="Growth %",
            color="Currency",
            color_discrete_map=color_map,
            title=f"Currency Holdings Growth (Baseline: {baseline_month_label} = 100%)",
            markers=True
        )

        fig_split.update_traces(
            line=dict(width=3),
            marker=dict(size=8),
            hovertemplate='Growth: %{y:.1f}%<br>' +
                         '<extra></extra>'
        )

        # Get theme colors
        colors = get_theme_colors()

        fig_split.update_layout(
            xaxis_title="Month",
            yaxis_title=f"Growth Index ({baseline_month_label} = 100%)",
            hovermode="x unified",
            xaxis=dict(
                showline=True,
                linewidth=2,
                linecolor=colors['plot_axis'],
                mirror=False,
                showgrid=True,
                gridwidth=1,
                gridcolor=colors['plot_grid'],
                title_font=dict(size=14, family='Arial, sans-serif', color=colors['plot_text'], weight='bold'),
                showspikes=True,
                spikecolor=colors['plot_axis'],
                spikethickness=1
            ),
            yaxis=dict(
                showline=True,
                linewidth=2,
                linecolor=colors['plot_axis'],
                mirror=False,
                showgrid=True,
                gridwidth=1,
                gridcolor=colors['plot_grid'],
                title_font=dict(size=14, family='Arial, sans-serif', color=colors['plot_text'], weight='bold'),
                showspikes=True,
                spikecolor=colors['plot_axis'],
                spikethickness=1
            ),
            plot_bgcolor=colors['plot_bg'],
            paper_bgcolor=colors['plot_bg'],
            font=dict(color=colors['plot_text']),
            title_font=dict(color=colors['text_primary']),
            hoverlabel=dict(
                bgcolor=colors['surface'],
                font_size=13,
                font_family="Arial, sans-serif",
                font_color=colors['text_primary']
            ),
            legend=dict(
                title=dict(text="Currency", font=dict(weight='bold', color=colors['text_primary'])),
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor=colors['surface'],
                bordercolor=colors['border'],
                borderwidth=1,
                font=dict(color=colors['text_primary'])
            )
        )
        
        # Render both charts in their respective columns
        with graph_col1:
            st.plotly_chart(fig_line, use_container_width=True)
            st.markdown(
                '<p style="text-align: right; font-size: 0.6rem; margin-top: -10px;">* Monthly exchange rates are derived from rates effective on the 1st of each month</p>',
                unsafe_allow_html=True
            )
        
        with graph_col2:
            st.plotly_chart(fig_split, use_container_width=True)
        
        st.divider()
                
        # Create two columns for pie charts
        pie_col1, pie_col2 = st.columns(2)
        
        # Get latest snapshots for pie charts
        latest_snapshots = db.get_latest_snapshots()
        
        if latest_snapshots:
            # Prepare data for pie charts
            rates = json.loads(latest_snapshots[0]["exchange_rates"]) if latest_snapshots[0].get("exchange_rates") else {}
            snapshot_date_str = latest_snapshots[0]["snapshot_date"]
            
            # Fetch commodity prices
            commodity_accounts = [s for s in latest_snapshots if s["account_type"] == "Commodity"]
            commodity_prices = {}
            commodity_configs = {}
            
            if commodity_accounts:
                commodity_list = [s.get("commodity") for s in commodity_accounts if s.get("commodity")]
                unique_commodities = list(set([c for c in commodity_list if c is not None]))
                enabled_currencies = db.get_currency_codes()
                
                commodity_prices = CurrencyConverter.get_commodity_prices(
                    unique_commodities,
                    enabled_currencies,
                    date=snapshot_date_str
                ) or {}
                
                commodity_configs = {c['name']: c for c in db.get_commodities()}
            
            # Calculate values by owner and type
            value_by_owner = {}
            value_by_type = {}
            
            for snapshot in latest_snapshots:
                is_commodity = snapshot["account_type"] == "Commodity"
                
                if is_commodity:
                    commodity_name = snapshot.get("commodity")
                    quantity = snapshot["balance"]
                    
                    if commodity_name and commodity_name in commodity_prices:
                        price_per_ounce = commodity_prices[commodity_name].get(base_currency, 0)
                        commodity_unit = "ounce"
                        if commodity_name in commodity_configs:
                            commodity_unit = commodity_configs[commodity_name].get('unit', 'ounce')
                        
                        price_per_unit = CurrencyConverter.convert_commodity_unit(
                            price_per_ounce,
                            "ounce",
                            commodity_unit
                        )
                        converted_value = quantity * price_per_unit
                    else:
                        converted_value = 0.0
                else:
                    converted_value = get_converted_value(
                        snapshot["balance"],
                        snapshot["currency"],
                        base_currency,
                        rates
                    )
                
                # Aggregate by owner
                owner = snapshot["owner"]
                if owner not in value_by_owner:
                    value_by_owner[owner] = 0.0
                value_by_owner[owner] += converted_value
                
                # Aggregate by type
                acc_type = snapshot["account_type"]
                if acc_type not in value_by_type:
                    value_by_type[acc_type] = 0.0
                value_by_type[acc_type] += converted_value
            
            # Get theme colors
            colors = get_theme_colors()
            
            # Get currency symbol for pie charts
            currency_symbol = get_currency_symbol(base_currency)
            
            # Pie chart 1: Value by Owner
            with pie_col1:
                st.markdown("#### Value by Owner")
                
                df_owner = pd.DataFrame([
                    {"Owner": owner, "Value": value}
                    for owner, value in value_by_owner.items()
                ])
                
                fig_owner = px.pie(
                    df_owner,
                    values="Value",
                    names="Owner",
                    title=f"Value by Owner ({base_currency})"
                )
                
                fig_owner.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    hovertemplate=f'<b>%{{label}}</b><br>Value: {currency_symbol}%{{value:,.2f}}<br>Percentage: %{{percent}}<extra></extra>'
                )
                
                fig_owner.update_layout(
                    plot_bgcolor=colors['plot_bg'],
                    paper_bgcolor=colors['plot_bg'],
                    font=dict(color=colors['plot_text']),
                    title_font=dict(color=colors['text_primary']),
                    hoverlabel=dict(
                        bgcolor=colors['surface'],
                        font_size=13,
                        font_family="Arial, sans-serif",
                        font_color=colors['text_primary']
                    ),
                    showlegend=True,
                    legend=dict(
                        bgcolor=colors['surface'],
                        bordercolor=colors['border'],
                        borderwidth=1,
                        font=dict(color=colors['text_primary'])
                    )
                )
                
                st.plotly_chart(fig_owner, use_container_width=True)
            
            # Pie chart 2: Value by Type
            with pie_col2:
                st.markdown("#### Value by Type")
                
                df_type = pd.DataFrame([
                    {"Type": acc_type, "Value": value}
                    for acc_type, value in value_by_type.items()
                ])
                
                fig_type = px.pie(
                    df_type,
                    values="Value",
                    names="Type",
                    title=f"Value by Type ({base_currency})"
                )
                
                fig_type.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    hovertemplate=f'<b>%{{label}}</b><br>Value: {currency_symbol}%{{value:,.2f}}<br>Percentage: %{{percent}}<extra></extra>'
                )
                
                fig_type.update_layout(
                    plot_bgcolor=colors['plot_bg'],
                    paper_bgcolor=colors['plot_bg'],
                    font=dict(color=colors['plot_text']),
                    title_font=dict(color=colors['text_primary']),
                    hoverlabel=dict(
                        bgcolor=colors['surface'],
                        font_size=13,
                        font_family="Arial, sans-serif",
                        font_color=colors['text_primary']
                    ),
                    showlegend=True,
                    legend=dict(
                        bgcolor=colors['surface'],
                        bordercolor=colors['border'],
                        borderwidth=1,
                        font=dict(color=colors['text_primary'])
                    )
                )
                
                st.plotly_chart(fig_type, use_container_width=True)
        
        st.divider()

        # Year-over-year comparison if we have enough data
        if len(snapshot_dates) >= 12:
            st.subheader("Year-over-Year Comparison")

            # Currency selector for YoY graph
            col1, col2 = st.columns([1, 3])
            with col1:
                yoy_currency = render_currency_selector(
                    label="Select Currency",
                    default_index=0,
                    key="yoy_currency_selector"
                )

            # Get all unique years from snapshots
            years = sorted(list(set([datetime.fromisoformat(d).year for d in snapshot_dates])))

            # Month names in order (uppercase)
            month_names = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

            # Create data structure with only months that have data
            yoy_data = []

            # Create a lookup dict for existing data
            data_lookup = {}
            for snapshot_date in snapshot_dates:
                dt = datetime.fromisoformat(snapshot_date)
                snapshots = db.get_snapshots_by_date(date.fromisoformat(snapshot_date))
                total = calculate_total_net_worth(snapshots, yoy_currency)
                key = (dt.year, dt.month)
                data_lookup[key] = total

            # Populate only months that have data (include year in x-axis label)
            for year in years:
                for month_num in range(1, 13):
                    key = (year, month_num)
                    if key in data_lookup:
                        yoy_data.append({
                            "Month": f"{month_names[month_num - 1]}<br>{year}",
                            "Year": str(year),
                            "Net Worth": data_lookup[key]
                        })

            df_yoy = pd.DataFrame(yoy_data)

            currency_symbol = get_currency_symbol(yoy_currency)
            fig_yoy = px.line(
                df_yoy,
                x="Month",
                y="Net Worth",
                color="Year",
                title=f"Year-over-Year Comparison ({yoy_currency})",
                markers=True
            )

            # Set month order
            fig_yoy.update_xaxes(categoryorder='array', categoryarray=month_names)

            fig_yoy.update_traces(
                line=dict(width=3),
                marker=dict(size=8),
                hovertemplate=f'Net Worth: {currency_symbol}' + '%{y:,.2f}<br>' +
                             '<extra></extra>'
            )

            # Get theme colors
            colors = get_theme_colors()

            fig_yoy.update_layout(
                hovermode="x unified",
                xaxis=dict(
                    showline=True,
                    linewidth=2,
                    linecolor=colors['plot_axis'],
                    mirror=False,
                    showgrid=True,
                    gridwidth=1,
                    gridcolor=colors['plot_grid'],
                    title_font=dict(size=14, family='Arial, sans-serif', color=colors['plot_text'], weight='bold'),
                    showspikes=True,
                    spikecolor=colors['plot_axis'],
                    spikethickness=1
                ),
                yaxis=dict(
                    showline=True,
                    linewidth=2,
                    linecolor=colors['plot_axis'],
                    mirror=False,
                    showgrid=True,
                    gridwidth=1,
                    gridcolor=colors['plot_grid'],
                    title_font=dict(size=14, family='Arial, sans-serif', color=colors['plot_text'], weight='bold'),
                    showspikes=True,
                    spikecolor=colors['plot_axis'],
                    spikethickness=1
                ),
                plot_bgcolor=colors['plot_bg'],
                paper_bgcolor=colors['plot_bg'],
                font=dict(color=colors['plot_text']),
                title_font=dict(color=colors['text_primary']),
                hoverlabel=dict(
                    bgcolor=colors['surface'],
                    font_size=13,
                    font_family="Arial, sans-serif",
                    font_color=colors['text_primary']
                ),
                legend=dict(
                    title=dict(text="Year", font=dict(weight='bold', color=colors['text_primary'])),
                    bgcolor=colors['surface'],
                    bordercolor=colors['border'],
                    borderwidth=1,
                    font=dict(color=colors['text_primary'])
                )
            )
            st.plotly_chart(fig_yoy, use_container_width=True)
            st.markdown(
                '<p style="text-align: right; font-size: 0.6rem; margin-top: -10px;">* Monthly exchange rates are derived from rates effective on the 1st of each month</p>',
                unsafe_allow_html=True
            )
            st.divider()
    else:
        st.info("Add more monthly snapshots to see trends over time")


# Page: Accounts
def page_accounts(key_prefix=""):
    # Unit options for commodity accounts
    UNIT_OPTIONS = ["gram", "ounce", "kilo"]

    # Show success message if account was just added
    show_success_toast('account')

    # List existing accounts with filter
    col_title, col_filter = st.columns([3, 1])
    with col_title:
        st.subheader("Existing Accounts")
    with col_filter:
        # Account type filter dropdown aligned to the right
        filter_options = ["All Types", "Bank", "Investment", "Commodity", "Other"]
        selected_filter = st.selectbox(
            "Filter by Type",
            filter_options,
            key=f"{key_prefix}account_type_filter",
            label_visibility="collapsed"
        )

    accounts = db.get_accounts()
    owner_names = db.get_owner_names()
    currency_codes = db.get_currency_codes()
    commodity_list = db.get_commodities()

    # Apply filter if not "All Types"
    if selected_filter != "All Types":
        accounts = [acc for acc in accounts if acc['account_type'] == selected_filter]

    if accounts:
        # Group accounts by owner for better organization
        accounts_by_owner = {}
        for acc in accounts:
            if acc['owner'] not in accounts_by_owner:
                accounts_by_owner[acc['owner']] = []
            accounts_by_owner[acc['owner']].append(acc)

        # Display accounts grouped by owner
        for owner_name in sorted(accounts_by_owner.keys()):
            st.write(f"**{owner_name}:**")

            for account in accounts_by_owner[owner_name]:
                # Create expandable section for each account
                is_commodity = account['account_type'] == "Commodity"
                account_icon = "🏦" if account['account_type'] == "Bank" else "📈" if account['account_type'] == "Investment" else "🏛️" if account['account_type'] == "Pension" else "🥇" if is_commodity else "💼"
                display_label = account.get('commodity', account['currency']) if is_commodity else account['currency']
                with st.expander(f"{account_icon} {account['name']} - {display_label}", expanded=False):
                    st.write(f"**Type:** {account['account_type']}")
                    if is_commodity:
                        st.write(f"**Commodity:** {account.get('commodity', 'N/A')}")
                    else:
                        st.write(f"**Currency:** {account['currency']}")

                    st.write("**Edit Account:**")
                    col1, col2 = st.columns(2)

                    with col1:
                        # For commodity accounts, name is uneditable
                        if is_commodity:
                            new_name = st.text_input(
                                "Account Name",
                                value=account['name'],
                                key=f"{key_prefix}name_{account['id']}",
                                disabled=True,
                                help="Commodity account names are auto-generated"
                            )
                        else:
                            new_name = st.text_input(
                                "Account Name",
                                value=account['name'],
                                key=f"{key_prefix}name_{account['id']}"
                            )
                        owner_index = owner_names.index(account['owner']) if account['owner'] in owner_names else 0
                        new_owner = st.selectbox(
                            "Owner",
                            owner_names,
                            index=owner_index,
                            key=f"{key_prefix}owner_{account['id']}"
                        )

                    with col2:
                        type_options = ["Bank", "Investment", "Pension", "Commodity", "Other"]
                        type_index = type_options.index(account['account_type']) if account['account_type'] in type_options else 0
                        new_type = st.selectbox(
                            "Account Type",
                            type_options,
                            index=type_index,
                            key=f"{key_prefix}type_{account['id']}"
                        )
                        
                        # Show currency or commodity dropdown based on account type
                        if new_type == "Commodity":
                            commodity_names = [c['name'] for c in commodity_list]
                            current_commodity = account.get('commodity', commodity_names[0] if commodity_names else '')
                            comm_index = commodity_names.index(current_commodity) if current_commodity in commodity_names else 0
                            new_commodity = st.selectbox(
                                "Commodity",
                                commodity_names,
                                index=comm_index,
                                key=f"{key_prefix}commodity_{account['id']}"
                            )
                            
                            # Extract unit from account name (format: "Gold (ounce)")
                            current_unit = "ounce"  # default
                            if '(' in account['name'] and ')' in account['name']:
                                unit_part = account['name'].split('(')[1].split(')')[0]
                                if unit_part in UNIT_OPTIONS:
                                    current_unit = unit_part
                            
                            unit_index = UNIT_OPTIONS.index(current_unit) if current_unit in UNIT_OPTIONS else 1
                            new_unit = st.selectbox(
                                "Unit",
                                UNIT_OPTIONS,
                                index=unit_index,
                                key=f"{key_prefix}unit_{account['id']}"
                            )
                            new_currency = ""  # Empty for commodity accounts
                        else:
                            curr_index = currency_codes.index(account['currency']) if account['currency'] in currency_codes else 0
                            new_currency = st.selectbox(
                                "Currency",
                                currency_codes,
                                index=curr_index,
                                key=f"{key_prefix}currency_{account['id']}"
                            )
                            new_commodity = None
                            new_unit = None

                    # Update button
                    if st.button(f"💾 Update Account", key=f"{key_prefix}update_btn_{account['id']}", width="stretch"):
                        if new_type == "Commodity":
                            # Auto-generate name for commodity accounts with unit
                            auto_name = f"{new_commodity} ({new_unit})"
                            db.update_account(account['id'], auto_name, new_owner, new_type, "", new_commodity)
                            st.success(f"Account updated!")
                            st.rerun()
                        else:
                            if new_name:
                                db.update_account(account['id'], new_name, new_owner, new_type, new_currency, None)
                                st.success(f"Account updated!")
                                st.rerun()
                            else:
                                st.error("Please enter an account name")

                    st.divider()

                    # Remove account button
                    if st.button(f"🗑️ Remove {account['name']}", key=f"{key_prefix}remove_btn_{account['id']}", width="stretch", type="secondary"):
                        db.delete_account(account['id'])
                        st.success(f"Account '{account['name']}' removed!")
                        st.rerun()

            st.write("")  # Add spacing between owners
    else:
        st.warning("No accounts found!")

    st.divider()

    # Add new account section
    st.subheader("Add New Account")

    if not owner_names:
        st.warning("Please add at least one owner first in the Owners page!")
    else:
        col1, col2 = st.columns(2)

        # Initialize variables
        account_name = ""
        currency = ""
        selected_commodity = None
        auto_account_name = None
        selected_commodity = None
        
        with col1:
            # Account type selector first to determine what to show
            account_type = st.selectbox("Account Type", ["Bank", "Investment", "Pension", "Commodity", "Other"], key=f"{key_prefix}add_account_type")
            owner = st.selectbox("Owner", owner_names, key=f"{key_prefix}add_account_owner")

        with col2:
            # Show currency or commodity dropdown based on account type
            if account_type == "Commodity":
                commodity_names = [c['name'] for c in commodity_list]
                if commodity_names:
                    selected_commodity = st.selectbox("Commodity", commodity_names, key=f"{key_prefix}add_account_commodity")
                    selected_unit = st.selectbox("Unit", UNIT_OPTIONS, index=1, key=f"{key_prefix}add_account_unit")  # Default to "ounce"
                    # Auto-generate account name with unit
                    auto_account_name = f"{selected_commodity} ({selected_unit})"
                    st.text_input("Account Name", value=auto_account_name, key=f"{key_prefix}add_account_name_display", disabled=True, help="Auto-generated for commodity accounts")
                else:
                    st.warning("No commodities available. Please add commodities first!")
                    selected_unit = None
            else:
                account_name = st.text_input("Account Name", placeholder="e.g., TD Chequing", key=f"{key_prefix}add_account_name")
                currency = st.selectbox("Currency", currency_codes, key=f"{key_prefix}add_account_currency")
                selected_unit = None

        # Add button
        if st.button("➕ Add Account", width="stretch", type="primary", key=f"{key_prefix}add_account_btn"):
            if account_type == "Commodity":
                if selected_commodity and auto_account_name:
                    db.add_account(auto_account_name, owner, account_type, "", selected_commodity)
                    st.session_state.account_added = True
                    st.session_state.added_account_name = auto_account_name
                    st.rerun()
                else:
                    st.error("Please select a commodity")
            else:
                if account_name:
                    db.add_account(account_name, owner, account_type, currency)
                    st.session_state.account_added = True
                    st.session_state.added_account_name = account_name
                    st.rerun()
                else:
                    st.error("Please enter an account name")


# Page: Update Balances
def page_update_balances():
    accounts = db.get_accounts()

    if not accounts:
        st.warning("No accounts found. Please add accounts first!")
        return

    current_date = date.today()
    month_names = MONTH_NAMES

    # Initialize session state for dialog
    if 'show_save_dialog' not in st.session_state:
        st.session_state.show_save_dialog = False
    if 'save_snapshot_data' not in st.session_state:
        st.session_state.save_snapshot_data = None
    if 'show_delete_dialog' not in st.session_state:
        st.session_state.show_delete_dialog = False
    if 'delete_snapshot_date' not in st.session_state:
        st.session_state.delete_snapshot_date = None

    # Show success message if save was just completed
    if st.session_state.get('snapshot_saved', False):
        saved_month = st.session_state.get('saved_month_name', '')
        saved_year = st.session_state.get('saved_year', '')
        st.toast(f"Snapshot saved successfully for {saved_month} {saved_year}!", icon="💰")
        # Clear the flag
        st.session_state.snapshot_saved = False

    # Get most recent 3 months with actual snapshot data
    snapshot_dates = db.get_all_snapshot_dates()

    prev_months = []
    prev_month_data = {}

    if snapshot_dates:
        # Sort snapshot dates in descending order and take the most recent 3
        recent_dates = sorted(snapshot_dates, reverse=True)[:3]

        for snapshot_date_str in recent_dates:
            prev_date = date.fromisoformat(snapshot_date_str)
            prev_months.append(prev_date)

            # Get snapshots for this month
            prev_snapshots = db.get_snapshots_by_date(prev_date)
            for snap in prev_snapshots:
                if snap['account_id'] not in prev_month_data:
                    prev_month_data[snap['account_id']] = {}
                prev_month_data[snap['account_id']][prev_date] = snap['balance']

    # Top section: Historical balances table
    st.subheader("📊 Account Balance History (Most recent 3 months)")

    # Create table data grouped by owner
    owners = db.get_owners()
    owner_names = [owner['name'] for owner in owners]

    table_data = []
    for account in accounts:
        # For commodity accounts, show commodity name; otherwise show currency
        is_commodity = account['account_type'] == "Commodity"
        display_currency = account.get('commodity', account['currency']) if is_commodity else account['currency']
        
        # Extract unit for commodity accounts
        unit = ""
        if is_commodity:
            account_name = account['name']
            if "(" in account_name and ")" in account_name:
                unit = account_name[account_name.rfind("(")+1:account_name.rfind(")")]
        
        row = {
            'Owner': account['owner'],
            'Account': account['name'],
            'Currency': display_currency,
        }

        # Add previous 3 months with unit or currency symbol
        for prev_date in reversed(prev_months):  # Show oldest to newest
            month_label = prev_date.strftime("%b %Y")
            if account['id'] in prev_month_data and prev_date in prev_month_data[account['id']]:
                balance_value = prev_month_data[account['id']][prev_date]
                if is_commodity and unit:
                    row[month_label] = f"{balance_value:,.2f} {unit}"
                else:
                    currency_symbol = get_currency_symbol(account['currency'])
                    row[month_label] = f"{currency_symbol}{balance_value:,.2f}"
            else:
                row[month_label] = "N/A"

        table_data.append(row)

    # Display table with previous months (read-only)
    if table_data:
        render_data_table(table_data)

    st.divider()

    # Month/Year selector section
    st.subheader("📅 Update Monthly Balances")

    col1, col2, col_warning = st.columns([2, 2, 4])

    with col1:
        selected_year = st.selectbox(
            "Year",
            options=list(range(current_date.year, current_date.year - 10, -1)),
            index=0
        )

    with col2:
        # Create months in descending order (Dec to Jan)
        months_desc = list(range(12, 0, -1))
        selected_month = st.selectbox(
            "Month",
            options=months_desc,
            format_func=lambda x: month_names[x - 1],
            index=months_desc.index(current_date.month)
        )

    # Create snapshot date as first day of selected month
    snapshot_date = date(selected_year, selected_month, 1)

    # Check if future date
    if snapshot_date > current_date:
        with col_warning:
            st.error("❌ Cannot create snapshots for future months!")
        return

    # Check if snapshot already exists and show alert
    snapshot_exists = db.snapshot_exists_for_date(snapshot_date)
    if snapshot_exists:
        with col_warning:
            st.warning(f"⚠️ Snapshot exists for {month_names[selected_month - 1]} {selected_year}. Saving will overwrite it.")

    st.divider()

    # Display existing snapshot if it exists
    if snapshot_exists:
        existing_snapshots = db.get_snapshots_by_date(snapshot_date)
        if existing_snapshots:
            st.subheader(f"📋 Existing Snapshot for {month_names[selected_month - 1]} {selected_year}")

            # Get base currency (default to first enabled currency)
            default_currency = get_default_currency()
            base_currency = st.session_state.get("base_currency", default_currency)
            currency_symbol = get_currency_symbol(base_currency)

            # Get exchange rates
            rates = json.loads(existing_snapshots[0]["exchange_rates"]) if existing_snapshots[0].get("exchange_rates") else {}

            # Calculate total net worth
            total = calculate_total_net_worth(existing_snapshots, base_currency)

            st.markdown(f"**Total Net Worth:** `{currency_symbol}{total:,.2f}` ({base_currency})")

            # Display snapshots grouped by owner
            log_entries = []
            for owner_name in owner_names:
                owner_snapshots = [s for s in existing_snapshots if s['owner'] == owner_name]

                if owner_snapshots:
                    log_entries.append(f"  **{owner_name}:**")

                    for snapshot in owner_snapshots:
                        converted_value = get_converted_value(
                            snapshot["balance"],
                            snapshot["currency"],
                            base_currency,
                            rates
                        )

                        # Check if this is a commodity account
                        is_commodity = snapshot["account_type"] == "Commodity"
                        
                        if is_commodity:
                            # For commodities, extract unit from account name
                            account_name = snapshot["name"]
                            unit = "units"
                            if "(" in account_name and ")" in account_name:
                                unit = account_name[account_name.rfind("(")+1:account_name.rfind(")")]
                            
                            # Show balance with unit instead of currency symbol
                            commodity_name = snapshot.get("commodity", snapshot["currency"])
                            entry = (
                                f"    • {snapshot['name']} ({snapshot['account_type']}): "
                                f"`{snapshot['balance']:,.2f} {unit}` {commodity_name}"
                            )
                        else:
                            # For regular accounts, show currency symbol
                            acc_symbol = get_currency_symbol(snapshot['currency'])
                            entry = (
                                f"    • {snapshot['name']} ({snapshot['account_type']}): "
                                f"`{acc_symbol}{snapshot['balance']:,.2f}` {snapshot['currency']}"
                            )
                        
                        if snapshot['currency'] != base_currency:
                            entry += f" = `{currency_symbol}{converted_value:,.2f}` {base_currency}"

                        log_entries.append(entry)

            # Display all log entries
            st.markdown("\n".join(log_entries))

            st.divider()

    # Fetch exchange rates for the selected date
    enabled_currencies = db.get_currency_codes()
    
    # If only one currency is enabled, no need to fetch exchange rates
    if len(enabled_currencies) == 1:
        # Create a simple rate dictionary with the single currency
        single_currency = enabled_currencies[0]
        exchange_rates = {f"{single_currency}_{single_currency}": 1.0}
    else:
        # Multiple currencies - fetch exchange rates from API
        with st.spinner("Fetching exchange rates..."):
            exchange_rates = CurrencyConverter.get_all_cross_rates(enabled_currencies, snapshot_date.isoformat())

        if not exchange_rates:
            st.warning("⚠️ Unable to fetch live exchange rates. Using fallback rates.")
            exchange_rates = CurrencyConverter._get_fallback_rates(enabled_currencies)
            if not exchange_rates:
                st.error("Unable to generate exchange rates. Please try again later.")
                return

    # Get existing snapshot data if it exists for pre-filling the form
    existing_snapshot_data = {}
    if snapshot_exists:
        existing_snapshots = db.get_snapshots_by_date(snapshot_date)
        for snap in existing_snapshots:
            existing_snapshot_data[snap['account_id']] = snap['balance']

    # Balance entry form - grouped by owner
    with st.form("balance_form"):
        st.write(f"**Enter Balances for {month_names[selected_month - 1]} {selected_year}**")

        balances = {}

        # Group accounts by owner
        for owner_name in owner_names:
            owner_accounts = [acc for acc in accounts if acc['owner'] == owner_name]

            if owner_accounts:
                st.markdown(f"### {owner_name}")

                # Create 2-column layout for accounts
                cols_per_row = 2
                for i in range(0, len(owner_accounts), cols_per_row):
                    cols = st.columns(cols_per_row)

                    for j, col in enumerate(cols):
                        idx = i + j
                        if idx < len(owner_accounts):
                            account = owner_accounts[idx]
                            with col:
                                # Priority: 1) Existing snapshot for this month, 2) Previous month's balance, 3) 0.0
                                default_val = 0.0

                                # Check if existing snapshot has this account
                                if account['id'] in existing_snapshot_data:
                                    default_val = float(existing_snapshot_data[account['id']])
                                # Otherwise, use previous month's balance
                                elif prev_months and account['id'] in prev_month_data:
                                    most_recent = prev_months[0]  # Most recent previous month
                                    if most_recent in prev_month_data[account['id']]:
                                        default_val = float(prev_month_data[account['id']][most_recent])

                                # Determine label based on account type
                                is_commodity = account['account_type'] == "Commodity"
                                if is_commodity:
                                    # Extract unit from account name
                                    account_name = account['name']
                                    unit = "units"
                                    if "(" in account_name and ")" in account_name:
                                        unit = account_name[account_name.rfind("(")+1:account_name.rfind(")")]
                                    commodity_name = account.get('commodity', account['currency'])
                                    label = f"{account['name']} ({unit})"
                                else:
                                    label = f"{account['name']} ({account['currency']})"

                                balance = st.number_input(
                                    label,
                                    min_value=0.0,
                                    value=default_val,
                                    step=100.0,
                                    format="%.2f",
                                    key=f"balance_{account['id']}"
                                )
                                balances[account['id']] = balance

                st.write("")  # Spacing between owners

        st.divider()
        submit = st.form_submit_button("💾 Save Snapshot", width="stretch")

        if submit:
            # Validate that at least one balance is entered
            if all(balance == 0 for balance in balances.values()):
                st.error("Please enter at least one non-zero balance")
            else:
                # Store data in session state for confirmation dialog
                st.session_state.save_snapshot_data = {
                    'snapshot_date': snapshot_date,
                    'balances': balances,
                    'exchange_rates': exchange_rates,
                    'snapshot_exists': snapshot_exists,
                    'month_name': month_names[selected_month - 1],
                    'year': selected_year
                }
                st.session_state.show_save_dialog = True
                st.rerun()

    # Show confirmation dialog
    if st.session_state.show_save_dialog and st.session_state.save_snapshot_data:
        data = st.session_state.save_snapshot_data

        @st.dialog("Confirm Save")
        def confirm_save():
            st.write(f"**Save snapshot for {data['month_name']} {data['year']}?**")

            if data['snapshot_exists']:
                st.warning("⚠️ This will overwrite the existing snapshot.")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("💾 Save", type="primary", width="stretch"):
                    # If snapshot exists, delete it first (overwrite)
                    if data['snapshot_exists']:
                        existing_snapshots = db.get_snapshots_by_date(data['snapshot_date'])
                        for snapshot in existing_snapshots:
                            db.delete_snapshot(snapshot['id'])

                    # Save new snapshots
                    for account_id, balance in data['balances'].items():
                        db.add_snapshot(data['snapshot_date'], account_id, balance, data['exchange_rates'])

                    # Set success flag to show message after rerun
                    st.session_state.snapshot_saved = True
                    st.session_state.saved_month_name = data['month_name']
                    st.session_state.saved_year = data['year']

                    # Clear dialog state
                    st.session_state.show_save_dialog = False
                    st.session_state.save_snapshot_data = None

                    st.rerun()

            with col2:
                if st.button("❌ Cancel", width="stretch"):
                    st.session_state.show_save_dialog = False
                    st.session_state.save_snapshot_data = None
                    st.rerun()

        confirm_save()
    
    # Show delete confirmation dialog
    if st.session_state.show_delete_dialog and st.session_state.delete_snapshot_date:
        delete_date = st.session_state.delete_snapshot_date
        
        @st.dialog("Confirm Delete")
        def confirm_delete():
            month_name = month_names[delete_date.month - 1]
            year = delete_date.year
            
            st.write(f"**Delete snapshot for {month_name} {year}?**")
            st.warning("⚠️ This action cannot be undone. All balance data for this month will be permanently deleted.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🗑️ Delete", type="primary", use_container_width=True):
                    # Delete all snapshots for this date
                    db.delete_snapshots_by_date(delete_date)
                    
                    # Set success flag
                    st.session_state.snapshot_deleted = True
                    st.session_state.deleted_month_name = month_name
                    st.session_state.deleted_year = year
                    
                    # Clear dialog state
                    st.session_state.show_delete_dialog = False
                    st.session_state.delete_snapshot_date = None
                    
                    st.rerun()
            
            with col2:
                if st.button("❌ Cancel", use_container_width=True):
                    st.session_state.show_delete_dialog = False
                    st.session_state.delete_snapshot_date = None
                    st.rerun()
        
        confirm_delete()


# Page: History
def page_history():
    st.caption("View all snapshot entries by year")

    snapshot_dates = db.get_all_snapshot_dates()

    if not snapshot_dates:
        st.info("No snapshots yet. Create your first monthly snapshot!")
        return

    # Extract unique years from snapshot dates
    years = sorted(list(set([datetime.fromisoformat(d).year for d in snapshot_dates])), reverse=True)

    # Year selector
    col1, _ = st.columns([2, 6])
    with col1:
        selected_year = st.selectbox(
            "Select Year",
            options=years,
            index=0
        )

    st.divider()

    # Get base currency (default to first enabled currency)
    default_currency = get_default_currency()
    base_currency = st.session_state.get("base_currency", default_currency)
    currency_symbol = get_currency_symbol(base_currency)

    # Month names
    month_names = MONTH_NAMES

    # Filter snapshots for selected year and organize by month
    year_snapshots = {}
    for snapshot_date_str in snapshot_dates:
        snapshot_dt = datetime.fromisoformat(snapshot_date_str)
        if snapshot_dt.year == selected_year:
            month_num = snapshot_dt.month
            year_snapshots[month_num] = date.fromisoformat(snapshot_date_str)

    # Display log entries for each month in descending order (Current month → Jan)
    st.markdown(f"### 📅 {selected_year} Snapshot Log")
    st.markdown("---")

    # Determine starting month
    current_date = date.today()
    if selected_year == current_date.year:
        # For current year, start from current month
        start_month = current_date.month
    else:
        # For past years, start from December
        start_month = 12

    for month_num in range(start_month, 0, -1):
        if month_num in year_snapshots:
            snapshot_date = year_snapshots[month_num]
            snapshots = db.get_snapshots_by_date(snapshot_date)

            if snapshots:
                # Get exchange rates
                rates = json.loads(snapshots[0]["exchange_rates"]) if snapshots[0].get("exchange_rates") else {}

                # Calculate total net worth
                total = calculate_total_net_worth(snapshots, base_currency)

                # Display month header
                st.markdown(f"#### 📌 {month_names[month_num - 1]} {selected_year}")
                st.markdown(f"**Total Net Worth:** `{currency_symbol}{total:,.2f}` ({base_currency})")

                # Group snapshots by owner for better organization
                owners = db.get_owners()
                owner_names = [owner['name'] for owner in owners]

                # Display snapshots grouped by owner
                log_entries = []
                for owner_name in owner_names:
                    owner_snapshots = [s for s in snapshots if s['owner'] == owner_name]

                    if owner_snapshots:
                        log_entries.append(f"  **{owner_name}:**")

                        for snapshot in owner_snapshots:
                            converted_value = get_converted_value(
                                snapshot["balance"],
                                snapshot["currency"],
                                base_currency,
                                rates
                            )

                            # Check if this is a commodity account
                            is_commodity = snapshot["account_type"] == "Commodity"
                            
                            if is_commodity:
                                # For commodities, extract unit from account name
                                account_name = snapshot["name"]
                                unit = "units"
                                if "(" in account_name and ")" in account_name:
                                    unit = account_name[account_name.rfind("(")+1:account_name.rfind(")")]
                                
                                # Show balance with unit instead of currency symbol
                                commodity_name = snapshot.get("commodity", snapshot["currency"])
                                entry = (
                                    f"    • {snapshot['name']} ({snapshot['account_type']}): "
                                    f"`{snapshot['balance']:,.2f} {unit}` {commodity_name}"
                                )
                            else:
                                # For regular accounts, show currency symbol
                                acc_symbol = get_currency_symbol(snapshot['currency'])
                                entry = (
                                    f"    • {snapshot['name']} ({snapshot['account_type']}): "
                                    f"`{acc_symbol}{snapshot['balance']:,.2f}` {snapshot['currency']}"
                                )
                            
                            if snapshot['currency'] != base_currency:
                                entry += f" = `{currency_symbol}{converted_value:,.2f}` {base_currency}"

                            log_entries.append(entry)

                # Display all log entries
                st.markdown("\n".join(log_entries))

                # Delete button for this month
                col_delete, _ = st.columns([2, 6])
                with col_delete:
                    if st.button(f"🗑️ Delete {month_names[month_num - 1]}", key=f"delete_{month_num}"):
                        if st.session_state.get(f"confirm_delete_{month_num}", False):
                            db.delete_snapshots_by_date(snapshot_date)
                            st.success(f"Deleted snapshot for {month_names[month_num - 1]} {selected_year}!")
                            st.session_state[f"confirm_delete_{month_num}"] = False
                            st.rerun()
                        else:
                            st.session_state[f"confirm_delete_{month_num}"] = True
                            st.warning("⚠️ Click again to confirm deletion")

                st.markdown("---")
        else:
            # No snapshot for this month
            st.markdown(f"#### ⚪ {month_names[month_num - 1]} {selected_year}")
            st.markdown("  *No snapshot recorded*")
            st.markdown("---")


# Page: Exchange Rates
def page_exchange_rates():
    st.title("💹 Exchange Rates")
    st.caption("View today's live exchange rates for supported currencies and commodities")
    
    # Check if multiple currencies exist
    if not has_multiple_currencies():
        st.info("💡 Exchange rates are not available with the current configuration.")
        st.write("To enable exchange rate functionality, you need:")
        st.write("- At least 1 currency AND 1 commodity, OR")
        st.write("- At least 2 currencies (without commodities), OR")
        st.write("- More than 2 currencies AND more than 2 commodities")
        st.write("\nConfigure currencies and commodities in the settings to enable this feature.")
        return

    # Date selector - allows viewing historical rates
    current_date = date.today()
    selected_date = st.date_input(
        "Select Date",
        value=current_date,
        max_value=current_date,
        disabled=False,
        help="Select a date to view historical exchange rates and commodity prices. Frankfurter API supports historical data from 1999 onwards."
    )
    
    # Convert date to string format for API (YYYY-MM-DD)
    date_str = selected_date.strftime('%Y-%m-%d') if selected_date != current_date else None

    st.divider()

    # Fetch exchange rates for selected date
    with st.spinner(f"Fetching exchange rates for {selected_date.strftime('%B %d, %Y')}..."):
        enabled_currencies = db.get_currency_codes()
        exchange_rates = CurrencyConverter.get_all_cross_rates(enabled_currencies, date=date_str)

    if not exchange_rates:
        st.error("⚠️ Unable to fetch live exchange rates from API. Using fallback rates.")
        st.info("💡 Fallback rates are approximate values. For accurate rates, please check your internet connection and try again.")
        # Get fallback rates
        exchange_rates = CurrencyConverter._get_fallback_rates(enabled_currencies)
        if not exchange_rates:
            st.error("Unable to generate exchange rates. Please try again later.")
            return
        rates_source = "Fallback"
    else:
        rates_source = "Live API"

    date_label = "Today's live" if selected_date == current_date else "Historical"
    st.success(f"✅ {date_label} exchange rates for {selected_date.strftime('%B %d, %Y')} ({rates_source})")

    st.divider()

    # Display exchange rates dynamically for all saved currencies
    st.subheader("💱 Currency Exchange Rates")
    
    # Get all saved currencies with their details
    currencies = db.get_currencies()
    
    if len(currencies) < 2:
        st.info("Add more currencies to see exchange rates between them.")
    else:
        # Create a grid layout based on number of currencies
        num_currencies = len(currencies)
        
        # Display rates in a table format
        st.write("**All Currency Pairs:**")
        
        # Create columns for better layout
        cols_per_row = 3
        rate_pairs = []
        
        # Generate all currency pairs
        for i, from_curr in enumerate(currencies):
            for j, to_curr in enumerate(currencies):
                if i != j:  # Don't show same currency conversions
                    from_code = from_curr['code']
                    to_code = to_curr['code']
                    rate_key = f"{from_code}_{to_code}"
                    rate_value = exchange_rates.get(rate_key, "N/A")
                    
                    rate_pairs.append({
                        'from': from_code,
                        'from_emoji': from_curr['flag_emoji'],
                        'to': to_code,
                        'to_emoji': to_curr['flag_emoji'],
                        'rate': rate_value
                    })
        
        # Display in columns
        for idx in range(0, len(rate_pairs), cols_per_row):
            cols = st.columns(cols_per_row)
            for col_idx, col in enumerate(cols):
                pair_idx = idx + col_idx
                if pair_idx < len(rate_pairs):
                    pair = rate_pairs[pair_idx]
                    with col:
                        if isinstance(pair['rate'], (int, float)):
                            st.metric(
                                f"{pair['from_emoji']} {pair['from']} → {pair['to_emoji']} {pair['to']}",
                                f"{pair['rate']:.4f}"
                            )
                        else:
                            st.metric(
                                f"{pair['from_emoji']} {pair['from']} → {pair['to_emoji']} {pair['to']}",
                                pair['rate']
                            )

    st.divider()

    # Display commodities section with prices
    st.subheader("🥇 Commodity Prices")
    
    commodities = db.get_commodities()
    
    if not commodities:
        st.info("No commodities configured yet. Add commodities in the **Commodities** settings.")
    else:
        # Unit selector dropdown
        unit_options = ["ounce", "gram", "kilogram", "pound", "ton"]
        
        # Initialize session state for selected unit if not exists
        if "commodity_display_unit" not in st.session_state:
            st.session_state.commodity_display_unit = "ounce"
        
        # Unit selector
        col_unit1, col_unit2 = st.columns([1, 3])
        with col_unit1:
            selected_unit = st.selectbox(
                "Display Unit",
                options=unit_options,
                index=unit_options.index(st.session_state.commodity_display_unit),
                key="page_unit_selector",
                help="Select the unit for displaying commodity prices"
            )
        
        # Update session state if unit changed
        if selected_unit != st.session_state.commodity_display_unit:
            st.session_state.commodity_display_unit = selected_unit
            st.rerun()
        
        st.write("")  # Add spacing
        
        # Fetch commodity prices for selected date
        commodity_names = [c['name'] for c in commodities]
        
        with st.spinner(f"Fetching commodity prices for {selected_date.strftime('%B %d, %Y')}..."):
            commodity_prices = CurrencyConverter.get_commodity_prices(commodity_names, enabled_currencies, date=date_str)
        
        if commodity_prices:
            st.write(f"**Current Commodity Prices (per {selected_unit}):**")
            
            # Display each commodity with its prices in different currencies
            for commodity in commodities:
                commodity_name = commodity['name']
                
                if commodity_name in commodity_prices:
                    st.markdown(f"### {commodity['symbol']} {commodity_name}")
                    
                    # Display prices in columns
                    cols_per_row = min(3, len(enabled_currencies))
                    prices = commodity_prices[commodity_name]
                    
                    currency_list = list(prices.keys())
                    for idx in range(0, len(currency_list), cols_per_row):
                        cols = st.columns(cols_per_row)
                        for col_idx, col in enumerate(cols):
                            curr_idx = idx + col_idx
                            if curr_idx < len(currency_list):
                                currency_code = currency_list[curr_idx]
                                # Get base price (per ounce from API)
                                base_price = prices[currency_code]
                                
                                # Convert price to selected unit
                                converted_price = CurrencyConverter.convert_commodity_unit(
                                    base_price,
                                    "ounce",  # API returns prices per ounce
                                    selected_unit
                                )
                                
                                # Get currency details for emoji
                                curr_details = db.get_currency_by_code(currency_code)
                                emoji = curr_details['flag_emoji'] if curr_details else ""
                                
                                with col:
                                    st.metric(
                                        f"{emoji} {currency_code}",
                                        f"{converted_price:,.2f}",
                                        help=f"Price per {selected_unit} in {currency_code}"
                                    )
                    
                    st.write("")  # Spacing
        else:
            st.warning("⚠️ Unable to fetch commodity prices. Using configured commodities only.")
            st.write("**Configured Commodities:**")
            
            # Display commodities in a grid without prices
            cols_per_row = 3
            for idx in range(0, len(commodities), cols_per_row):
                cols = st.columns(cols_per_row)
                for col_idx, col in enumerate(cols):
                    comm_idx = idx + col_idx
                    if comm_idx < len(commodities):
                        commodity = commodities[comm_idx]
                        with col:
                            st.markdown(
                                f"""
                                <div style="padding: 1rem; border-radius: 0.5rem; background-color: {commodity['color']}20; border: 2px solid {commodity['color']};">
                                    <div style="font-size: 2rem; text-align: center;">{commodity['symbol']}</div>
                                    <div style="font-weight: bold; text-align: center; margin-top: 0.5rem;">{commodity['name']}</div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
        
        st.info("💡 **Note:** Commodity prices are fetched from live market data and displayed per troy ounce by default. Use the unit selector above to view prices in different units (gram, kilogram, pound, ton). When multiple currencies are configured, prices are calculated using current exchange rates.")

    st.divider()

    # Exchange rate information
    with st.expander("ℹ️ About Exchange Rates & Commodity Prices"):
        st.write("""
        **Source:** Exchange rates and commodity prices are fetched from the Frankfurter API (v2)

        **Update Frequency:** Rates are updated daily

        **Historical Data:** You can view historical exchange rates and commodity prices by selecting a past date.
        The Frankfurter API provides historical data from 1999 onwards for currencies, and from 2005 onwards for Gold (XAU),
        2019 onwards for Silver (XAG), and 2026 onwards for Platinum (XPT) and Palladium (XPD).
        
        **Weekend/Holiday Handling:** When you select a weekend or holiday date, the API automatically returns the last working day's prices.

        **Commodity Pricing:**
        - All commodity prices from the API are per **troy ounce** (the standard unit for precious metals)
        - 1 troy ounce = 31.1035 grams
        - When you change the display unit, prices are automatically converted from troy ounces
        - For multiple currencies, the base price is fetched from the API, then converted to other currencies using exchange rates

        **Usage:** These rates are automatically used when calculating net worth across different currencies

        **Supported Commodities:** Gold (XAU), Silver (XAG), Platinum (XPT), and Palladium (XPD) are supported directly through the Frankfurter API.
        """)


# Page: Currencies
def page_currencies(key_prefix=""):
    # Currency metadata (Frankfurter API supported currencies with flags)
    AVAILABLE_CURRENCIES = {
        "AUD": {"name": "Australian Dollar", "flag": "🇦🇺"},
        "BGN": {"name": "Bulgarian Lev", "flag": "🇧🇬"},
        "BRL": {"name": "Brazilian Real", "flag": "🇧🇷"},
        "CAD": {"name": "Canadian Dollar", "flag": "🇨🇦"},
        "CHF": {"name": "Swiss Franc", "flag": "🇨🇭"},
        "CNY": {"name": "Chinese Yuan", "flag": "🇨🇳"},
        "CZK": {"name": "Czech Koruna", "flag": "🇨🇿"},
        "DKK": {"name": "Danish Krone", "flag": "🇩🇰"},
        "EUR": {"name": "Euro", "flag": "🇪🇺"},
        "GBP": {"name": "British Pound", "flag": "🇬🇧"},
        "HKD": {"name": "Hong Kong Dollar", "flag": "🇭🇰"},
        "HUF": {"name": "Hungarian Forint", "flag": "🇭🇺"},
        "IDR": {"name": "Indonesian Rupiah", "flag": "🇮🇩"},
        "ILS": {"name": "Israeli Shekel", "flag": "🇮🇱"},
        "INR": {"name": "Indian Rupee", "flag": "🇮🇳"},
        "ISK": {"name": "Icelandic Króna", "flag": "🇮🇸"},
        "JPY": {"name": "Japanese Yen", "flag": "🇯🇵"},
        "KRW": {"name": "South Korean Won", "flag": "🇰🇷"},
        "MXN": {"name": "Mexican Peso", "flag": "🇲🇽"},
        "MYR": {"name": "Malaysian Ringgit", "flag": "🇲🇾"},
        "NOK": {"name": "Norwegian Krone", "flag": "🇳🇴"},
        "NZD": {"name": "New Zealand Dollar", "flag": "🇳🇿"},
        "PHP": {"name": "Philippine Peso", "flag": "🇵🇭"},
        "PLN": {"name": "Polish Złoty", "flag": "🇵🇱"},
        "RON": {"name": "Romanian Leu", "flag": "🇷🇴"},
        "RUB": {"name": "Russian Ruble", "flag": "🇷🇺"},
        "SEK": {"name": "Swedish Krona", "flag": "🇸🇪"},
        "SGD": {"name": "Singapore Dollar", "flag": "🇸🇬"},
        "THB": {"name": "Thai Baht", "flag": "🇹🇭"},
        "TRY": {"name": "Turkish Lira", "flag": "🇹🇷"},
        "USD": {"name": "US Dollar", "flag": "🇺🇸"},
        "ZAR": {"name": "South African Rand", "flag": "🇿🇦"},
    }

    # Theme-friendly colors (work well in both light and dark mode)
    COLOR_OPTIONS = {
        "Crimson Red": "#DC143C",
        "Navy Blue": "#003366",
        "Dark Orange": "#FF8C00",
        "Forest Green": "#228B22",
        "Purple": "#8B008B",
        "Teal": "#008080",
        "Maroon": "#800000",
        "Olive": "#808000",
        "Steel Blue": "#4682B4",
    }

    # Show success message if currency was just added
    if st.session_state.get('currency_added', False):
        currency_code = st.session_state.get('added_currency_code', '')
        st.toast(f"Currency '{currency_code}' added successfully!", icon="💱")
        st.session_state.currency_added = False

    # Get enabled currencies
    enabled_currencies = db.get_currencies()
    enabled_codes = [c['code'] for c in enabled_currencies]
    currency_count = len(enabled_currencies)

    st.info(f"**{currency_count}/9 currencies enabled** (Minimum: 1, Maximum: 9)")

    st.divider()

    # Show enabled currencies with inline editing and removal
    st.subheader("Enabled Currencies")

    if enabled_currencies:
        for curr in enabled_currencies:
            currency_name = AVAILABLE_CURRENCIES.get(curr['code'], {}).get('name', curr['code'])
            is_in_use = db.currency_in_use(curr['code'])
            in_use_text = "Yes" if is_in_use else "No"

            # Create expandable section for each currency
            with st.expander(f"{curr['flag_emoji']} {curr['code']} - {currency_name}", expanded=False):
                st.write(f"**In Use:** {in_use_text}")

                st.write("**Change Color:**")
                col1, col2, col3 = st.columns([2, 3, 2])

                with col1:
                    # Current color preview - aligned with dropdown center
                    st.markdown("<div style='text-align: center;'>Current</div>", unsafe_allow_html=True)
                    st.markdown(f"""
                        <div style="
                            width: 40px;
                            height: 40px;
                            background-color: {curr['color']};
                            border-radius: 50%;
                            border: 2px solid #666;
                            margin-left: auto;
                            margin-right: auto;
                        "></div>
                    """, unsafe_allow_html=True)

                with col2:
                    # Color selector
                    new_color = st.selectbox(
                        "Select Color",
                        list(COLOR_OPTIONS.keys()),
                        key=f"{key_prefix}color_select_{curr['id']}"
                    )

                with col3:
                    # New color preview - aligned with dropdown center
                    st.markdown("<div style='text-align: center;'>New</div>", unsafe_allow_html=True)
                    new_color_value = COLOR_OPTIONS[new_color]
                    st.markdown(f"""
                        <div style="
                            width: 40px;
                            height: 40px;
                            background-color: {new_color_value};
                            border-radius: 50%;
                            border: 2px solid #666;
                            margin-left: auto;
                            margin-right: auto;
                        "></div>
                    """, unsafe_allow_html=True)

                # Update button
                if st.button(f"🎨 Update Color", key=f"{key_prefix}update_btn_{curr['id']}", width="stretch"):
                    success = db.update_currency_color(curr['id'], new_color_value)
                    if success:
                        st.success(f"Color updated!")
                        st.rerun()
                    else:
                        st.error("Failed to update color")

                st.divider()

                # Remove currency button
                if currency_count <= 1:
                    st.info("Cannot remove the last currency. At least one currency is required.")
                elif is_in_use:
                    st.warning(f"Cannot remove {curr['code']} - it's currently used by existing accounts.")
                else:
                    if st.button(f"🗑️ Remove {curr['code']}", key=f"{key_prefix}remove_btn_{curr['id']}", width="stretch", type="secondary"):
                        success = db.delete_currency(curr['id'])
                        if success:
                            st.success(f"Currency {curr['code']} removed!")
                            st.rerun()
                        else:
                            st.error("Failed to remove currency")
    else:
        st.warning("No currencies enabled!")

    # Add new currency section
    if currency_count < 9:  # Only allow adding if less than 9 currencies
        st.subheader("Add New Currency")

        # Filter out already enabled currencies
        available_to_add = {k: v for k, v in AVAILABLE_CURRENCIES.items() if k not in enabled_codes}

        if available_to_add:
            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                # Currency selector
                currency_options = [f"{v['flag']} {k} - {v['name']}" for k, v in sorted(available_to_add.items())]
                selected = st.selectbox("Select Currency", currency_options, key=f"{key_prefix}add_currency_selector")

                # Extract currency code from selection
                selected_code = selected.split()[1] if selected else None

            with col2:
                # Color selector
                color_name = st.selectbox("Select Color", list(COLOR_OPTIONS.keys()), key=f"{key_prefix}add_color_selector")
                color_value = COLOR_OPTIONS[color_name]

            with col3:
                # Color preview - aligned with dropdown center
                st.markdown("<div style='text-align: center;'>Preview</div>", unsafe_allow_html=True)
                st.markdown(f"""
                    <div style="
                        width: 40px;
                        height: 40px;
                        background-color: {color_value};
                        border-radius: 50%;
                        border: 2px solid #666;
                        margin-left: auto;
                        margin-right: auto;
                    "></div>
                """, unsafe_allow_html=True)

            # Add button with proper spacing
            if st.button("➕ Add Currency", width="stretch", type="primary", key=f"{key_prefix}add_currency_btn"):
                if selected_code:
                    flag_emoji = AVAILABLE_CURRENCIES[selected_code]['flag']
                    db.add_currency(selected_code, flag_emoji, color_value)
                    st.session_state.currency_added = True
                    st.session_state.added_currency_code = selected_code
                    st.rerun()
        else:
            st.info("All available currencies have been added!")
    else:
        st.warning("Maximum of 9 currencies reached. Remove a currency to add a new one.")

    st.divider()

    st.info("""
**About Currencies**

- Exchange rates are fetched from the [Frankfurter API](https://frankfurter.dev/)
- Rates are effective as of the 1st of each month
- View current rates using the **Exchange Rate** tool in the sidebar
- Currencies cannot be removed if they're used by accounts
    """)


def page_commodities(key_prefix=""):
    # Commodity metadata - Only Gold and Silver are supported
    AVAILABLE_COMMODITIES = {
        "Gold": {"symbol": "🥇", "description": "Precious metal - Gold"},
        "Silver": {"symbol": "🥈", "description": "Precious metal - Silver"},
    }
    
    # Theme-friendly colors (work well in both light and dark mode)
    COLOR_OPTIONS = {
        "Gold": "#FFD700",
        "Silver": "#C0C0C0",
        "Copper": "#B87333",
        "Crimson Red": "#DC143C",
        "Navy Blue": "#003366",
        "Dark Orange": "#FF8C00",
        "Forest Green": "#228B22",
        "Purple": "#8B008B",
        "Teal": "#008080",
        "Maroon": "#800000",
        "Olive": "#808000",
        "Steel Blue": "#4682B4",
    }

    # Show success message if commodity was just added
    if st.session_state.get('commodity_added', False):
        commodity_name = st.session_state.get('added_commodity_name', '')
        st.toast(f"Commodity '{commodity_name}' added successfully!", icon="🥇")
        st.session_state.commodity_added = False

    # Get enabled commodities
    enabled_commodities = db.get_commodities()
    enabled_names = [c['name'] for c in enabled_commodities]
    commodity_count = len(enabled_commodities)

    st.info(f"**{commodity_count}/2 commodities enabled** (Minimum: 0, Maximum: 2)")

    st.divider()

    # Show enabled commodities with inline editing and removal
    st.subheader("Enabled Commodities")

    if enabled_commodities:
        for comm in enabled_commodities:
            commodity_desc = AVAILABLE_COMMODITIES.get(comm['name'], {}).get('description', comm['name'])
            is_in_use = db.commodity_in_use(comm['name'])
            in_use_text = "Yes" if is_in_use else "No"

            # Create expandable section for each commodity
            with st.expander(f"{comm['symbol']} {comm['name']} - {commodity_desc}", expanded=False):
                st.write(f"**In Use:** {in_use_text}")

                st.write("**Change Color:**")
                col1, col2, col3 = st.columns([2, 3, 2])

                with col1:
                    # Current color preview - aligned with dropdown center
                    st.markdown("<div style='text-align: center;'>Current</div>", unsafe_allow_html=True)
                    st.markdown(
                        f"<div style='width: 40px; height: 40px; background-color: {comm['color']}; "
                        f"border-radius: 50%; border: 2px solid #666; margin-left: auto; margin-right: auto;'></div>",
                        unsafe_allow_html=True
                    )

                with col2:
                    # Color selector
                    new_color = st.selectbox(
                        "Select Color",
                        list(COLOR_OPTIONS.keys()),
                        key=f"{key_prefix}color_select_{comm['id']}"
                    )

                with col3:
                    # New color preview - aligned with dropdown center
                    st.markdown("<div style='text-align: center;'>New</div>", unsafe_allow_html=True)
                    new_color_value = COLOR_OPTIONS[new_color]
                    st.markdown(
                        f"<div style='width: 40px; height: 40px; background-color: {new_color_value}; "
                        f"border-radius: 50%; border: 2px solid #666; margin-left: auto; margin-right: auto;'></div>",
                        unsafe_allow_html=True
                    )

                # Update button
                if st.button(f"🎨 Update Color", key=f"{key_prefix}update_btn_{comm['id']}", width="stretch"):
                    success = db.update_commodity_color(comm['id'], new_color_value)
                    if success:
                        st.success(f"Color updated!")
                        st.rerun()
                    else:
                        st.error("Failed to update color")

                st.divider()

                # Remove commodity button
                if is_in_use:
                    st.warning(f"Cannot remove {comm['name']} - it's currently used by existing accounts.")
                else:
                    if st.button(f"🗑️ Remove {comm['name']}", key=f"{key_prefix}remove_btn_{comm['id']}", width="stretch", type="secondary"):
                        success = db.delete_commodity(comm['id'])
                        if success:
                            st.success(f"Commodity {comm['name']} removed!")
                            st.rerun()
                        else:
                            st.error("Failed to remove commodity")
    else:
        st.warning("No commodities enabled!")

    # Add new commodity section
    if commodity_count < 2:  # Only allow adding if less than 2 commodities
        st.subheader("Add New Commodity")

        # Filter out already enabled commodities
        available_to_add = {k: v for k, v in AVAILABLE_COMMODITIES.items() if k not in enabled_names}

        if available_to_add:
            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                # Commodity selector
                commodity_options = [f"{v['symbol']} {k} - {v['description']}" for k, v in sorted(available_to_add.items())]
                selected = st.selectbox("Select Commodity", commodity_options, key=f"{key_prefix}add_commodity_selector")

                # Extract commodity name from selection
                selected_name = selected.split()[1] if selected else None

            with col2:
                # Color selector
                color_name = st.selectbox("Select Color", list(COLOR_OPTIONS.keys()), key=f"{key_prefix}add_color_selector")
                color_value = COLOR_OPTIONS[color_name]

            with col3:
                # Color preview - aligned with dropdown center
                st.markdown("<div style='text-align: center;'>Preview</div>", unsafe_allow_html=True)
                st.markdown(
                    f"<div style='width: 40px; height: 40px; background-color: {color_value}; "
                    f"border-radius: 50%; border: 2px solid #666; margin-left: auto; margin-right: auto;'></div>",
                    unsafe_allow_html=True
                )

            # Add button with proper spacing
            if st.button("➕ Add Commodity", width="stretch", type="primary", key=f"{key_prefix}add_commodity_btn"):
                if selected_name:
                    symbol = AVAILABLE_COMMODITIES[selected_name]['symbol']
                    # Default unit is 'ounce' - will be set when creating account
                    db.add_commodity(selected_name, symbol, color_value, "ounce")
                    st.session_state.commodity_added = True
                    st.session_state.added_commodity_name = selected_name
                    st.rerun()
        else:
            st.info("All available commodities have been added!")
    else:
        st.warning("Maximum of 2 commodities reached. Remove a commodity to add a new one.")

    st.divider()

    st.info("""
**About Commodities**

- Track precious and industrial metals
- Commodities can be used for investment tracking
- Colors help distinguish different commodities in charts
- Commodities cannot be removed if they're used by accounts
    """)


# Page: Settings (with tabs for Accounts, Commodities, Currencies, Owners)
def page_settings():
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
    
    # Create tabs for the five settings pages
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["🏦 Accounts", "🥇 Commodities", "💱 Currencies", "👥 Owners", "🏠 Mortgage"]
    )
    
    # Only render content in active tab to avoid key conflicts
    # Streamlit tabs render all content, so we need to ensure unique keys
    with tab1:
        page_accounts(key_prefix="accounts_")
    
    with tab2:
        page_commodities(key_prefix="commodities_")
    
    with tab3:
        page_currencies(key_prefix="currencies_")
    
    with tab4:
        page_owners(key_prefix="owners_")
    
    with tab5:
        page_mortgage_settings(key_prefix="mortgage_settings_")


# Page: Owners
def page_owners(key_prefix=""):
    # Show success message if owner was just added
    show_success_toast('owner')

    # List existing owners
    st.subheader("Existing Owners")

    owners = db.get_owners()
    owner_count = len(owners)

    if owners:
        for owner in owners:
            has_accounts = db.owner_has_accounts(owner['name'])
            has_accounts_text = "Yes" if has_accounts else "No"

            # Create expandable section for each owner
            with st.expander(f"👤 {owner['name']} - {owner['owner_type']}", expanded=False):
                st.write(f"**Has Accounts:** {has_accounts_text}")

                st.write("**Edit Owner:**")
                col1, col2 = st.columns(2)

                with col1:
                    new_name = st.text_input(
                        "Owner Name",
                        value=owner['name'],
                        key=f"{key_prefix}name_{owner['id']}"
                    )

                with col2:
                    type_options = ["Individual", "Company", "Joint/Shared", "Trust", "Other"]
                    current_index = type_options.index(owner['owner_type']) if owner['owner_type'] in type_options else 0
                    new_type = st.selectbox(
                        "Owner Type",
                        type_options,
                        index=current_index,
                        key=f"{key_prefix}type_{owner['id']}"
                    )

                # Update button
                if st.button(f"💾 Update Owner", key=f"{key_prefix}update_btn_{owner['id']}", width="stretch"):
                    if new_name:
                        try:
                            db.update_owner(owner['id'], new_name, new_type)
                            st.success(f"Owner updated!")
                            st.rerun()
                        except Exception as e:
                            if "UNIQUE constraint failed" in str(e):
                                st.error(f"Owner '{new_name}' already exists!")
                            else:
                                st.error(f"Error updating owner: {str(e)}")
                    else:
                        st.error("Please enter an owner name")

                st.divider()

                # Remove owner button
                if owner_count <= 1:
                    st.info("Cannot remove the last owner. At least one owner is required.")
                elif has_accounts:
                    st.warning(f"Cannot remove {owner['name']} - this owner has existing accounts.")
                else:
                    if st.button(f"🗑️ Remove {owner['name']}", key=f"{key_prefix}remove_btn_{owner['id']}", width="stretch", type="secondary"):
                        success = db.delete_owner(owner['id'])
                        if success:
                            st.success(f"Owner '{owner['name']}' removed!")
                            st.rerun()
                        else:
                            st.error("Failed to remove owner")
    else:
        st.warning("No owners found!")

    st.divider()

    # Add new owner section
    st.subheader("Add New Owner")

    col1, col2 = st.columns(2)

    with col1:
        owner_name = st.text_input("Owner Name", placeholder="e.g., John, Acme Corp", key=f"{key_prefix}add_owner_name")

    with col2:
        owner_type = st.selectbox("Owner Type", ["Individual", "Company", "Joint/Shared", "Trust", "Other"], key=f"{key_prefix}add_owner_type")

    # Add button
    if st.button("➕ Add Owner", width="stretch", type="primary", key=f"{key_prefix}add_owner_btn"):
        if owner_name:
            try:
                db.add_owner(owner_name, owner_type)
                st.session_state.owner_added = True
                st.session_state.added_owner_name = owner_name
                st.rerun()
            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    st.error(f"Owner '{owner_name}' already exists!")
                else:
                    st.error(f"Error adding owner: {str(e)}")
        else:
            st.error("Please enter an owner name")


# ===== TOOL BUTTON TEMPLATE =====
# Reusable template for expandable tool buttons with visual connection

def render_tool_button(icon, label, state_key, widget_renderer):
    """
    Render a tool button with arrow that expands to show a widget

    Args:
        icon: Emoji icon for the button
        label: Button label text
        state_key: Session state key for tracking open/closed state
        widget_renderer: Function to render the widget content
    """
    colors = get_theme_colors()

    # Check if widget is open
    is_open = st.session_state.get(state_key, False)
    arrow = "▼" if is_open else "▲"

    # Render button
    if st.button(f"{icon} {label} {arrow}", width="stretch", key=f"{state_key}_btn"):
        # Toggle state
        st.session_state[state_key] = not is_open
        st.rerun()

    # Render widget if open
    if is_open:
        # Visual connection using columns for indentation
        col_spacer, col_content = st.columns([0.08, 0.92])

        with col_spacer:
            # Subtle vertical line indicator
            st.markdown(f"""
                <div style="
                    width: 2px;
                    background-color: {colors['border']};
                    height: 100%;
                    min-height: 500px;
                    border-radius: 1px;
                    opacity: 0.6;
                "></div>
            """, unsafe_allow_html=True)

        with col_content:
            # Render the actual widget content
            widget_renderer()


# ===== EXCHANGE RATE WIDGET =====

def render_exchange_rate_widget_inline():
    """Exchange Rate widget content"""
    
    # Check if multiple currencies exist
    if not has_multiple_currencies():
        st.info("💡 Exchange rates are not available with the current configuration.")
        st.write("To enable exchange rate functionality, you need:")
        st.write("- At least 1 currency AND 1 commodity, OR")
        st.write("- At least 2 currencies (without commodities), OR")
        st.write("- More than 2 currencies AND more than 2 commodities")
        st.write("\nConfigure currencies and commodities in the settings to enable this feature.")
        return

    # Date selector (disabled - live rates are always shown for today)
    current_date = date.today()
    selected_date = current_date
    with st.expander("📅 Select Date", expanded=False):
        st.date_input(
            "Select Date",
            value=current_date,
            max_value=current_date,
            key="exchange_rate_date",
            label_visibility="collapsed",
            disabled=True
        )

    st.write("")  # Add spacing

    # Fetch exchange rates
    with st.spinner("Fetching rates..."):
        enabled_currencies = db.get_currency_codes()
        exchange_rates = CurrencyConverter.get_all_cross_rates(enabled_currencies)

    if not exchange_rates:
        st.error("Unable to fetch rates.")
        return

    # Display date caption
    st.caption(f"📅 {selected_date.strftime('%B %d, %Y')}")

    st.divider()

    # Get enabled currencies
    enabled_currencies = db.get_currency_codes()

    # Currency Exchange Rates Section
    st.subheader("💱 Currency Exchange Rates")
    
    # Generate all currency pairs (sorted alphabetically)
    rates_display = []
    for from_curr in enabled_currencies:
        for to_curr in enabled_currencies:
            if from_curr != to_curr:
                pair_key = f"{from_curr}_{to_curr}"
                rate_value = exchange_rates.get(pair_key, "N/A")
                rates_display.append((f"{from_curr} → {to_curr}", rate_value))

    # Sort alphabetically
    rates_display.sort(key=lambda x: x[0])

    # Display rates with better formatting
    for label, rate in rates_display:
        col1, col2 = st.columns([1.5, 1])
        with col1:
            st.markdown(f"**{label}**")
        with col2:
            if rate != "N/A":
                st.text(f"{rate:.4f}")
            else:
                st.text("N/A")
    
    # Commodity Prices Section
    commodities = db.get_commodities()
    if commodities:
        st.divider()
        st.subheader("🥇 Commodity Prices")
        
        # Unit selector dropdown
        unit_options = ["ounce", "gram", "kilogram", "pound", "ton"]
        
        # Initialize session state for selected unit if not exists
        if "commodity_display_unit" not in st.session_state:
            st.session_state.commodity_display_unit = "ounce"
        
        # Unit selector with callback
        col_unit1, col_unit2 = st.columns([1, 2])
        with col_unit1:
            selected_unit = st.selectbox(
                "Display Unit",
                options=unit_options,
                index=unit_options.index(st.session_state.commodity_display_unit),
                key="unit_selector",
                help="Select the unit for displaying commodity prices"
            )
        
        # Update session state if unit changed
        if selected_unit != st.session_state.commodity_display_unit:
            st.session_state.commodity_display_unit = selected_unit
            st.rerun()
        
        st.write("")  # Add spacing
        
        # Fetch commodity prices
        with st.spinner("Fetching commodity prices..."):
            commodity_names = [c['name'] for c in commodities]
            commodity_prices = CurrencyConverter.get_commodity_prices(commodity_names, enabled_currencies)
        
        if commodity_prices:
            # Display commodity prices in compact format like currency pairs
            commodity_display = []
            for commodity in commodities:
                commodity_name = commodity['name']
                commodity_unit = commodity.get('unit', 'ounce')
                if commodity_name in commodity_prices:
                    prices = commodity_prices[commodity_name]
                    for currency_code in enabled_currencies:
                        if currency_code in prices:
                            # Get base price (per ounce from API)
                            base_price = prices[currency_code]
                            
                            # Convert price to selected unit
                            converted_price = CurrencyConverter.convert_commodity_unit(
                                base_price,
                                "ounce",  # API returns prices per ounce
                                selected_unit
                            )
                            
                            # Get currency details for emoji
                            curr_details = db.get_currency_by_code(currency_code)
                            emoji = curr_details['flag_emoji'] if curr_details else ""
                            commodity_display.append((
                                f"{commodity['symbol']} {commodity_name} ({selected_unit}) → {emoji} {currency_code}",
                                converted_price
                            ))
            
            # Sort alphabetically
            commodity_display.sort(key=lambda x: x[0])
            
            # Display in same format as currency rates
            for label, price in commodity_display:
                col1, col2 = st.columns([1.5, 1])
                with col1:
                    st.markdown(f"**{label}**")
                with col2:
                    st.text(f"{price:,.2f}")
        else:
            st.info("💡 Commodity prices are currently unavailable. Please try again later.")


# ===== CALENDAR INVITE WIDGET =====

def page_reminder():
    """Reminder page for monthly balance update reminders"""
    st.title("🔔 Reminder")
    st.markdown("Set up calendar invites to remind you to update monthly balances")
    
    render_calendar_widget()

def calculate_scheduled_payment(principal, annual_interest_rate, total_payments, payments_per_year):
    """
    Calculate the regular scheduled mortgage payment using the PMT formula.

    Args:
        principal: Original loan amount
        annual_interest_rate: Annual nominal rate as a percentage (e.g. 3.55)
        total_payments: Total scheduled number of payments
        payments_per_year: Number of payments made per year

    Returns:
        float: Scheduled periodic payment amount
    """
    rate_per_period = (annual_interest_rate / 100) / payments_per_year

    if rate_per_period == 0:
        return principal / total_payments if total_payments else 0.0

    growth_factor = (1 + rate_per_period) ** total_payments
    return principal * (rate_per_period * growth_factor) / (growth_factor - 1)


def generate_amortization_schedule(
    loan_amount,
    annual_interest_rate,
    loan_term_years,
    payments_per_year,
    start_date,
    recurring_extra_payment,
    custom_extra_payments
):
    """
    Build a mortgage amortization schedule period-by-period until the loan is paid off.

    Args:
        loan_amount: Original mortgage principal
        annual_interest_rate: Annual nominal rate as a percentage
        loan_term_years: Loan term in years (can be fractional)
        payments_per_year: Number of scheduled payments per year
        start_date: Repayment start date
        recurring_extra_payment: Fixed extra payment applied every period
        custom_extra_payments: DataFrame with columns ['PMT NO', 'EXTRA PAYMENT']

    Returns:
        tuple[pd.DataFrame, dict]: Full schedule dataframe and summary metrics
    """
    total_scheduled_payments = loan_term_years * payments_per_year
    scheduled_payment = calculate_scheduled_payment(
        principal=loan_amount,
        annual_interest_rate=annual_interest_rate,
        total_payments=total_scheduled_payments,
        payments_per_year=payments_per_year
    )
    rate_per_period = (annual_interest_rate / 100) / payments_per_year

    # Build a lookup of one-off extra payments keyed by payment number.
    custom_payment_lookup = {}
    if custom_extra_payments is not None and not custom_extra_payments.empty:
        cleaned_custom_payments = custom_extra_payments.copy()
        cleaned_custom_payments = cleaned_custom_payments.dropna(subset=["PMT NO", "EXTRA PAYMENT"])

        for _, row in cleaned_custom_payments.iterrows():
            payment_no = int(row["PMT NO"])
            extra_amount = float(row["EXTRA PAYMENT"])
            if payment_no > 0 and extra_amount != 0:
                custom_payment_lookup[payment_no] = custom_payment_lookup.get(payment_no, 0.0) + extra_amount

    schedule_rows = []
    beginning_balance = float(loan_amount)
    cumulative_interest = 0.0
    payment_number = 1

    # Iterate until the mortgage is fully repaid.
    # The original sheet appears to be monthly, so payment dates advance month-by-month.
    months_per_payment = max(int(round(12 / payments_per_year)), 1)

    while beginning_balance > 1e-8:
        payment_date = start_date + relativedelta(months=(payment_number - 1) * months_per_payment)
        interest = beginning_balance * rate_per_period
        one_off_extra_payment = custom_payment_lookup.get(payment_number, 0.0)
        extra_payment = float(recurring_extra_payment) + one_off_extra_payment
        proposed_total_payment = scheduled_payment + extra_payment

        # Cap the final payment so the loan never goes below zero.
        payoff_amount = beginning_balance + interest
        total_payment = min(proposed_total_payment, payoff_amount)
        principal = total_payment - interest
        ending_balance = max(beginning_balance - principal, 0.0)
        cumulative_interest += interest

        schedule_rows.append({
            "PMT NO": payment_number,
            "PAYMENT DATE": payment_date,
            "BEGINNING BALANCE": beginning_balance,
            "SCHEDULED PAYMENT": scheduled_payment,
            "EXTRA PAYMENT": extra_payment,
            "TOTAL PAYMENT": total_payment,
            "PRINCIPAL": principal,
            "INTEREST": interest,
            "ENDING BALANCE": ending_balance,
            "CUMULATIVE INTEREST": cumulative_interest
        })

        beginning_balance = ending_balance
        payment_number += 1

        # Safety guard to avoid an infinite loop on unexpected inputs.
        if payment_number > max(int(total_scheduled_payments) * 5, 1000):
            break

    schedule_df = pd.DataFrame(schedule_rows)
    actual_number_of_payments = len(schedule_df)
    total_early_payments = schedule_df["EXTRA PAYMENT"].sum() if not schedule_df.empty else 0.0
    total_interest = schedule_df["INTEREST"].sum() if not schedule_df.empty else 0.0
    years_saved = (total_scheduled_payments - actual_number_of_payments) / payments_per_year

    summary = {
        "scheduled_payment": scheduled_payment,
        "scheduled_number_of_payments": total_scheduled_payments,
        "actual_number_of_payments": actual_number_of_payments,
        "years_saved": years_saved,
        "total_early_payments": total_early_payments,
        "total_interest": total_interest
    }

    return schedule_df, summary


def format_euro(amount):
    """Format a numeric value as Euro currency."""
    return f"€{amount:,.2f}"


def prepare_schedule_for_display(schedule_df):
    """
    Format the amortization schedule for Streamlit display and CSV export friendliness.
    """
    display_df = schedule_df.copy()

    if display_df.empty:
        return display_df

    display_df["PAYMENT DATE"] = pd.to_datetime(display_df["PAYMENT DATE"]).dt.strftime("%Y-%m-%d")

    display_df = display_df.rename(columns={
        "BEGINNING BALANCE": "BEGINNING BALANCE (€)",
        "SCHEDULED PAYMENT": "SCHEDULED PAYMENT (€)",
        "EXTRA PAYMENT": "EXTRA PAYMENT (€)",
        "TOTAL PAYMENT": "TOTAL PAYMENT (€)",
        "PRINCIPAL": "PRINCIPAL (€)",
        "INTEREST": "INTEREST (€)",
        "ENDING BALANCE": "ENDING BALANCE (€)",
        "CUMULATIVE INTEREST": "CUMULATIVE INTEREST (€)"
    })

    currency_columns = [
        "BEGINNING BALANCE (€)",
        "SCHEDULED PAYMENT (€)",
        "EXTRA PAYMENT (€)",
        "TOTAL PAYMENT (€)",
        "PRINCIPAL (€)",
        "INTEREST (€)",
        "ENDING BALANCE (€)",
        "CUMULATIVE INTEREST (€)"
    ]

    for column in currency_columns:
        display_df[column] = display_df[column].map(format_euro)

    return display_df

# Page: Mortgage Settings (in Settings tab)
def page_mortgage_settings(key_prefix=""):
    """Render the mortgage configuration settings page."""
    st.subheader("🏠 Mortgage Configuration")
    st.caption("Configure your mortgage details. These settings will be used in the Mortgage page.")
    
    # Initialize mortgage settings in session state if not present
    if "mortgage_config" not in st.session_state:
        st.session_state.mortgage_config = {
            "lender_name": "Your Bank",
            "loan_amount": 450586.0,
            "interest_rate": 3.55,
            "loan_term_years": 34.916,
            "payments_per_year": 12,
            "start_date": date(2024, 10, 7),
            "recurring_extra_payment": 0.0
        }
    
    st.info("💡 Enter your mortgage details below. These values will be used to calculate your amortization schedule on the Mortgage page.")
    
    # Create two columns for better layout
    col1, col2 = st.columns(2)
    
    with col1:
        lender_name = st.text_input(
            "Lender Name",
            value=st.session_state.mortgage_config["lender_name"],
            key=f"{key_prefix}lender_name",
            help="Name of your mortgage lender or bank"
        )
        
        loan_amount = st.number_input(
            "Loan Amount (€)",
            min_value=0.0,
            value=st.session_state.mortgage_config["loan_amount"],
            step=1000.0,
            format="%.2f",
            key=f"{key_prefix}loan_amount",
            help="Total mortgage loan amount in Euros"
        )
        
        interest_rate = st.number_input(
            "Interest Rate (%)",
            min_value=0.0,
            max_value=100.0,
            value=st.session_state.mortgage_config["interest_rate"],
            step=0.01,
            format="%.4f",
            key=f"{key_prefix}interest_rate",
            help="Annual interest rate as a percentage (e.g., 3.55 for 3.55%)"
        )
        
        loan_term_years = st.number_input(
            "Loan Term in Years",
            min_value=0.0,
            max_value=50.0,
            value=st.session_state.mortgage_config["loan_term_years"],
            step=0.1,
            format="%.4f",
            key=f"{key_prefix}loan_term_years",
            help="Original loan term in years (can include decimals)"
        )
    
    with col2:
        payments_per_year = st.number_input(
            "Payments Made Per Year",
            min_value=1,
            max_value=365,
            value=st.session_state.mortgage_config["payments_per_year"],
            step=1,
            key=f"{key_prefix}payments_per_year",
            help="Number of payments per year (typically 12 for monthly)"
        )
        
        start_date = st.date_input(
            "Loan Repayment Start Date",
            value=st.session_state.mortgage_config["start_date"],
            key=f"{key_prefix}start_date",
            help="Date when loan repayments begin"
        )
        
        recurring_extra_payment = st.number_input(
            "Optional Extra Payments (€)",
            min_value=0.0,
            value=st.session_state.mortgage_config["recurring_extra_payment"],
            step=100.0,
            format="%.2f",
            key=f"{key_prefix}recurring_extra_payment",
            help="Additional amount to pay with each regular payment"
        )
    
    st.divider()
    
    # Save button
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    
    with col_btn1:
        if st.button("💾 Save Configuration", key=f"{key_prefix}save_btn", type="primary", use_container_width=True):
            # Update session state with new values
            st.session_state.mortgage_config = {
                "lender_name": lender_name,
                "loan_amount": loan_amount,
                "interest_rate": interest_rate,
                "loan_term_years": loan_term_years,
                "payments_per_year": payments_per_year,
                "start_date": start_date,
                "recurring_extra_payment": recurring_extra_payment
            }
            st.success("✅ Mortgage configuration saved successfully!")
            st.info("📊 Go to the Mortgage page to view your amortization schedule.")
    
    with col_btn2:
        if st.button("🔄 Reset to Defaults", key=f"{key_prefix}reset_btn", use_container_width=True):
            st.session_state.mortgage_config = {
                "lender_name": "Your Bank",
                "loan_amount": 450586.0,
                "interest_rate": 3.55,
                "loan_term_years": 34.916,
                "payments_per_year": 12,
                "start_date": date(2024, 10, 7),
                "recurring_extra_payment": 0.0
            }
            st.rerun()
    
    st.divider()
    
    # Display current configuration summary
    st.subheader("📋 Current Configuration Summary")
    
    summary_col1, summary_col2 = st.columns(2)
    
    with summary_col1:
        st.metric("Lender", st.session_state.mortgage_config["lender_name"])
        st.metric("Loan Amount", format_euro(st.session_state.mortgage_config["loan_amount"]))
        st.metric("Interest Rate", f"{st.session_state.mortgage_config['interest_rate']:.4f}%")
        st.metric("Loan Term", f"{st.session_state.mortgage_config['loan_term_years']:.3f} years")
    
    with summary_col2:
        st.metric("Payments Per Year", st.session_state.mortgage_config["payments_per_year"])
        st.metric("Start Date", st.session_state.mortgage_config["start_date"].strftime("%d/%m/%Y"))
        st.metric("Extra Payments", format_euro(st.session_state.mortgage_config["recurring_extra_payment"]))



def page_mortgage():
    """Render the mortgage amortization calculator."""
    st.title("🏠 Mortgage Amortization Schedule: Kilmartin Grove")
    st.caption("Interactive mortgage amortization calculator with recurring and one-off extra payments, fully formatted in Euros.")
    
    # Initialize mortgage configuration if not present
    if "mortgage_config" not in st.session_state:
        st.session_state.mortgage_config = {
            "lender_name": "Your Bank",
            "loan_amount": 450586.0,
            "interest_rate": 3.55,
            "loan_term_years": 34.916,
            "payments_per_year": 12,
            "start_date": date(2024, 10, 7),
            "recurring_extra_payment": 0.0
        }
    
    # Initialize editable one-off payment defaults once in session state.
    if "mortgage_custom_payments" not in st.session_state:
        st.session_state.mortgage_custom_payments = pd.DataFrame(
            columns=["PMT NO", "EXTRA PAYMENT"]
        )
    
    # Get values from saved configuration
    lender_name = st.session_state.mortgage_config["lender_name"]
    loan_amount = st.session_state.mortgage_config["loan_amount"]
    interest_rate = st.session_state.mortgage_config["interest_rate"]
    loan_term_years = st.session_state.mortgage_config["loan_term_years"]
    payments_per_year = st.session_state.mortgage_config["payments_per_year"]
    loan_start_date = st.session_state.mortgage_config["start_date"]
    recurring_extra_payment = st.session_state.mortgage_config["recurring_extra_payment"]
    
    # Check if configuration is set (not default zeros)
    if loan_amount == 0 or interest_rate == 0 or loan_term_years == 0:
        st.warning("⚠️ Mortgage configuration not set. Please configure your mortgage details in Settings → Mortgage tab.")
        st.info("👉 Go to **Settings** page and select the **🏠 Mortgage** tab to enter your mortgage details.")
        return
    
    st.info("💡 To modify mortgage details, go to **Settings → Mortgage** tab.")
    
    # Display current mortgage configuration
    st.markdown(f"### Loan Summary — {lender_name}")
    
    with st.expander("📋 View Mortgage Configuration", expanded=False):
        config_col1, config_col2 = st.columns(2)
        
        with config_col1:
            st.write("**Loan Amount:**", format_euro(loan_amount))
            st.write("**Interest Rate:**", f"{interest_rate:.4f}%")
            st.write("**Loan Term:**", f"{loan_term_years:.3f} years")
        
        with config_col2:
            st.write("**Payments Per Year:**", payments_per_year)
            st.write("**Start Date:**", loan_start_date.strftime("%d/%m/%Y"))
            st.write("**Recurring Extra Payment:**", format_euro(recurring_extra_payment))
    
    st.write("#### One-Off / Custom Extra Payments")

    edited_custom_payments = st.data_editor(
        st.session_state.mortgage_custom_payments,
        num_rows="dynamic",
        width="stretch",
        hide_index=True,
        column_config={
            "PMT NO": st.column_config.NumberColumn(
                "PMT NO",
                min_value=1,
                step=1,
                format="%d",
                help="Payment number to apply the one-off extra payment to."
            ),
            "EXTRA PAYMENT": st.column_config.NumberColumn(
                "EXTRA PAYMENT (€)",
                min_value=0.0,
                step=100.0,
                format="%.2f",
                help="One-off extra payment amount in Euros."
            )
        },
        key="mortgage_custom_payment_editor"
    )

    st.session_state.mortgage_custom_payments = edited_custom_payments

    schedule_df, summary = generate_amortization_schedule(
        loan_amount=loan_amount,
        annual_interest_rate=interest_rate,
        loan_term_years=loan_term_years,
        payments_per_year=payments_per_year,
        start_date=loan_start_date,
        recurring_extra_payment=recurring_extra_payment,
        custom_extra_payments=edited_custom_payments
    )

    metric_col_1, metric_col_2, metric_col_3 = st.columns(3)
    metric_col_4, metric_col_5, metric_col_6 = st.columns(3)

    metric_col_1.metric("Scheduled payment", format_euro(summary["scheduled_payment"]))
    metric_col_2.metric("Scheduled number of payments", f'{summary["scheduled_number_of_payments"]:.2f}')
    metric_col_3.metric("Actual number of payments", f'{summary["actual_number_of_payments"]}')

    metric_col_4.metric("Years saved off original loan term", f'{summary["years_saved"]:.3f}')
    metric_col_5.metric("Total early payments", format_euro(summary["total_early_payments"]))
    metric_col_6.metric("Total interest", format_euro(summary["total_interest"]))

    st.divider()
    st.write("### Amortization Schedule")

    display_df = prepare_schedule_for_display(schedule_df)

    csv_buffer = StringIO()
    schedule_df_for_csv = schedule_df.copy()
    if not schedule_df_for_csv.empty:
        schedule_df_for_csv["PAYMENT DATE"] = pd.to_datetime(schedule_df_for_csv["PAYMENT DATE"]).dt.strftime("%Y-%m-%d")
        numeric_columns = [
            "BEGINNING BALANCE",
            "SCHEDULED PAYMENT",
            "EXTRA PAYMENT",
            "TOTAL PAYMENT",
            "PRINCIPAL",
            "INTEREST",
            "ENDING BALANCE",
            "CUMULATIVE INTEREST"
        ]
        schedule_df_for_csv[numeric_columns] = schedule_df_for_csv[numeric_columns].round(2)

    schedule_df_for_csv.to_csv(csv_buffer, index=False)

    st.download_button(
        label="Download Amortization_Schedule.csv",
        data=csv_buffer.getvalue(),
        file_name="Amortization_Schedule.csv",
        mime="text/csv",
        type="primary"
    )

    st.dataframe(display_df, width="stretch", hide_index=True)

    if not schedule_df.empty:
        with st.expander("Custom extra payment dates"):
            custom_payment_rows = []
            custom_lookup = edited_custom_payments.dropna(subset=["PMT NO", "EXTRA PAYMENT"]).copy()

            for _, row in custom_lookup.iterrows():
                payment_no = int(row["PMT NO"])
                extra_payment_amount = float(row["EXTRA PAYMENT"])

                if payment_no > 0 and payment_no <= len(schedule_df):
                    payment_date = schedule_df.loc[schedule_df["PMT NO"] == payment_no, "PAYMENT DATE"].iloc[0]
                    custom_payment_rows.append({
                        "PMT NO": payment_no,
                        "DATE": pd.to_datetime(payment_date).strftime("%Y-%m-%d"),
                        "EXTRA PAYMENT": format_euro(extra_payment_amount)
                    })

            if custom_payment_rows:
                st.dataframe(pd.DataFrame(custom_payment_rows), width="stretch", hide_index=True)
            else:
                st.caption("No valid one-off extra payments configured.")



def render_calendar_widget():
    """Calendar Invite widget for monthly balance update reminders"""
    from datetime import datetime, timedelta

    st.write("**Create Monthly Reminder**")
    st.caption("Set up a calendar invite to remind you to update monthly balances")

    # Initialize previous date in session state if not exists
    if "prev_calendar_start_date" not in st.session_state:
        st.session_state.prev_calendar_start_date = datetime.now().date() + timedelta(days=30)

    # Date selector for first reminder
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "First Reminder Date",
            value=st.session_state.prev_calendar_start_date,
            key="calendar_start_date"
        )
        
        # Update previous date when changed
        if start_date != st.session_state.prev_calendar_start_date:
            st.session_state.prev_calendar_start_date = start_date

    with col2:
        reminder_time = st.time_input(
            "Reminder Time",
            value=datetime.strptime("09:00", "%H:%M").time(),
            key="calendar_time"
        )

    # Email input
    emails = st.text_input(
        "Invite additional attendees",
        placeholder="email1@example.com, email2@example.com",
        help="Add comma-separated email addresses",
        key="calendar_emails"
    )

    # Generate invite button
    if st.button("Generate Calendar Invite", width="stretch", type="primary", key="gen_calendar"):
        if emails:
            # Create .ics file content
            event_datetime = datetime.combine(start_date, reminder_time)

            ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//KUYAN//Monthly Balance Reminder//EN
BEGIN:VEVENT
UID:{event_datetime.strftime('%Y%m%d%H%M%S')}@kuyan
DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}
DTSTART:{event_datetime.strftime('%Y%m%dT%H%M%S')}
DTEND:{(event_datetime + timedelta(hours=1)).strftime('%Y%m%dT%H%M%S')}
RRULE:FREQ=MONTHLY;COUNT=12
SUMMARY:Update Monthly Balances in KUYAN
DESCRIPTION:Monthly reminder to update account balances in KUYAN
LOCATION:KUYAN App
ATTENDEE:MAILTO:{emails.split(',')[0].strip()}
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR"""

            # Offer download
            st.download_button(
                label="📅 Download .ics File",
                data=ics_content,
                file_name=f"kuyan_reminder_{start_date.strftime('%Y%m%d')}.ics",
                mime="text/calendar",
                width="stretch"
            )
            st.success("Calendar invite generated! Click above to download.")
        else:
            st.error("Please enter at least one email address")


# ===== EXPORT DASHBOARD WIDGET =====

# Main app
def render_navbar():
    """Render horizontal navbar with tool buttons for dashboard pages"""
    colors = get_theme_colors()
    
    # Initialize modal states in session state
    if "show_exchange_rate_modal" not in st.session_state:
        st.session_state.show_exchange_rate_modal = False
    
    # Create navbar with buttons
    st.markdown(f"""
        <style>
        .navbar-container {{
            background-color: {colors['bg_secondary']};
            padding: 10px 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            border: 1px solid {colors['border']};
        }}
        </style>
    """, unsafe_allow_html=True)
    
    # Create columns for navbar buttons
    cols = st.columns([1])
    
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
        default_currency = get_default_currency()
        st.session_state.base_currency = default_currency

    # Render sidebar and get selected settings page
    settings_page = render_sidebar()

    # Check if a settings page is selected
    if settings_page in ["Settings", "Exchange Rates", "Reminder", "Mortgage"]:
        # Show settings page
        if settings_page == "Settings":
            page_settings()
        elif settings_page == "Exchange Rates":
            page_exchange_rates()
        elif settings_page == "Reminder":
            page_reminder()
        elif settings_page == "Mortgage":
            page_mortgage()
    else:
        # Render full navbar with all buttons for dashboard pages
        st.title("📊 Dashboard")
        
        # Custom CSS to make tabs larger
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


        # Main navigation tabs at the top for primary pages
        tab1, tab2, tab3 = st.tabs(
            ["📊 Overview", "💰 Update Balances", "📜 History"]
        )

        with tab1:
            page_dashboard()

        with tab2:
            page_update_balances()

        with tab3:
            page_history()


if __name__ == "__main__":
    main()
