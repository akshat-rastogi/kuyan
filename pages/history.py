"""
KUYAN - History Page Module
Copyright (c) 2025 mycloudcondo inc.
Licensed under MIT License - see LICENSE file for details
"""

import streamlit as st
from datetime import datetime, date
import json
import pandas as pd
from io import StringIO
from components import render_data_table
from helper import (
    get_currency_symbol,
    get_default_currency,
    get_converted_value,
    calculate_total_net_worth,
    generate_amortization_schedule,
    prepare_schedule_for_display,
    format_currency
)


# ===== CONSTANTS =====
MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


def render_mortgage_amortization_tab(db):
    """
    Render the mortgage amortization schedule tab.
    
    Args:
        db: Database instance
    """
    st.markdown("### 🏠 Mortgage Amortization Schedule")
    st.caption("Interactive mortgage amortization calculator with recurring and one-off extra payments.")
    
    # Get all mortgages from database
    all_mortgages = db.get_all_mortgages()
    
    # Check if any mortgages exist
    if not all_mortgages:
        st.warning("⚠️ No mortgages configured. Please configure your mortgage details in Settings → Mortgage tab.")
        st.info("👉 Go to **Settings** page and select the **🏠 Mortgage** tab to add your mortgage details.")
        return
    
    # Create dropdown for mortgage selection
    mortgage_names = [m['mortgage_name'] for m in all_mortgages]
    
    # Initialize selected mortgage in session state
    if "selected_mortgage_name" not in st.session_state:
        st.session_state.selected_mortgage_name = mortgage_names[0]
    
    # Mortgage selector
    selected_mortgage_name = st.selectbox(
        "Select Mortgage",
        options=mortgage_names,
        index=mortgage_names.index(st.session_state.selected_mortgage_name) if st.session_state.selected_mortgage_name in mortgage_names else 0,
        key="mortgage_selector_history",
        help="Select which mortgage to view the amortization schedule for"
    )
    
    # Update session state
    st.session_state.selected_mortgage_name = selected_mortgage_name
    
    # Ensure selected_mortgage_name is not None
    if not selected_mortgage_name:
        st.error("❌ No mortgage selected. Please select a mortgage from the dropdown.")
        return
    
    # Get the selected mortgage details
    selected_mortgage = db.get_mortgage_by_name(selected_mortgage_name)
    
    if not selected_mortgage:
        st.error("❌ Selected mortgage not found. Please refresh the page.")
        return
    
    mortgage_id = selected_mortgage['id']
    
    # Initialize editable one-off payment defaults for this mortgage
    session_key = f"mortgage_custom_payments_{mortgage_id}"
    if session_key not in st.session_state:
        # Try to load from database first
        db_payments = db.get_mortgage_extra_payments(mortgage_id)
        if db_payments:
            payments_data = [
                {"PMT NO": int(p["payment_number"]), "EXTRA PAYMENT": float(p["extra_payment_amount"])}
                for p in db_payments
            ]
            st.session_state[session_key] = pd.DataFrame(payments_data)
        else:
            st.session_state[session_key] = pd.DataFrame(
                {"PMT NO": [], "EXTRA PAYMENT": []}
            )
    
    # Get values from selected mortgage
    lender_name = selected_mortgage["lender_name"]
    loan_amount = float(selected_mortgage["loan_amount"])
    interest_rate = float(selected_mortgage["interest_rate"])
    loan_term_years = float(selected_mortgage["loan_term_years"])
    payments_per_year = int(selected_mortgage["payments_per_year"])
    loan_start_date = date.fromisoformat(selected_mortgage["start_date"]) if isinstance(selected_mortgage["start_date"], str) else selected_mortgage["start_date"]
    defer_months = int(selected_mortgage.get("defer_months", 0))
    recurring_extra_payment = float(selected_mortgage["recurring_extra_payment"])
    currency = selected_mortgage.get("currency", "EUR")
    
    schedule_df, summary = generate_amortization_schedule(
        loan_amount=loan_amount,
        annual_interest_rate=interest_rate,
        loan_term_years=loan_term_years,
        payments_per_year=payments_per_year,
        start_date=loan_start_date,
        defer_months=defer_months,
        recurring_extra_payment=recurring_extra_payment,
        custom_extra_payments=st.session_state[session_key]
    )

    with st.expander("📋 View Mortgage Configuration", expanded=False):
        config_col1, config_col2, config_col3 = st.columns(3)
        
        with config_col1:
            st.write("**Loan Amount:**", format_currency(loan_amount))
            st.write("**Interest Rate:**", f"{interest_rate:.4f}%")
            st.write("**Loan Term:**", f"{loan_term_years:.3f} years")

        with config_col2:
            st.write("**Currency:**", currency)
            st.write("**Payments Per Year:**", payments_per_year)
            st.write("**Start Date:**", loan_start_date.strftime("%d/%m/%Y"))
        
        with config_col3:
            st.write("**Deferred Months:**", defer_months)
            st.write("**Recurring Extra Payment:**", format_currency(recurring_extra_payment))
        
        st.divider()
        
        # Property value information
        purchase_val = float(selected_mortgage.get("purchase_value", 0.0))
        present_val = float(selected_mortgage.get("present_value", 0.0))
        down_payment = purchase_val - loan_amount
        
        prop_col1, prop_col2, prop_col3 = st.columns(3)

        prop_col1.metric("Purchase Value", format_currency(purchase_val))
        prop_col2.metric("Down Payment", format_currency(down_payment))        
        prop_col3.metric("Present Market Value", format_currency(present_val))

        metric_col_1, metric_col_2, metric_col_3 = st.columns(3)
        metric_col_4, metric_col_5, metric_col_6 = st.columns(3)

        metric_col_1.metric("Scheduled payment", format_currency(summary["scheduled_payment"]))
        metric_col_2.metric("Scheduled number of payments", f'{summary["scheduled_number_of_payments"]:.2f}')
        metric_col_3.metric("Actual number of payments", f'{summary["actual_number_of_payments"]}')

        metric_col_4.metric("Years saved off original loan term", f'{summary["years_saved"]:.3f}')
        metric_col_5.metric("Total early payments", format_currency(summary["total_early_payments"]))
        metric_col_6.metric("Total interest", format_currency(summary["total_interest"]))

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
        label=f"Download {selected_mortgage_name}_Amortization_Schedule.csv",
        data=csv_buffer.getvalue(),
        file_name=f"{selected_mortgage_name.replace(' ', '_')}_Amortization_Schedule.csv",
        mime="text/csv",
        type="primary"
    )

    st.dataframe(display_df, width="stretch", hide_index=True)

    if not schedule_df.empty:
        with st.expander("Custom extra payment dates"):
            custom_payment_rows = []
            custom_lookup = st.session_state[session_key].dropna(subset=["PMT NO", "EXTRA PAYMENT"]).copy()

            for _, row in custom_lookup.iterrows():
                payment_no = int(row["PMT NO"])
                extra_payment_amount = float(row["EXTRA PAYMENT"])

                if payment_no > 0 and payment_no <= len(schedule_df):
                    payment_date = schedule_df.loc[schedule_df["PMT NO"] == payment_no, "PAYMENT DATE"].iloc[0]
                    custom_payment_rows.append({
                        "PMT NO": payment_no,
                        "DATE": pd.to_datetime(payment_date).strftime("%Y-%m-%d"),
                        "EXTRA PAYMENT": format_currency(extra_payment_amount)
                    })

            if custom_payment_rows:
                st.dataframe(pd.DataFrame(custom_payment_rows), width="stretch", hide_index=True)
            else:
                st.caption("No valid one-off extra payments configured.")


def render_balance_history_tab(db):
    """
    Render the account balance history tab (most recent 3 months).
    
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


def render_yearly_snapshots_tab(db):
    """
    Render the yearly snapshots tab (view all snapshot entries by year).
    
    Args:
        db: Database instance
    """
    snapshot_dates = db.get_all_snapshot_dates()

    if not snapshot_dates:
        st.info("No snapshots yet. Create your first monthly snapshot!")
        return

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
                                    # Get unit from snapshot (from database join) or extract from account name as fallback
                                    unit = snapshot.get("commodity_unit")
                                    if not unit:
                                        # Fallback: extract unit from account name
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



def history(db):
    """
    Render the history page with tabs for balance history, yearly snapshots, and mortgage amortization.
    
    Args:
        db: Database instance
    """
    # Custom CSS to make tabs larger (consistent with settings page)
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
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📊 Recent History", "📅 Yearly View", "🏠 Mortgage"])
    
    with tab1:
        render_balance_history_tab(db)
    
    with tab2:
        render_yearly_snapshots_tab(db)
    
    with tab3:
        render_mortgage_amortization_tab(db)
