"""
KUYAN - History Page Module
Copyright (c) 2025 mycloudcondo inc.
Licensed under MIT License - see LICENSE file for details
"""

import streamlit as st
from datetime import datetime, date
import json
from components import render_data_table
from helper import (
    get_currency_symbol,
    get_default_currency,
    get_converted_value,
    calculate_total_net_worth
)


# ===== CONSTANTS =====
MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


def history(db):
    """
    Render the history page showing account balance history and snapshot logs.
    
    Args:
        db: Database instance
    """
    snapshot_dates = db.get_all_snapshot_dates()

    if not snapshot_dates:
        st.info("No snapshots yet. Create your first monthly snapshot!")
        return

    # Account Balance History section
    st.subheader("📊 Account Balance History (Most recent 3 months)")
    
    accounts = db.get_accounts()
    
    if accounts:
        prev_months = []
        prev_month_data = {}

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

    st.subheader("View all snapshot entries by year")

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
    default_currency = get_default_currency(db)
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
                total = calculate_total_net_worth(snapshots, base_currency, db)

                # Create accordion with month name and total net worth in title
                # Using markdown formatting to preserve the code-style appearance of the amount
                expander_label = f"📌 {month_names[month_num - 1]} {selected_year} - Total Net Worth: `{currency_symbol}{total:,.2f}` ({base_currency})"
                with st.expander(expander_label, expanded=False):
                    # Group snapshots by owner for better organization
                    owners = db.get_owners()
                    owner_names = [owner['name'] for owner in owners]

                    # Display snapshots grouped by owner
                    log_entries = []
                    for idx, owner_name in enumerate(owner_names):
                        owner_snapshots = [s for s in snapshots if s['owner'] == owner_name]

                        if owner_snapshots:
                            # Add line break before each owner (except the first one)
                            if idx > 0:
                                log_entries.append("")  # Empty line for visual separation
                            
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
                    st.markdown("")  # Add spacing
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
        else:
            # No snapshot for this month - show collapsed accordion
            with st.expander(f"⚪ {month_names[month_num - 1]} {selected_year}", expanded=False):
                st.markdown("  *No snapshot recorded*")

