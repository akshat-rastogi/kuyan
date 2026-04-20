"""
KUYAN - Monthly Net Worth Tracker
Mortgage Page Module - Mortgage amortization calculator
Copyright (c) 2025 mycloudcondo inc.
Licensed under MIT License - see LICENSE file for details
"""

import streamlit as st
import pandas as pd
from datetime import date
from io import StringIO
from database import Database
from helper import (
    generate_amortization_schedule,
    prepare_schedule_for_display,
    format_currency
)


def mortgage(db: Database):
    """
    Render the mortgage amortization calculator page.
    
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
        key="mortgage_selector",
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
    recurring_extra_payment = float(selected_mortgage["recurring_extra_payment"])
    currency = selected_mortgage.get("currency", "EUR")
    
    st.info("💡 To modify mortgage details, go to **Settings → Mortgage** tab.")
    
    # Display current mortgage configuration
    st.markdown(f"### Loan Summary — {selected_mortgage_name} ({lender_name})")
    
    with st.expander("📋 View Mortgage Configuration", expanded=False):
        config_col1, config_col2 = st.columns(2)
        
        with config_col1:
            st.write("**Loan Amount:**", format_currency(loan_amount))
            st.write("**Interest Rate:**", f"{interest_rate:.4f}%")
            st.write("**Loan Term:**", f"{loan_term_years:.3f} years")
            st.write("**Currency:**", currency)
        
        with config_col2:
            st.write("**Payments Per Year:**", payments_per_year)
            st.write("**Start Date:**", loan_start_date.strftime("%d/%m/%Y"))
            st.write("**Recurring Extra Payment:**", format_currency(recurring_extra_payment))
        
        st.divider()
        
        # Property value information
        purchase_val = float(selected_mortgage.get("purchase_value", 0.0))
        present_val = float(selected_mortgage.get("present_value", 0.0))
        down_payment = purchase_val - loan_amount
        equity = present_val - loan_amount
        
        prop_col1, prop_col2 = st.columns(2)
        
        with prop_col1:
            st.write("**Purchase Value:**", format_currency(purchase_val))
            st.write("**Down Payment:**", format_currency(down_payment))
        
        with prop_col2:
            st.write("**Present Market Value:**", format_currency(present_val))
            st.write("**Current Equity:**", format_currency(equity))
    
    st.write("#### One-Off / Custom Extra Payments")

    edited_custom_payments = st.data_editor(
        st.session_state[session_key],
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
                f"EXTRA PAYMENT ({currency})",
                min_value=0.0,
                step=100.0,
                format="%.2f",
                help=f"One-off extra payment amount in {currency}."
            )
        },
        key=f"mortgage_custom_payment_editor_{mortgage_id}"
    )

    # Save extra payments to database when they change
    if not edited_custom_payments.equals(st.session_state[session_key]):
        st.session_state[session_key] = edited_custom_payments
        
        # Save to database
        payments_to_save = []
        for _, row in edited_custom_payments.iterrows():
            if pd.notna(row["PMT NO"]) & pd.notna(row["EXTRA PAYMENT"]):
                payments_to_save.append({
                    "payment_number": int(row["PMT NO"]),
                    "extra_payment_amount": float(row["EXTRA PAYMENT"])
                })
        
        db.save_mortgage_extra_payments(mortgage_id, payments_to_save)
    else:
        st.session_state[session_key] = edited_custom_payments

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

    metric_col_1.metric("Scheduled payment", format_currency(summary["scheduled_payment"]))
    metric_col_2.metric("Scheduled number of payments", f'{summary["scheduled_number_of_payments"]:.2f}')
    metric_col_3.metric("Actual number of payments", f'{summary["actual_number_of_payments"]}')

    metric_col_4.metric("Years saved off original loan term", f'{summary["years_saved"]:.3f}')
    metric_col_5.metric("Total early payments", format_currency(summary["total_early_payments"]))
    metric_col_6.metric("Total interest", format_currency(summary["total_interest"]))

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
            custom_lookup = edited_custom_payments.dropna(subset=["PMT NO", "EXTRA PAYMENT"]).copy()

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

# Made with Bob
