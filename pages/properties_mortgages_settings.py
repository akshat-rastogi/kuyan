"""
KUYAN - Monthly Net Worth Tracker
Properties Settings Page Module - Unified property and mortgage management
Licensed under MIT License - see LICENSE file for details
"""

import streamlit as st
from datetime import date
from database import Database
from helper import format_currency, get_default_currency, get_currency_symbol

def properties_mortgages_settings(db: Database, key_prefix=""):
    """
    Render the unified properties and mortgages configuration settings page.
    
    Args:
        db: Database instance
        key_prefix: Prefix for widget keys to avoid conflicts when used in tabs
    """
    
    st.info("💡 Properties are added from the Accounts page. Select a property from the dropdown to view or edit details.")

    st.divider()
    
    st.subheader("Owned Properties")
    
    # Get all properties from database
    all_properties = db.get_all_properties_with_financials()
    
    # Initialize session state
    if "selected_property_id" not in st.session_state:
        st.session_state.selected_property_id = None
    if "show_new_property_form" not in st.session_state:
        st.session_state.show_new_property_form = False
    
    
    if all_properties and not st.session_state.show_new_property_form:
        # Create property options for dropdown using the exact property/account name
        property_options = {p.get('account_name') or p['property_name']: p['id'] for p in all_properties}
        property_names = list(property_options.keys())
        
        # Find current selection index
        current_index = 0
        if st.session_state.selected_property_id:
            for idx, (_, pid) in enumerate(property_options.items()):
                if pid == st.session_state.selected_property_id:
                    current_index = idx
                    break
        
        previous_property_id = st.session_state.selected_property_id
        selected_property_name = st.selectbox(
            "Select Property",
            options=property_names,
            index=current_index,
            key=f"{key_prefix}property_selector",
            help="Choose a property to view or edit"
        )
        
        # Update selected property ID when selection changes
        selected_property_id = property_options[selected_property_name]
        if previous_property_id != selected_property_id:
            # Clear mortgage session state to reload for new property
            st.session_state.pop("property_form_mortgages", None)
            st.session_state.pop("current_property_id", None)
        st.session_state.selected_property_id = selected_property_id
        st.session_state.show_new_property_form = False
    else:
        st.write("")
    
    st.divider()
    
    # Get enabled currencies and owners for selectors
    enabled_currencies = db.get_currencies()
    currency_codes = [curr['code'] for curr in enabled_currencies]
    owner_names = db.get_owner_names()
    
    property_types = ["Residential", "Commercial", "Land", "Investment", "Vacation", "Other"]
    valuation_types = ["Purchase Price", "Market Appraisal", "Tax Assessment", "Online Estimate", "Professional Valuation", "Other"]
    
    # Show property form (either new or existing)
    if st.session_state.show_new_property_form:
        # NEW PROPERTY FORM
        render_property_form(
            db=db,
            property_data=None,
            currency_codes=currency_codes,
            owner_names=owner_names,
            property_types=property_types,
            valuation_types=valuation_types,
            key_prefix=key_prefix,
            is_new=True
        )
    elif st.session_state.selected_property_id:
        # EXISTING PROPERTY FORM
        property_data = next((p for p in all_properties if p['id'] == st.session_state.selected_property_id), None)
        if property_data:
            render_property_form(
                db=db,
                property_data=property_data,
                currency_codes=currency_codes,
                owner_names=owner_names,
                property_types=property_types,
                valuation_types=valuation_types,
                key_prefix=key_prefix,
                is_new=False
            )
    else:
        st.info("📝 No properties configured yet. Add a Property account from the Accounts page to get started.")


def render_property_form(db, property_data, currency_codes, owner_names, property_types, valuation_types, key_prefix, is_new):
    """Render the property form for new or existing property"""
    
    # Set default values for new property
    if is_new:
        property_id = None
        property_name = ""
        property_type = "Residential"
        address = ""
        owner = owner_names[0] if owner_names else "Me"
        currency = get_default_currency(db)
        latest_value = 0.0
        latest_valuation_date = None
        valuation_type = "Market Appraisal"
        property_mortgages = []
        purchase_price_asset = None
    else:
        property_id = property_data['id']
        property_name = property_data['property_name']
        property_type = property_data['property_type']
        address = property_data.get('address', '')
        owner = property_data['owner']
        currency = property_data['currency']
        latest_value = float(property_data.get('latest_value', 0.0)) if property_data.get('latest_value') else 0.0
        latest_valuation_date = property_data.get('latest_valuation_date')
        valuation_type = property_data.get('valuation_type', 'Market Appraisal')
        property_mortgages = property_data.get('mortgages', [])
        
        # Get purchase price from property assets if it exists
        all_assets = db.get_property_assets(property_id)
        purchase_price_asset = next((a for a in all_assets if a['valuation_type'] == 'Purchase Price'), None)
    
    # Initialize mortgage list in session state
    mortgage_key = f"property_form_mortgages"
    if mortgage_key not in st.session_state or st.session_state.get('current_property_id') != property_id:
        st.session_state[mortgage_key] = property_mortgages.copy()
        st.session_state['current_property_id'] = property_id
    
    # Property basic information
    st.markdown("#### 📋 Property Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_property_name = st.text_input(
            "Property Name",
            value=property_name,
            key=f"{key_prefix}property_name_form_{property_id}",
            help="Give this property a unique name",
            placeholder="e.g., Main Residence, Beach House"
        )
        
        new_property_type = st.selectbox(
            "Property Type",
            options=property_types,
            index=property_types.index(property_type) if property_type in property_types else 0,
            key=f"{key_prefix}property_type_form_{property_id}",
            help="Type of property"
        )
        
        new_owner = st.selectbox(
            "Owner",
            options=owner_names,
            index=owner_names.index(owner) if owner in owner_names else 0,
            key=f"{key_prefix}property_owner_form_{property_id}",
            help="Property owner"
        )
    
    with col2:
        new_address = st.text_area(
            "Address",
            value=address,
            key=f"{key_prefix}property_address_form_{property_id}",
            help="Property address",
            height=100,
            placeholder="Enter full address"
        )
        
        try:
            currency_index = currency_codes.index(currency)
        except ValueError:
            currency_index = 0
        
        new_currency = st.selectbox(
            "Currency",
            options=currency_codes,
            index=currency_index,
            key=f"{key_prefix}property_currency_form_{property_id}",
            help="Currency for property values"
        ) or "EUR"
    
    # Purchase Price section
    st.markdown("**Purchase Price** (Original acquisition cost)")
    col_pp1, col_pp2 = st.columns(2)
    
    with col_pp1:
        purchase_date = st.date_input(
            "Purchase Date",
            value=date.fromisoformat(purchase_price_asset['valuation_date']) if purchase_price_asset else date.today(),
            key=f"{key_prefix}purchase_date_form_{property_id}",
            help="Date when the property was purchased"
        )
    
    with col_pp2:
        purchase_price = st.number_input(
            f"Purchase Price ({new_currency})",
            min_value=0.0,
            value=float(purchase_price_asset['market_value']) if purchase_price_asset else 0.0,
            step=1000.0,
            format="%.2f",
            key=f"{key_prefix}purchase_price_form_{property_id}",
            help="Original purchase price of the property"
        )
    
    purchase_notes = st.text_area(
        "Purchase Notes (Optional)",
        value=purchase_price_asset['notes'] if purchase_price_asset and purchase_price_asset.get('notes') else "",
        key=f"{key_prefix}purchase_notes_form_{property_id}",
        help="Additional notes about the purchase",
        height=60
    )
        
    # Current Market Value section
    st.markdown("**Current Market Value** (Latest valuation)")
    col3, col4, col5 = st.columns(3)
    
    with col3:
        new_valuation_date = st.date_input(
            "Valuation Date",
            value=date.fromisoformat(latest_valuation_date) if latest_valuation_date and isinstance(latest_valuation_date, str) else date.today(),
            key=f"{key_prefix}valuation_date_form_{property_id}",
            help="Date of property valuation"
        )
    
    with col4:
        new_market_value = st.number_input(
            f"Market Value ({new_currency})",
            min_value=0.0,
            value=latest_value,
            step=1000.0,
            format="%.2f",
            key=f"{key_prefix}market_value_form_{property_id}",
            help="Current market value of the property"
        )
    
    with col5:
        new_valuation_type = st.selectbox(
            "Valuation Type",
            options=valuation_types,
            index=valuation_types.index(valuation_type) if valuation_type in valuation_types else 1,
            key=f"{key_prefix}valuation_type_form_{property_id}",
            help="Type of valuation"
        )
    
    new_valuation_notes = st.text_area(
        "Valuation Notes (Optional)",
        value="",
        key=f"{key_prefix}valuation_notes_form_{property_id}",
        help="Additional notes about this valuation",
        height=60,
        placeholder="Add any relevant notes about the valuation"
    )
    
    col_save, col_cancel = st.columns([1, 1])
    
    with col_save:
        save_label = "💾 Save Property" if is_new else f"💾 Update Property"
        if st.button(save_label, key=f"{key_prefix}save_property_form_{property_id}", type="primary", use_container_width=True):
            if not new_property_name:
                st.error("❌ Property name is required!")
            else:
                # Save or update property
                if is_new:
                    # Add new property
                    property_id = db.add_property(
                        property_name=new_property_name,
                        property_type=new_property_type,
                        address=new_address or "",
                        owner=new_owner,
                        currency=new_currency
                    )
                else:
                    # Update existing property
                    db.update_property(
                        property_id=property_id,
                        property_name=new_property_name,
                        property_type=new_property_type,
                        address=new_address or "",
                        owner=new_owner,
                        currency=new_currency
                    )
                
                # Save purchase price as a property asset (if provided)
                if purchase_price > 0:
                    # Check if purchase price already exists
                    if purchase_price_asset:
                        # Update existing purchase price
                        db.update_property_asset(
                            asset_id=purchase_price_asset['id'],
                            valuation_date=purchase_date,
                            market_value=purchase_price,
                            valuation_type="Purchase Price",
                            notes=purchase_notes
                        )
                    else:
                        # Add new purchase price
                        db.add_property_asset(
                            property_id=property_id,
                            valuation_date=purchase_date,
                            market_value=purchase_price,
                            valuation_type="Purchase Price",
                            notes=purchase_notes
                        )
                
                # Save current market valuation (if different from purchase price)
                if new_market_value > 0 and new_valuation_type != "Purchase Price":
                    db.add_property_asset(
                        property_id=property_id,
                        valuation_date=new_valuation_date,
                        market_value=new_market_value,
                        valuation_type=new_valuation_type,
                        notes=new_valuation_notes
                    )
                
                st.success(f"✅ Property {new_property_name} updated successfully!")
                
                # Reset form state
                st.session_state.show_new_property_form = False
                st.session_state.selected_property_id = property_id
                st.rerun()
    
    with col_cancel:
        if st.button("❌ Cancel", key=f"{key_prefix}cancel_property_form_{property_id}", use_container_width=True):
            st.session_state.show_new_property_form = False
            if not is_new:
                st.session_state.selected_property_id = property_id
            st.rerun()
    
    st.divider()
    
    # Mortgages section
    st.markdown("#### 🏦 Mortgages for This Property")
    
    # Add mortgage button
    if st.button(f"➕ Add Mortgage", key=f"{key_prefix}add_mortgage_form_{property_id}", use_container_width=True):
        # Generate unique mortgage name
        existing_mortgage_names = [m.get('mortgage_name', '') for m in st.session_state[mortgage_key]]
        counter = len(st.session_state[mortgage_key]) + 1
        new_mortgage_name = f"{new_property_name or 'Property'} Mortgage {counter}"
        while new_mortgage_name in existing_mortgage_names:
            counter += 1
            new_mortgage_name = f"{new_property_name or 'Property'} Mortgage {counter}"
        
        # Add new mortgage
        new_mortgage = {
            "id": None,
            "mortgage_name": new_mortgage_name,
            "lender_name": "",
            "loan_amount": 0.0,
            "interest_rate": 0.0,
            "loan_term_years": 30.0,
            "payments_per_year": 12,
            "start_date": date.today(),
            "defer_months": 0,
            "recurring_extra_payment": 0.0,
            "currency": new_currency
        }
        st.session_state[mortgage_key].append(new_mortgage)
        st.rerun()
    
    # Display mortgages in accordions
    if st.session_state[mortgage_key]:
        for mort_idx, mortgage in enumerate(st.session_state[mortgage_key]):
            with st.expander(f"🏦 {mortgage.get('mortgage_name', f'Mortgage {mort_idx + 1}')}", expanded=(mort_idx == -1)):
                mort_col1, mort_col2 = st.columns(2)
                
                with mort_col1:
                    mortgage_name = st.text_input(
                        "Mortgage Name",
                        value=mortgage.get("mortgage_name", ""),
                        key=f"{key_prefix}mortgage_name_form_{property_id}_{mort_idx}",
                        help="Name for this mortgage"
                    )
                    
                    lender_name = st.text_input(
                        "Lender Name",
                        value=mortgage.get("lender_name", ""),
                        key=f"{key_prefix}lender_name_form_{property_id}_{mort_idx}",
                        help="Name of your mortgage lender or bank"
                    )
                    
                    loan_amount = st.number_input(
                        f"Loan Amount ({new_currency})",
                        min_value=0.0,
                        value=float(mortgage.get("loan_amount", 0.0)),
                        step=1000.0,
                        format="%.2f",
                        key=f"{key_prefix}loan_amount_form_{property_id}_{mort_idx}",
                        help=f"Total mortgage loan amount in {new_currency}"
                    )
                    
                    interest_rate = st.number_input(
                        "Interest Rate (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=float(mortgage.get("interest_rate", 0.0)),
                        step=0.01,
                        format="%.4f",
                        key=f"{key_prefix}interest_rate_form_{property_id}_{mort_idx}",
                        help="Annual interest rate as a percentage"
                    )
                
                with mort_col2:
                    loan_term_years = st.number_input(
                        "Loan Term in Years",
                        min_value=0.0,
                        max_value=50.0,
                        value=float(mortgage.get("loan_term_years", 30.0)),
                        step=0.1,
                        format="%.4f",
                        key=f"{key_prefix}loan_term_years_form_{property_id}_{mort_idx}",
                        help="Original loan term in years"
                    )
                    
                    payments_per_year = st.number_input(
                        "Payments Per Year",
                        min_value=1,
                        max_value=365,
                        value=int(mortgage.get("payments_per_year", 12)),
                        step=1,
                        key=f"{key_prefix}payments_per_year_form_{property_id}_{mort_idx}",
                        help="Number of payments per year (typically 12)"
                    )
                    
                    start_date_value = mortgage.get("start_date", date.today())
                    if isinstance(start_date_value, str):
                        start_date_value = date.fromisoformat(start_date_value)
                    
                    start_date = st.date_input(
                        "Loan Start Date",
                        value=start_date_value,
                        key=f"{key_prefix}start_date_form_{property_id}_{mort_idx}",
                        help="Date when the mortgage started"
                    )
                    
                    defer_months = st.number_input(
                        "Defer Payments By (Months)",
                        min_value=0,
                        max_value=120,
                        value=int(mortgage.get("defer_months", 0)),
                        step=1,
                        key=f"{key_prefix}defer_months_form_{property_id}_{mort_idx}",
                        help="Number of months to defer payments"
                    )
                
                recurring_extra_payment = st.number_input(
                    f"Optional Extra Payments ({new_currency})",
                    min_value=0.0,
                    value=float(mortgage.get("recurring_extra_payment", 0.0)),
                    step=100.0,
                    format="%.2f",
                    key=f"{key_prefix}recurring_extra_payment_form_{property_id}_{mort_idx}",
                    help="Additional amount to pay with each regular payment"
                )
                
                # Update mortgage data in session state
                mortgage['mortgage_name'] = mortgage_name
                mortgage['lender_name'] = lender_name
                mortgage['loan_amount'] = loan_amount
                mortgage['interest_rate'] = interest_rate
                mortgage['loan_term_years'] = loan_term_years
                mortgage['payments_per_year'] = payments_per_year
                mortgage['start_date'] = start_date
                mortgage['defer_months'] = defer_months
                mortgage['recurring_extra_payment'] = recurring_extra_payment
                mortgage['currency'] = new_currency
                
                # Mortgage action buttons
                mort_btn_col1, mort_btn_col2 = st.columns([1, 1])
                
                with mort_btn_col1:
                    if st.button(f"💾 Update Mortgage", key=f"{key_prefix}update_mortgage_form_{property_id}_{mort_idx}", type="primary", use_container_width=True):
                        if not mortgage_name:
                            st.error("❌ Mortgage name is required!")
                        else:
                            if mortgage.get('id'):
                                # Update existing mortgage
                                db.update_mortgage(
                                    mortgage_id=mortgage['id'],
                                    mortgage_name=mortgage['mortgage_name'],
                                    lender_name=mortgage['lender_name'],
                                    loan_amount=mortgage['loan_amount'],
                                    interest_rate=mortgage['interest_rate'],
                                    loan_term_years=mortgage['loan_term_years'],
                                    payments_per_year=mortgage['payments_per_year'],
                                    start_date=mortgage['start_date'],
                                    defer_months=mortgage['defer_months'],
                                    recurring_extra_payment=mortgage['recurring_extra_payment'],
                                    currency=new_currency
                                )
                                st.success(f"✅ Mortgage '{mortgage_name}' updated successfully!")
                            else:
                                # Add new mortgage
                                mort_id = db.add_mortgage(
                                    mortgage_name=mortgage['mortgage_name'],
                                    lender_name=mortgage['lender_name'],
                                    loan_amount=mortgage['loan_amount'],
                                    interest_rate=mortgage['interest_rate'],
                                    loan_term_years=mortgage['loan_term_years'],
                                    payments_per_year=mortgage['payments_per_year'],
                                    start_date=mortgage['start_date'],
                                    defer_months=mortgage['defer_months'],
                                    recurring_extra_payment=mortgage['recurring_extra_payment'],
                                    currency=new_currency
                                )
                                mortgage['id'] = mort_id
                                
                                # Link mortgage to property
                                db.link_mortgage_to_property(property_id, mort_id)
                                st.success(f"✅ Mortgage '{mortgage_name}' saved successfully!")
                            st.rerun()
                
                with mort_btn_col2:
                    if st.button(f"🗑️ Delete This Mortgage", key=f"{key_prefix}delete_mortgage_form_{property_id}_{mort_idx}", use_container_width=True):
                        if mortgage.get('id'):
                            db.delete_mortgage(mortgage['id'])
                        st.session_state[mortgage_key].pop(mort_idx)
                        st.rerun()
    else:
        st.info("No mortgages added yet. Click 'Add Mortgage' to add one.")

# Made with Bob
