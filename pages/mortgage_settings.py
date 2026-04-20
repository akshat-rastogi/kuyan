"""
KUYAN - Monthly Net Worth Tracker
Mortgage Settings Page Module - Configure mortgage details
Copyright (c) 2025 mycloudcondo inc.
Licensed under MIT License - see LICENSE file for details
"""

import streamlit as st
from datetime import date
from database import Database
from helper import format_currency, get_default_currency

def mortgage_settings(db: Database, key_prefix=""):
    """
    Render the mortgage configuration settings page.
    
    Args:
        db: Database instance
        key_prefix: Prefix for widget keys to avoid conflicts when used in tabs
    """
    st.subheader("🏠 Mortgage Configuration")
    st.caption("Configure your mortgage details. These settings will be used in the Mortgage page.")
    
    # Get all mortgages from database
    all_mortgages = db.get_all_mortgages()
    
    # Initialize session state for managing mortgages
    if "mortgage_list" not in st.session_state:
        if all_mortgages:
            st.session_state.mortgage_list = all_mortgages
        else:
            st.session_state.mortgage_list = []
    
    st.info("💡 Add and configure multiple mortgages below. Each mortgage can have its own settings and amortization schedule.")
    
    # Add new mortgage button
    col_add, col_space = st.columns([1, 3])
    with col_add:
        if st.button("➕ Add New Mortgage", key=f"{key_prefix}add_mortgage_btn", type="primary", use_container_width=True):
            # Generate a unique default name
            existing_names = [m.get('mortgage_name', '') for m in st.session_state.mortgage_list]
            counter = len(st.session_state.mortgage_list) + 1
            new_name = f"Mortgage {counter}"
            while new_name in existing_names:
                counter += 1
                new_name = f"Mortgage {counter}"
            
            # Add new mortgage to session state (will be saved when user clicks save)
            new_mortgage = {
                "id": None,  # Will be assigned when saved
                "mortgage_name": new_name,
                "lender_name": "",
                "loan_amount": 0.0,
                "interest_rate": 0.0,
                "loan_term_years": 0.0,
                "payments_per_year": 12,
                "start_date": date.today(),
                "defer_months": 0,
                "recurring_extra_payment": 0.0,
                "purchase_value": 0.0,
                "present_value": 0.0,
                "currency": get_default_currency(db)
            }
            st.session_state.mortgage_list.append(new_mortgage)
            st.rerun()
    
    st.divider()
    
    # Display mortgages in accordions
    if not st.session_state.mortgage_list:
        st.info("📝 No mortgages configured yet. Click 'Add New Mortgage' to get started.")
    else:
        # Get enabled currencies for the currency selector
        enabled_currencies = db.get_currencies()
        currency_codes = [curr['code'] for curr in enabled_currencies]
        
        for idx, mortgage in enumerate(st.session_state.mortgage_list):
            mortgage_id = mortgage.get('id')
            mortgage_name = mortgage.get('mortgage_name', f'Mortgage {idx + 1}')
            
            # Create accordion for each mortgage
            with st.expander(f"🏠 {mortgage_name}", expanded=(idx == 0)):
                # Mortgage name input
                new_mortgage_name = st.text_input(
                    "Mortgage Name",
                    value=mortgage_name,
                    key=f"{key_prefix}mortgage_name_{idx}",
                    help="Give this mortgage a unique name (e.g., 'Primary Home', 'Rental Property')"
                )
                
                # Create two columns for better layout
                col1, col2 = st.columns(2)
                
                with col1:
                    lender_name = st.text_input(
                        "Lender Name",
                        value=mortgage.get("lender_name", ""),
                        key=f"{key_prefix}lender_name_{idx}",
                        help="Name of your mortgage lender or bank"
                    )
                    
                    # Currency selector
                    current_currency = mortgage.get("currency", "EUR")
                    try:
                        currency_index = currency_codes.index(current_currency)
                    except ValueError:
                        currency_index = 0
                    
                    selected_currency = st.selectbox(
                        "Mortgage Currency",
                        options=currency_codes,
                        index=currency_index,
                        key=f"{key_prefix}mortgage_currency_{idx}",
                        help="Currency in which the mortgage is denominated"
                    )
                    
                    loan_amount = st.number_input(
                        f"Loan Amount ({selected_currency})",
                        min_value=0.0,
                        value=float(mortgage.get("loan_amount", 0.0)),
                        step=1000.0,
                        format="%.2f",
                        key=f"{key_prefix}loan_amount_{idx}",
                        help=f"Total mortgage loan amount in {selected_currency}"
                    )
                    
                    interest_rate = st.number_input(
                        "Interest Rate (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=float(mortgage.get("interest_rate", 0.0)),
                        step=0.01,
                        format="%.4f",
                        key=f"{key_prefix}interest_rate_{idx}",
                        help="Annual interest rate as a percentage (e.g., 3.55 for 3.55%)"
                    )
                    
                    loan_term_years = st.number_input(
                        "Loan Term in Years",
                        min_value=0.0,
                        max_value=50.0,
                        value=float(mortgage.get("loan_term_years", 0.0)),
                        step=0.1,
                        format="%.4f",
                        key=f"{key_prefix}loan_term_years_{idx}",
                        help="Original loan term in years (can include decimals)"
                    )
                
                with col2:
                    payments_per_year = st.number_input(
                        "Payments Made Per Year",
                        min_value=1,
                        max_value=365,
                        value=int(mortgage.get("payments_per_year", 12)),
                        step=1,
                        key=f"{key_prefix}payments_per_year_{idx}",
                        help="Number of payments per year (typically 12 for monthly)"
                    )
                    
                    # Handle start_date - convert from string if needed
                    start_date_value = mortgage.get("start_date", date.today())
                    if isinstance(start_date_value, str):
                        start_date_value = date.fromisoformat(start_date_value)
                    
                    start_date = st.date_input(
                        "Loan Start Date",
                        value=start_date_value,
                        key=f"{key_prefix}start_date_{idx}",
                        help="Date when the mortgage/loan started"
                    )
                    
                    defer_months = st.number_input(
                        "Defer Payments By (Months)",
                        min_value=0,
                        max_value=120,
                        value=int(mortgage.get("defer_months", 0)),
                        step=1,
                        key=f"{key_prefix}defer_months_{idx}",
                        help="Number of months to defer payments after loan start date (0 = payments start immediately)"
                    )
                    
                    recurring_extra_payment = st.number_input(
                        f"Optional Extra Payments ({selected_currency})",
                        min_value=0.0,
                        value=float(mortgage.get("recurring_extra_payment", 0.0)),
                        step=100.0,
                        format="%.2f",
                        key=f"{key_prefix}recurring_extra_payment_{idx}",
                        help="Additional amount to pay with each regular payment"
                    )
                
                st.markdown("#### 🏡 Property Value Information")
                
                col3, col4 = st.columns(2)
                
                with col3:
                    purchase_value = st.number_input(
                        f"Purchase Value ({selected_currency})",
                        min_value=0.0,
                        value=float(mortgage.get("purchase_value", 0.0)),
                        step=1000.0,
                        format="%.2f",
                        key=f"{key_prefix}purchase_value_{idx}",
                        help="Original purchase price of the property"
                    )
                
                with col4:
                    present_value = st.number_input(
                        f"Present Market Value ({selected_currency})",
                        min_value=0.0,
                        value=float(mortgage.get("present_value", 0.0)),
                        step=1000.0,
                        format="%.2f",
                        key=f"{key_prefix}present_value_{idx}",
                        help="Current estimated market value of the property"
                    )
                
                st.divider()
                
                # Action buttons for this mortgage
                col_save, col_delete = st.columns([1, 1])
                
                with col_save:
                    if st.button(f"💾 Save {mortgage_name}", key=f"{key_prefix}save_mortgage_{idx}", type="primary", use_container_width=True):
                        # Ensure mortgage_name is not empty
                        final_mortgage_name = new_mortgage_name if new_mortgage_name else f"Mortgage {idx + 1}"
                        final_lender_name = lender_name if lender_name else "Bank"
                        final_currency = selected_currency if selected_currency else "EUR"
                        
                        # Update or insert mortgage
                        if mortgage_id:
                            # Update existing mortgage
                            db.update_mortgage(
                                mortgage_id=mortgage_id,
                                mortgage_name=final_mortgage_name,
                                lender_name=final_lender_name,
                                loan_amount=loan_amount,
                                interest_rate=interest_rate,
                                loan_term_years=loan_term_years,
                                payments_per_year=payments_per_year,
                                start_date=start_date,
                                defer_months=defer_months,
                                recurring_extra_payment=recurring_extra_payment,
                                purchase_value=purchase_value,
                                present_value=present_value,
                                currency=final_currency
                            )
                            st.success(f"✅ {final_mortgage_name} updated successfully!")
                        else:
                            # Add new mortgage
                            new_id = db.add_mortgage(
                                mortgage_name=final_mortgage_name,
                                lender_name=final_lender_name,
                                loan_amount=loan_amount,
                                interest_rate=interest_rate,
                                loan_term_years=loan_term_years,
                                payments_per_year=payments_per_year,
                                start_date=start_date,
                                defer_months=defer_months,
                                recurring_extra_payment=recurring_extra_payment,
                                purchase_value=purchase_value,
                                present_value=present_value,
                                currency=final_currency
                            )
                            mortgage['id'] = new_id
                            st.success(f"✅ {final_mortgage_name} saved successfully!")
                        
                        # Update session state
                        mortgage['mortgage_name'] = final_mortgage_name
                        mortgage['lender_name'] = final_lender_name
                        mortgage['loan_amount'] = loan_amount
                        mortgage['interest_rate'] = interest_rate
                        mortgage['loan_term_years'] = loan_term_years
                        mortgage['payments_per_year'] = payments_per_year
                        mortgage['start_date'] = start_date
                        mortgage['defer_months'] = defer_months
                        mortgage['recurring_extra_payment'] = recurring_extra_payment
                        mortgage['purchase_value'] = purchase_value
                        mortgage['present_value'] = present_value
                        mortgage['currency'] = final_currency
                        
                        st.info("📊 Go to the Mortgage page to view the amortization schedule.")
                
                with col_delete:
                    if st.button(f"🗑️ Delete {mortgage_name}", key=f"{key_prefix}delete_mortgage_{idx}", use_container_width=True):
                        if mortgage_id:
                            db.delete_mortgage(mortgage_id)
                            st.success(f"✅ {mortgage_name} deleted successfully!")
                        st.session_state.mortgage_list.pop(idx)
                        st.rerun()
                
                # Display summary for this mortgage
                st.markdown("##### 📋 Summary")
                summary_col1, summary_col2 = st.columns(2)
                
                with summary_col1:
                    st.metric("Lender", mortgage.get("lender_name", "Not set"))
                    st.metric("Loan Amount", format_currency(mortgage.get("loan_amount", 0.0)))
                    st.metric("Interest Rate", f"{mortgage.get('interest_rate', 0.0):.4f}%")
                
                with summary_col2:
                    st.metric("Loan Term", f"{mortgage.get('loan_term_years', 0.0):.3f} years")
                    st.metric("Payments Per Year", mortgage.get("payments_per_year", 12))
                    st.metric("Extra Payments", format_currency(mortgage.get("recurring_extra_payment", 0.0)))
                
                # Property value summary
                purchase_val = mortgage.get("purchase_value", 0.0)
                present_val = mortgage.get("present_value", 0.0)
                down_payment = purchase_val - mortgage.get("loan_amount", 0.0)
                
                prop_col1, prop_col2, prop_col3 = st.columns(3)
                
                with prop_col1:
                    st.metric("Purchase Value", format_currency(purchase_val))
                
                with prop_col2:
                    st.metric("Present Market Value", format_currency(present_val))
                
                with prop_col3:
                    st.metric("Down Payment", format_currency(down_payment))

# Made with Bob
