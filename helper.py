"""
KUYAN - Monthly Net Worth Tracker
Helper Functions Module - Common utility functions used across the application
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
    """Convert amount using exchange rates for regular currency accounts
    
    Args:
        amount: Amount to convert
        from_currency: Source currency code
        to_currency: Target currency code
        rates: Dictionary of exchange rates
        
    Returns:
        Converted amount in target currency
    """
    if not rates:
        return amount
    return CurrencyConverter.convert(amount, from_currency, to_currency, rates)


def get_commodity_value(quantity, commodity_name, target_currency, commodity_prices, commodity_configs, commodity_unit=None):
    """Calculate commodity value in target currency
    
    This function handles the conversion of commodity quantities to currency values,
    taking into account the unit of measurement for each commodity.
    
    Args:
        quantity: Quantity of commodity held
        commodity_name: Name of the commodity (e.g., "Gold", "Silver")
        target_currency: Target currency code (e.g., "EUR", "USD")
        commodity_prices: Dictionary of commodity prices per troy ounce
                         Format: {"Gold": {"USD": 2000.50, "EUR": 1850.25}, ...}
        commodity_configs: Dictionary of commodity configurations
                          Format: {"Gold": {"unit": "gram", ...}, ...}
        commodity_unit: Optional unit override from snapshot (takes precedence over commodity_configs)
    
    Returns:
        float: Value of the commodity in target currency
    """
    if not commodity_name or commodity_name not in commodity_prices:
        return 0.0
    
    # Get price per troy ounce in target currency
    price_per_ounce = commodity_prices[commodity_name].get(target_currency, 0)
    
    if price_per_ounce == 0:
        return 0.0
    
    # Get the unit for this commodity
    # Priority: 1) commodity_unit parameter (from snapshot), 2) commodity_configs, 3) default "ounce"
    if commodity_unit:
        resolved_unit = commodity_unit
    elif commodity_name in commodity_configs:
        resolved_unit = commodity_configs[commodity_name].get('unit', 'ounce')
    else:
        resolved_unit = "ounce"
    
    # Convert price from per-ounce to per-unit
    # IMPORTANT: API always returns price per troy ounce, so from_unit is always "ounce"
    price_per_unit = CurrencyConverter.convert_commodity_unit(
        price_per_ounce,
        "ounce",  # API always returns per troy ounce (from_unit)
        resolved_unit  # Convert to the commodity's configured unit (to_unit)
    )
    
    total_value = quantity * price_per_unit
    
    # Calculate total value: quantity * price per unit
    return total_value


def get_converted_account_value(snapshot, target_currency, rates, commodity_prices=None, commodity_configs=None):
    """Convert account value to target currency, handling both regular and commodity accounts
    
    Args:
        snapshot: Account snapshot dictionary with balance, currency, account_type, etc.
        target_currency: Target currency code
        rates: Dictionary of exchange rates
        commodity_prices: Optional dictionary of commodity prices (required for commodity accounts)
        commodity_configs: Optional dictionary of commodity configurations (required for commodity accounts)
    
    Returns:
        float: Converted value in target currency
    """
    is_commodity = snapshot.get("account_type") == "Commodity"
    
    if is_commodity:
        # For commodity accounts, use commodity-specific calculation
        commodity_name = snapshot.get("commodity")
        quantity = snapshot["balance"]
        
        # Get unit from snapshot if available (from database join), otherwise from commodity_configs
        commodity_unit = snapshot.get("commodity_unit")
        if not commodity_unit and commodity_configs and commodity_name in commodity_configs:
            commodity_unit = commodity_configs[commodity_name].get('unit', 'ounce')
        elif not commodity_unit:
            commodity_unit = "ounce"  # Default fallback
        
        if commodity_prices and commodity_configs:
            return get_commodity_value(quantity, commodity_name, target_currency, commodity_prices, commodity_configs, commodity_unit)
        else:
            # Fallback if commodity data not provided
            return 0.0
    else:
        # For regular accounts, use currency conversion
        return get_converted_value(
            snapshot["balance"],
            snapshot["currency"],
            target_currency,
            rates
        )

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


def calculate_total_net_worth(snapshots, base_currency, db, excluded_account_types=None, include_mortgage_debt=False):
    """Calculate total net worth from snapshots in base currency
    
    Args:
        snapshots: List of account snapshots
        base_currency: Target currency for conversion
        db: Database instance
        excluded_account_types: Optional list of account types to exclude from calculation
        include_mortgage_debt: If True, subtract mortgage debt from net worth
    
    Returns:
        float: Total net worth in base currency (assets minus mortgage debt if include_mortgage_debt=True)
    """
    if not snapshots:
        return 0.0
    
    # Filter out excluded account types if specified
    if excluded_account_types:
        snapshots = [s for s in snapshots if s.get("account_type") not in excluded_account_types]
    
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
        # Use the new unified function to get converted value
        converted = get_converted_account_value(
            snapshot,
            base_currency,
            rates,
            commodity_prices,
            commodity_configs
        )
        total += converted
    
    # Subtract mortgage debt if requested
    if include_mortgage_debt:
        all_mortgage_balances = get_all_mortgage_balances(db)
        for mortgage in all_mortgage_balances:
            # Convert mortgage balance to base currency and subtract
            if rates:
                mortgage_in_base = get_converted_value(
                    mortgage["balance"],
                    mortgage["currency"],
                    base_currency,
                    rates
                )
                total -= mortgage_in_base

    return total


def get_current_mortgage_balance(db):
    """Get the current remaining mortgage balance and its currency (backward compatible)
    
    Returns:
        tuple: (balance, currency) where balance is float and currency is str
        Returns the first mortgage's balance for backward compatibility
    """
    all_balances = get_all_mortgage_balances(db)
    if not all_balances:
        return 0.0, "EUR"
    return all_balances[0]["balance"], all_balances[0]["currency"]


def get_all_mortgage_balances(db):
    """Get current remaining balances for all mortgages
    
    Returns:
        list: List of dicts with keys: mortgage_id, mortgage_name, balance, currency
    """
    # Get all mortgages
    all_mortgages = db.get_all_mortgages()
    if not all_mortgages:
        return []
    
    mortgage_balances = []
    
    for mortgage in all_mortgages:
        mortgage_id = mortgage["id"]
        mortgage_name = mortgage["mortgage_name"]
        
        # Get mortgage configuration
        loan_amount = float(mortgage["loan_amount"])
        interest_rate = float(mortgage["interest_rate"])
        loan_term_years = float(mortgage["loan_term_years"])
        payments_per_year = int(mortgage["payments_per_year"])
        start_date = date.fromisoformat(mortgage["start_date"]) if isinstance(mortgage["start_date"], str) else mortgage["start_date"]
        defer_months = int(mortgage.get("defer_months", 0))
        recurring_extra_payment = float(mortgage["recurring_extra_payment"])
        currency = mortgage.get("currency", "EUR")
        
        # Get extra payments for this specific mortgage
        db_payments = db.get_mortgage_extra_payments(mortgage_id)
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
            defer_months=defer_months,
            recurring_extra_payment=recurring_extra_payment,
            custom_extra_payments=custom_payments
        )
        
        current_balance = 0.0
        
        if not schedule_df.empty:
            # Find the most recent payment that has occurred (payment date <= today)
            from datetime import datetime
            today = datetime.now().date()
            schedule_df["PAYMENT DATE"] = pd.to_datetime(schedule_df["PAYMENT DATE"]).dt.date
            
            # Filter to payments that have already occurred
            past_payments = schedule_df[schedule_df["PAYMENT DATE"] <= today]
            
            if past_payments.empty:
                # No payments made yet, use original loan amount
                current_balance = loan_amount
            else:
                # Get the ending balance from the most recent payment
                current_balance = float(past_payments.iloc[-1]["ENDING BALANCE"])
        else:
            # If schedule is empty, use original loan amount
            current_balance = loan_amount
        
        mortgage_balances.append({
            "mortgage_id": mortgage_id,
            "mortgage_name": mortgage_name,
            "balance": current_balance,
            "currency": currency
        })
    
    return mortgage_balances


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
    defer_months=0,
    recurring_extra_payment=0.0,
    custom_extra_payments=None
):
    """
    Build a mortgage amortization schedule period-by-period until the loan is paid off.

    Args:
        loan_amount: Original mortgage principal
        annual_interest_rate: Annual nominal rate as a percentage
        loan_term_years: Loan term in years (can be fractional)
        payments_per_year: Number of scheduled payments per year
        start_date: Loan start date (not payment start date)
        defer_months: Number of months to defer payments (interest accrues during deferral)
        recurring_extra_payment: Fixed extra payment applied every period
        custom_extra_payments: DataFrame with columns ['PMT NO', 'EXTRA PAYMENT']

    Returns:
        tuple[pd.DataFrame, dict]: Full schedule dataframe and summary metrics
    """
    total_scheduled_payments = loan_term_years * payments_per_year
    rate_per_period = (annual_interest_rate / 100) / payments_per_year
    months_per_payment = max(int(round(12 / payments_per_year)), 1)
    
    # Calculate the principal after deferral period (with accrued interest)
    # During deferral, interest compounds but no payments are made
    deferred_principal = loan_amount
    if defer_months > 0:
        # Calculate number of compounding periods during deferral
        deferral_periods = defer_months / months_per_payment
        deferred_principal = loan_amount * ((1 + rate_per_period) ** deferral_periods)
    
    # Calculate scheduled payment based on the deferred principal
    scheduled_payment = calculate_scheduled_payment(
        principal=deferred_principal,
        annual_interest_rate=annual_interest_rate,
        total_payments=total_scheduled_payments,
        payments_per_year=payments_per_year
    )

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
    while beginning_balance > 1e-8:
        # Calculate payment date: start_date + defer_months + payment periods
        payment_date = start_date + relativedelta(months=defer_months + (payment_number - 1) * months_per_payment)
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





def get_property_equity_data(db):
    """Get equity data for all properties with linked mortgages
    
    Returns:
        list: List of dicts with property equity information
    """
    properties = db.get_all_properties_with_financials()
    all_mortgage_balances = get_all_mortgage_balances(db)
    
    equity_data = []
    
    for prop in properties:
        property_id = prop['id']
        property_name = prop['property_name']
        currency = prop['currency']
        market_value = float(prop.get('latest_value', 0.0)) if prop.get('latest_value') else 0.0
        
        # Calculate total mortgage debt for this property
        total_debt = 0.0
        linked_mortgages = []
        
        for mortgage in prop.get('mortgages', []):
            mortgage_balance = next((m for m in all_mortgage_balances if m['mortgage_id'] == mortgage['id']), None)
            if mortgage_balance:
                total_debt += mortgage_balance['balance']
                linked_mortgages.append({
                    'name': mortgage_balance['mortgage_name'],
                    'balance': mortgage_balance['balance'],
                    'currency': mortgage_balance['currency']
                })
        
        equity = market_value - total_debt
        equity_percentage = (equity / market_value * 100) if market_value > 0 else 0
        
        equity_data.append({
            'property_id': property_id,
            'property_name': property_name,
            'property_type': prop.get('property_type', 'Unknown'),
            'owner': prop.get('owner', 'Unknown'),
            'currency': currency,
            'market_value': market_value,
            'total_debt': total_debt,
            'equity': equity,
            'equity_percentage': equity_percentage,
            'linked_mortgages': linked_mortgages,
            'valuation_date': prop.get('latest_valuation_date'),
            'valuation_type': prop.get('valuation_type')
        })
    
    return equity_data


def calculate_total_property_assets(db, base_currency, rates=None):
    """Calculate total value of all property assets in base currency
    
    Args:
        db: Database instance
        base_currency: Target currency for conversion
        rates: Optional exchange rates dictionary
    
    Returns:
        float: Total property asset value in base currency
    """
    properties = db.get_all_properties_with_financials()
    total = 0.0
    
    for prop in properties:
        market_value = float(prop.get('latest_value', 0.0)) if prop.get('latest_value') else 0.0
        property_currency = prop.get('currency', 'EUR')
        
        if rates and property_currency != base_currency:
            converted_value = get_converted_value(market_value, property_currency, base_currency, rates)
            total += converted_value
        else:
            total += market_value
    
    return total


def calculate_total_property_liabilities(db, base_currency, rates=None):
    """Calculate total mortgage debt across all properties in base currency
    
    Args:
        db: Database instance
        base_currency: Target currency for conversion
        rates: Optional exchange rates dictionary
    
    Returns:
        float: Total property liability value in base currency
    """
    all_mortgage_balances = get_all_mortgage_balances(db)
    total = 0.0
    
    for mortgage in all_mortgage_balances:
        balance = mortgage['balance']
        mortgage_currency = mortgage['currency']
        
        if rates and mortgage_currency != base_currency:
            converted_balance = get_converted_value(balance, mortgage_currency, base_currency, rates)
            total += converted_balance
        else:
            total += balance
    
    return total
