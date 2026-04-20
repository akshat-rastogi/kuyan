"""
KUYAN - Monthly Net Worth Tracker
Helper Functions Module - Common utility functions used across the application
Copyright (c) 2025 mycloudcondo inc.
Licensed under MIT License - see LICENSE file for details
"""

import streamlit as st
from currencyConverter import CurrencyConverter
from constants import AVAILABLE_CURRENCIES
import json
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta


def get_currency_symbol(currency):
    """Get currency symbol for display
    
    Args:
        currency: Currency code (e.g., 'USD', 'EUR')
        
    Returns:
        Currency symbol string, or the currency code if not found
    """
    return AVAILABLE_CURRENCIES.get(currency, {}).get("symbol", currency)



def get_default_currency(db):
    """Get the default base currency (first enabled currency)"""
    codes = db.get_currency_codes()
    return codes[0] if codes else "EUR"


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



def get_converted_value(amount, from_currency, to_currency, rates):
    """Convert amount using exchange rates"""
    if not rates:
        return amount
    return CurrencyConverter.convert(amount, from_currency, to_currency, rates)

def has_multiple_currencies(db) -> bool:
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




def get_rates_from_snapshot(snapshot):
    """Extract exchange rates from a snapshot, returning empty dict if not present"""
    return json.loads(snapshot["exchange_rates"]) if snapshot.get("exchange_rates") else {}






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


def calculate_total_net_worth(snapshots, base_currency, db):
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


def get_current_mortgage_balance(db):
    """Get the current remaining mortgage balance and its currency
    
    Returns:
        tuple: (balance, currency) where balance is float and currency is str
    """
    # Get mortgage settings
    db_settings = db.get_mortgage_settings()
    if not db_settings:
        return 0.0, "EUR"
    
    # Get mortgage configuration
    loan_amount = float(db_settings["loan_amount"])
    interest_rate = float(db_settings["interest_rate"])
    loan_term_years = float(db_settings["loan_term_years"])
    payments_per_year = int(db_settings["payments_per_year"])
    start_date = date.fromisoformat(db_settings["start_date"])
    recurring_extra_payment = float(db_settings["recurring_extra_payment"])
    currency = db_settings.get("currency", "EUR")
    
    # Get extra payments
    db_payments = db.get_mortgage_extra_payments()
    if db_payments:
        payments_data = [
            {"PMT NO": int(p["payment_number"]), "EXTRA PAYMENT": float(p["extra_payment_amount"])}
            for p in db_payments
        ]
        custom_payments = pd.DataFrame(payments_data)
    else:
        custom_payments = pd.DataFrame({"PMT NO": [], "EXTRA PAYMENT": []})
    
    # Generate amortization schedule
    schedule_df, _ = generate_amortization_schedule(
        loan_amount=loan_amount,
        annual_interest_rate=interest_rate,
        loan_term_years=loan_term_years,
        payments_per_year=payments_per_year,
        start_date=start_date,
        recurring_extra_payment=recurring_extra_payment,
        custom_extra_payments=custom_payments
    )
    
    if schedule_df.empty:
        return 0.0, currency
    
    # Find the most recent payment that has occurred (payment date <= today)
    from datetime import datetime
    today = datetime.now().date()
    schedule_df["PAYMENT DATE"] = pd.to_datetime(schedule_df["PAYMENT DATE"]).dt.date
    
    # Filter to payments that have already occurred
    past_payments = schedule_df[schedule_df["PAYMENT DATE"] <= today]
    
    if past_payments.empty:
        # No payments made yet, return original loan amount
        return loan_amount, currency
    
    # Get the ending balance from the most recent payment
    current_balance = past_payments.iloc[-1]["ENDING BALANCE"]
    
    return float(current_balance), currency


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


def format_currency(amount, currency_code="EUR"):
    """
    Format a numeric value with the appropriate currency symbol.
    
    Args:
        amount: Numeric value to format
        currency_code: Currency code (e.g., 'EUR', 'USD', 'GBP'). Defaults to 'EUR'.
    
    Returns:
        Formatted string with currency symbol and amount
    """
    symbol = get_currency_symbol(currency_code)
    return f"{symbol}{amount:,.2f}"


def prepare_schedule_for_display(schedule_df, currency_code="EUR"):
    """
    Format the amortization schedule for Streamlit display and CSV export friendliness.
    
    Args:
        schedule_df: DataFrame containing the amortization schedule
        currency_code: Currency code for formatting (e.g., 'EUR', 'USD'). Defaults to 'EUR'.
    
    Returns:
        Formatted DataFrame with currency symbols
    """
    display_df = schedule_df.copy()

    if display_df.empty:
        return display_df

    display_df["PAYMENT DATE"] = pd.to_datetime(display_df["PAYMENT DATE"]).dt.strftime("%Y-%m-%d")

    # Get currency symbol for column headers
    currency_symbol = get_currency_symbol(currency_code)
    
    display_df = display_df.rename(columns={
        "BEGINNING BALANCE": f"BEGINNING BALANCE ({currency_symbol})",
        "SCHEDULED PAYMENT": f"SCHEDULED PAYMENT ({currency_symbol})",
        "EXTRA PAYMENT": f"EXTRA PAYMENT ({currency_symbol})",
        "TOTAL PAYMENT": f"TOTAL PAYMENT ({currency_symbol})",
        "PRINCIPAL": f"PRINCIPAL ({currency_symbol})",
        "INTEREST": f"INTEREST ({currency_symbol})",
        "ENDING BALANCE": f"ENDING BALANCE ({currency_symbol})",
        "CUMULATIVE INTEREST": f"CUMULATIVE INTEREST ({currency_symbol})"
    })

    currency_columns = [
        f"BEGINNING BALANCE ({currency_symbol})",
        f"SCHEDULED PAYMENT ({currency_symbol})",
        f"EXTRA PAYMENT ({currency_symbol})",
        f"TOTAL PAYMENT ({currency_symbol})",
        f"PRINCIPAL ({currency_symbol})",
        f"INTEREST ({currency_symbol})",
        f"ENDING BALANCE ({currency_symbol})",
        f"CUMULATIVE INTEREST ({currency_symbol})"
    ]

    for column in currency_columns:
        display_df[column] = display_df[column].map(lambda x: format_currency(x, currency_code))

    return display_df


