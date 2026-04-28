"""
KUYAN - Monthly Net Worth Tracker
Mortgage Page Module - Mortgage amortization calculator
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
    
    # Get all properties with mortgages
    all_properties = db.get_all_properties_with_financials()
    
    # Filter properties that have mortgages
    properties_with_mortgages = [p for p in all_properties if p.get('mortgages')]
    
    # Check if any properties with mortgages exist
    if not properties_with_mortgages:
        st.warning("⚠️ No properties with mortgages configured. Please configure your properties and mortgages in Settings → Properties tab.")
        st.info("👉 Go to **Settings** page and select the **🏘️ Properties** tab to add properties and their mortgages.")
        return
    
    # Create property dropdown
    property_names = [p['property_name'] for p in properties_with_mortgages]
    property_map = {p['property_name']: p for p in properties_with_mortgages}
    
    # Initialize selected property in session state
    if "selected_property_name_update" not in st.session_state:
        st.session_state.selected_property_name_update = property_names[0]
    
    # Property selector
    col1, col2 = st.columns([1, 1])
    
    with col1:
        selected_property_name = st.selectbox(
            "Select Property",
            options=property_names,
            index=property_names.index(st.session_state.selected_property_name_update) if st.session_state.selected_property_name_update in property_names else 0,
            key="property_selector_update",
            help="Select which property to view mortgages for"
        )
    
    # Update session state
    st.session_state.selected_property_name_update = selected_property_name
    
    # Get the selected property
    selected_property = property_map.get(selected_property_name)
    
    if not selected_property:
        st.error("❌ Selected property not found. Please refresh the page.")
        return
    
    # Get mortgages for the selected property
    property_mortgages = selected_property.get('mortgages', [])
    
    if not property_mortgages:
        st.warning(f"⚠️ No mortgages found for {selected_property_name}.")
        return
    
    # Create mortgage dropdown for the selected property
    mortgage_names = [m['mortgage_name'] for m in property_mortgages]
    mortgage_map = {m['mortgage_name']: m for m in property_mortgages}
    
    # Initialize selected mortgage in session state
    mortgage_session_key = f"selected_mortgage_name_update_{selected_property['id']}"
    if mortgage_session_key not in st.session_state:
        st.session_state[mortgage_session_key] = mortgage_names[0]
    
    # Ensure the selected mortgage is still valid for this property
    if st.session_state[mortgage_session_key] not in mortgage_names:
        st.session_state[mortgage_session_key] = mortgage_names[0]
    
    # Mortgage selector
    with col2:
        selected_mortgage_name = st.selectbox(
            "Select Mortgage",
            options=mortgage_names,
            index=mortgage_names.index(st.session_state[mortgage_session_key]) if st.session_state[mortgage_session_key] in mortgage_names else 0,
            key=f"mortgage_selector_update_{selected_property['id']}",
            help="Select which mortgage to view the amortization schedule for"
        )
    
    # Update session state
    st.session_state[mortgage_session_key] = selected_mortgage_name
    
    # Get the selected mortgage details
    selected_mortgage = mortgage_map.get(selected_mortgage_name)
    
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
    loan_amount = float(selected_mortgage["loan_amount"])
    interest_rate = float(selected_mortgage["interest_rate"])
    loan_term_years = float(selected_mortgage["loan_term_years"])
    payments_per_year = int(selected_mortgage["payments_per_year"])
    loan_start_date = date.fromisoformat(selected_mortgage["start_date"]) if isinstance(selected_mortgage["start_date"], str) else selected_mortgage["start_date"]
    defer_months = int(selected_mortgage.get("defer_months", 0))
    recurring_extra_payment = float(selected_mortgage["recurring_extra_payment"])
    currency = selected_mortgage.get("currency", "EUR")
    
    # Show property information
    with st.expander("🏘️ Property Information", expanded=False):
        st.markdown(f"**Property:** {selected_property['property_name']}")
        if selected_property.get('address'):
            st.markdown(f"**Address:** {selected_property['address']}")
        st.markdown(f"**Owner:** {selected_property['owner']}")
        
        # Get latest property asset value
        latest_asset = db.get_latest_property_asset(selected_property['id'])
        if latest_asset:
            present_val = float(latest_asset['market_value'])
            valuation_date = latest_asset['valuation_date']
            valuation_type = latest_asset['valuation_type']
            
            st.divider()
            st.markdown("**Property Valuation:**")
            st.write(f"Market Value: {format_currency(present_val, currency)} ({valuation_type})")
            st.write(f"Valuation Date: {valuation_date}")
    
    st.info("💡 To modify mortgage details, go to **Settings → Properties** tab.")

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
        defer_months=defer_months,
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

