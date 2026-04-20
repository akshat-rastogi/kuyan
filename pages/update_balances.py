"""
KUYAN - Monthly Net Worth Tracker
Accounts Page Module - Handles monthly balance updates
Copyright (c) 2025 mycloudcondo inc.
Licensed under MIT License - see LICENSE file for details
"""

import streamlit as st
from datetime import date
from database import Database
from currencyConverter import CurrencyConverter
import json
from helper import (
    get_default_currency,
    get_currency_symbol,
    get_converted_value,
    get_commodity_value,
    get_converted_account_value,
    calculate_total_net_worth
)
from components import render_calendar_widget
from pages.mortgage import mortgage as mortgage_page


# ===== CONSTANTS =====
MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


def update_balances(db: Database):
    st.title("💰 Update Accounts")
    
    # Apply tab styling to match settings page
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
    
    # Create tabs for Accounts, Mortgage, and Reminder
    tab1, tab2, tab3 = st.tabs(["📊 Update Balances", "🏠 Update Mortgage", "🔔 Add Reminder"])
    
    with tab1:
        balances(db=db)
    
    with tab2:
        mortgage_page(db=db)
    
    with tab3:
        st.markdown("Set up calendar invites to remind you to update monthly balances")
        render_calendar_widget()

def balances(db: Database):
    """
    Render the Accounts page for monthly snapshots.
    
    Args:
        db: Database instance
    """
    
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

    # Month/Year selector section
    st.subheader("📅 Update Monthly Balances")

    col1, col2, col_warning = st.columns([2, 2, 4])

    with col1:
        selected_year = st.selectbox(
            "Year",
            options=list(range(current_date.year, current_date.year - 10, -1)),
            index=0,
            key='year_selector'
        )

    with col2:
        # Create months in descending order (Dec to Jan)
        months_desc = list(range(12, 0, -1))
        selected_month = st.selectbox(
            "Month",
            options=months_desc,
            format_func=lambda x: month_names[x - 1],
            index=months_desc.index(current_date.month),
            key='month_selector'
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

    # Display existing snapshot if it exists
    if snapshot_exists:
        existing_snapshots = db.get_snapshots_by_date(snapshot_date)
        if existing_snapshots:
            # Get base currency (default to first enabled currency)
            default_currency = get_default_currency(db)
            base_currency = st.session_state.get("base_currency", default_currency)
            currency_symbol = get_currency_symbol(base_currency)

            # Get exchange rates
            rates = json.loads(existing_snapshots[0]["exchange_rates"]) if existing_snapshots[0].get("exchange_rates") else {}

            # Calculate total net worth
            total = calculate_total_net_worth(existing_snapshots, base_currency, db)
            
            # Fetch commodity prices if there are commodity accounts
            commodity_accounts = [s for s in existing_snapshots if s.get("account_type") == "Commodity"]
            commodity_prices = {}
            commodity_configs = {}
            
            if commodity_accounts and rates:
                # Get snapshot date and unique commodities
                snapshot_date_str = snapshot_date.isoformat()
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
                    
                    # Get commodity configurations to know the units
                    commodity_configs = {c['name']: c for c in db.get_commodities()}

            # Create accordion with month name and total net worth in title
            expander_label = f"📋 Existing Snapshot for {month_names[selected_month - 1]} {selected_year} - Total Net Worth: `{currency_symbol}{total:,.2f}` ({base_currency})"
            with st.expander(expander_label, expanded=False):
                # Get owners for grouping
                owners = db.get_owners()
                owner_names = [owner['name'] for owner in owners]
                
                # Display snapshots grouped by owner
                log_entries = []
                for idx, owner_name in enumerate(owner_names):
                    owner_snapshots = [s for s in existing_snapshots if s['owner'] == owner_name]

                    if owner_snapshots:
                        # Add line break before each owner (except the first one)
                        if idx > 0:
                            log_entries.append("")  # Empty line for visual separation
                        
                        log_entries.append(f"  **{owner_name}:**")

                        for snapshot in owner_snapshots:
                            # Check if this is a commodity account
                            is_commodity = snapshot["account_type"] == "Commodity"
                            
                            if is_commodity:
                                # For commodities, calculate value using the new commodity function
                                commodity_name = snapshot.get("commodity")
                                quantity = snapshot["balance"]
                                
                                # Get unit from snapshot (from database join) or extract from account name as fallback
                                unit = snapshot.get("commodity_unit")
                                if not unit:
                                    # Fallback: extract unit from account name
                                    account_name = snapshot["name"]
                                    unit = "units"
                                    if "(" in account_name and ")" in account_name:
                                        unit = account_name[account_name.rfind("(")+1:account_name.rfind(")")]
                                
                                # Calculate commodity value in base currency using new function
                                converted_value = get_commodity_value(
                                    quantity,
                                    commodity_name,
                                    base_currency,
                                    commodity_prices,
                                    commodity_configs,
                                    unit
                                )
                                
                                # Show balance with unit
                                entry = (
                                    f"    • {snapshot['name']} ({snapshot['account_type']}): "
                                    f"`{snapshot['balance']:,.2f} {unit}` {commodity_name}"
                                )
                                
                                # Always show converted value for commodities
                                entry += f" = `{currency_symbol}{converted_value:,.2f}` {base_currency}"
                            else:
                                # For regular accounts, use currency conversion
                                converted_value = get_converted_value(
                                    snapshot["balance"],
                                    snapshot["currency"],
                                    base_currency,
                                    rates
                                )
                                
                                # Show currency symbol
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

    # Get owners for grouping
    owners = db.get_owners()
    owner_names = [owner['name'] for owner in owners]

    # Balance entry form - grouped by owner
    # Use a unique key based on the selected date to force form recreation when date changes
    form_key = f"balance_form_{selected_year}_{selected_month}"
    with st.form(form_key):
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
                                # Priority: 1) Existing snapshot for the selected month, 2) 0.0
                                default_val = 0.0

                                # Check if existing snapshot has this account for the selected month
                                if account['id'] in existing_snapshot_data:
                                    default_val = float(existing_snapshot_data[account['id']])

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
                                    key=f"balance_{account['id']}_{selected_year}_{selected_month}"
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
