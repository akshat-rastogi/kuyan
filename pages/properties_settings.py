"""
KUYAN - Monthly Net Worth Tracker
Properties Settings Page Module - Configure properties and their assets/liabilities
Licensed under MIT License - see LICENSE file for details
"""

import streamlit as st
from datetime import date
from database import Database
from helper import format_currency, get_default_currency, get_currency_symbol

def properties_settings(db: Database, key_prefix=""):
    """
    Render the properties configuration settings page.
    
    Args:
        db: Database instance
        key_prefix: Prefix for widget keys to avoid conflicts when used in tabs
    """
    st.subheader("🏘️ Properties & Real Estate")
    st.caption("Manage your properties, track their values, and link mortgages to properties.")
    
    # Get all properties from database
    all_properties = db.get_all_properties_with_financials()
    
    # Initialize session state
    if "selected_property_id" not in st.session_state:
        st.session_state.selected_property_id = None
    if "show_new_property_form" not in st.session_state:
        st.session_state.show_new_property_form = False
    
    st.info("💡 Select a property from the dropdown to view/edit, or add a new property.")
    
    # Top section: Property selector and Add New button
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if all_properties and not st.session_state.show_new_property_form:
            # Create property options for dropdown
            property_options = {f"{p['property_name']} ({p['property_type']})": p['id'] for p in all_properties}
            property_names = list(property_options.keys())
            
            # Find current selection index
            current_index = 0
            if st.session_state.selected_property_id:
                for idx, (name, pid) in enumerate(property_options.items()):
                    if pid == st.session_state.selected_property_id:
                        current_index = idx
                        break
            
            selected_property_name = st.selectbox(
                "Select Property",
                options=property_names,
                index=current_index,
                key=f"{key_prefix}property_selector",
                help="Choose a property to view or edit"
            )
            
            # Update selected property ID
            st.session_state.selected_property_id = property_options[selected_property_name]
            st.session_state.show_new_property_form = False
        else:
            st.info("📝 No properties yet or adding new property")
    
    with col2:
        if st.button("➕ Add New Property", key=f"{key_prefix}add_property_btn", type="primary", use_container_width=True):
            st.session_state.show_new_property_form = True
            st.session_state.selected_property_id = None
            st.rerun()
    
    st.divider()
    
    # Get enabled currencies and owners for selectors
    enabled_currencies = db.get_currencies()
    currency_codes = [curr['code'] for curr in enabled_currencies]
    owner_names = db.get_owner_names()
    all_mortgages = db.get_all_mortgages()
    
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
            all_mortgages=all_mortgages,
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
                all_mortgages=all_mortgages,
                property_types=property_types,
                valuation_types=valuation_types,
                key_prefix=key_prefix,
                is_new=False
            )
    else:
        st.info("📝 No properties configured yet. Click 'Add New Property' to get started.")


def render_property_form(db, property_data, currency_codes, owner_names, all_mortgages, property_types, valuation_types, key_prefix, is_new):
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
        linked_mortgages = []
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
        linked_mortgages = property_data.get('mortgages', [])
    
    # Property basic information
    st.markdown("#### 📋 Property Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_property_name = st.text_input(
            "Property Name",
            value=property_name,
            key=f"{key_prefix}property_name_form",
            help="Give this property a unique name",
            placeholder="e.g., Main Residence, Beach House"
        )
        
        new_property_type = st.selectbox(
            "Property Type",
            options=property_types,
            index=property_types.index(property_type) if property_type in property_types else 0,
            key=f"{key_prefix}property_type_form",
            help="Type of property"
        )
        
        new_owner = st.selectbox(
            "Owner",
            options=owner_names,
            index=owner_names.index(owner) if owner in owner_names else 0,
            key=f"{key_prefix}property_owner_form",
            help="Property owner"
        )
    
    with col2:
        new_address = st.text_area(
            "Address",
            value=address,
            key=f"{key_prefix}property_address_form",
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
            key=f"{key_prefix}property_currency_form",
            help="Currency for property values"
        ) or "EUR"
    
    st.divider()
    
    # Property valuation section
    st.markdown("#### 💰 Property Valuation")
    
    col3, col4, col5 = st.columns(3)
    
    with col3:
        new_valuation_date = st.date_input(
            "Valuation Date",
            value=date.fromisoformat(latest_valuation_date) if latest_valuation_date and isinstance(latest_valuation_date, str) else date.today(),
            key=f"{key_prefix}valuation_date_form",
            help="Date of property valuation"
        )
    
    with col4:
        new_market_value = st.number_input(
            f"Market Value ({new_currency})",
            min_value=0.0,
            value=latest_value,
            step=1000.0,
            format="%.2f",
            key=f"{key_prefix}market_value_form",
            help="Current market value of the property"
        )
    
    with col5:
        new_valuation_type = st.selectbox(
            "Valuation Type",
            options=valuation_types,
            index=valuation_types.index(valuation_type) if valuation_type in valuation_types else 1,
            key=f"{key_prefix}valuation_type_form",
            help="Type of valuation"
        )
    
    new_valuation_notes = st.text_area(
        "Valuation Notes (Optional)",
        value="",
        key=f"{key_prefix}valuation_notes_form",
        help="Additional notes about this valuation",
        height=80,
        placeholder="Add any relevant notes about the valuation"
    )
    
    st.divider()
    
    # Linked mortgages section
    st.markdown("#### 🏦 Linked Mortgages")
    
    mortgage_options = {}
    if all_mortgages:
        # Get currently linked mortgage IDs
        linked_mortgage_ids = [m['id'] for m in linked_mortgages]
        
        # Create multiselect for linking mortgages
        mortgage_options = {m['mortgage_name']: m['id'] for m in all_mortgages}
        selected_mortgage_names = [name for name, mid in mortgage_options.items() if mid in linked_mortgage_ids]
        
        selected_mortgages = st.multiselect(
            "Link Mortgages to This Property",
            options=list(mortgage_options.keys()),
            default=selected_mortgage_names,
            key=f"{key_prefix}linked_mortgages_form",
            help="Select mortgages associated with this property"
        )
        
        # Show linked mortgage details in accordions
        if selected_mortgages:
            st.markdown("**Linked Mortgage Details:**")
            for mortgage_name in selected_mortgages:
                mortgage = next((m for m in all_mortgages if m['mortgage_name'] == mortgage_name), None)
                if mortgage:
                    with st.expander(f"🏦 {mortgage_name}", expanded=False):
                        curr_symbol = get_currency_symbol(mortgage['currency'])
                        
                        mcol1, mcol2, mcol3 = st.columns(3)
                        with mcol1:
                            st.metric("Loan Amount", f"{curr_symbol}{mortgage['loan_amount']:,.2f}")
                        with mcol2:
                            st.metric("Interest Rate", f"{mortgage['interest_rate']:.2f}%")
                        with mcol3:
                            st.metric("Term", f"{mortgage['loan_term_years']} years")
                        
                        st.caption(f"**Lender:** {mortgage['lender_name']}")
                        st.caption(f"**Start Date:** {mortgage['start_date']}")
    else:
        st.info("No mortgages configured. Go to Settings → Mortgage to add mortgages.")
        selected_mortgages = []
    
    st.divider()
    
    # Action buttons
    col_save, col_cancel, col_delete = st.columns([1, 1, 1])
    
    with col_save:
        save_label = "💾 Save Property" if is_new else f"💾 Update {property_name}"
        if st.button(save_label, key=f"{key_prefix}save_property_form", type="primary", use_container_width=True):
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
                
                # Save property valuation
                if new_market_value > 0:
                    db.add_property_asset(
                        property_id=property_id,
                        valuation_date=new_valuation_date,
                        market_value=new_market_value,
                        valuation_type=new_valuation_type,
                        notes=new_valuation_notes
                    )
                
                # Update mortgage links
                if all_mortgages:
                    # Get selected mortgage IDs
                    selected_mortgage_ids = [mortgage_options[name] for name in selected_mortgages]
                    
                    # Unlink mortgages that are no longer selected
                    for mortgage in linked_mortgages:
                        if mortgage['id'] not in selected_mortgage_ids:
                            db.unlink_mortgage_from_property(property_id, mortgage['id'])
                    
                    # Link newly selected mortgages
                    for mortgage_id in selected_mortgage_ids:
                        db.link_mortgage_to_property(property_id, mortgage_id)
                
                st.success(f"✅ {new_property_name} saved successfully!")
                
                # Reset form state
                st.session_state.show_new_property_form = False
                st.session_state.selected_property_id = property_id
                st.rerun()
    
    with col_cancel:
        if st.button("❌ Cancel", key=f"{key_prefix}cancel_property_form", use_container_width=True):
            st.session_state.show_new_property_form = False
            if not is_new:
                st.session_state.selected_property_id = property_id
            st.rerun()
    
    with col_delete:
        if not is_new:
            if st.button(f"🗑️ Delete", key=f"{key_prefix}delete_property_form", use_container_width=True):
                db.delete_property(property_id)
                st.success(f"✅ {property_name} deleted successfully!")
                st.session_state.show_new_property_form = False
                st.session_state.selected_property_id = None
                st.rerun()
    
    # Display property summary for existing properties
    if not is_new and property_id and new_market_value > 0:
        st.divider()
        st.markdown("##### 📊 Property Summary")
        
        # Calculate total mortgage debt for this property
        total_debt = 0.0
        if linked_mortgages:
            from helper import get_all_mortgage_balances
            all_mortgage_balances = get_all_mortgage_balances(db)
            for mortgage in linked_mortgages:
                mortgage_balance = next((m for m in all_mortgage_balances if m['mortgage_id'] == mortgage['id']), None)
                if mortgage_balance:
                    # For simplicity, assuming same currency - in production, convert currencies
                    total_debt += mortgage_balance['balance']
        
        equity = new_market_value - total_debt
        equity_percentage = (equity / new_market_value * 100) if new_market_value > 0 else 0
        
        sum_col1, sum_col2, sum_col3 = st.columns(3)
        
        with sum_col1:
            st.metric("Market Value", format_currency(new_market_value, new_currency))
        
        with sum_col2:
            st.metric("Total Debt", format_currency(total_debt, new_currency))
        
        with sum_col3:
            st.metric("Equity", format_currency(equity, new_currency), delta=f"{equity_percentage:.1f}%")

# Made with Bob
