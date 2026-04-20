"""
KUYAN - Monthly Net Worth Tracker
Accounts Page Module - Handles account management functionality
Copyright (c) 2025 mycloudcondo inc.
Licensed under MIT License - see LICENSE file for details
"""

import streamlit as st
from database import Database
from components import show_success_toast


def accounts_settings(db: Database, key_prefix=""):
    """
    Render the accounts management page.
    
    Args:
        db: Database instance
        key_prefix: Prefix for widget keys to avoid conflicts when used in tabs
    """
    # Unit options for commodity accounts
    UNIT_OPTIONS = ["gram", "ounce", "kilo"]

    # Show success message if account was just added
    show_success_toast('account')

    # List existing accounts with filter
    col_title, col_filter = st.columns([3, 1])
    with col_title:
        st.subheader("Existing Accounts")
    with col_filter:
        # Account type filter dropdown aligned to the right
        filter_options = ["All Types", "Bank", "Investment", "Commodity", "Other"]
        selected_filter = st.selectbox(
            "Filter by Type",
            filter_options,
            key=f"{key_prefix}account_type_filter",
            label_visibility="collapsed"
        )

    accounts = db.get_accounts()
    owner_names = db.get_owner_names()
    currency_codes = db.get_currency_codes()
    commodity_list = db.get_commodities()

    # Apply filter if not "All Types"
    if selected_filter != "All Types":
        accounts = [acc for acc in accounts if acc['account_type'] == selected_filter]

    if accounts:
        # Group accounts by owner for better organization
        accounts_by_owner = {}
        for acc in accounts:
            if acc['owner'] not in accounts_by_owner:
                accounts_by_owner[acc['owner']] = []
            accounts_by_owner[acc['owner']].append(acc)

        # Display accounts grouped by owner
        for owner_name in sorted(accounts_by_owner.keys()):
            st.write(f"**{owner_name}:**")

            for account in accounts_by_owner[owner_name]:
                # Create expandable section for each account
                is_commodity = account['account_type'] == "Commodity"
                account_icon = "🏦" if account['account_type'] == "Bank" else "📈" if account['account_type'] == "Investment" else "🏛️" if account['account_type'] == "Pension" else "🥇" if is_commodity else "💼"
                display_label = account.get('commodity', account['currency']) if is_commodity else account['currency']
                with st.expander(f"{account_icon} {account['name']} - {display_label}", expanded=False):
                    st.write(f"**Type:** {account['account_type']}")
                    if is_commodity:
                        st.write(f"**Commodity:** {account.get('commodity', 'N/A')}")
                    else:
                        st.write(f"**Currency:** {account['currency']}")

                    st.write("**Edit Account:**")
                    col1, col2 = st.columns(2)

                    with col1:
                        # For commodity accounts, name is uneditable
                        if is_commodity:
                            new_name = st.text_input(
                                "Account Name",
                                value=account['name'],
                                key=f"{key_prefix}name_{account['id']}",
                                disabled=True,
                                help="Commodity account names are auto-generated"
                            )
                        else:
                            new_name = st.text_input(
                                "Account Name",
                                value=account['name'],
                                key=f"{key_prefix}name_{account['id']}"
                            )
                        owner_index = owner_names.index(account['owner']) if account['owner'] in owner_names else 0
                        new_owner = st.selectbox(
                            "Owner",
                            owner_names,
                            index=owner_index,
                            key=f"{key_prefix}owner_{account['id']}"
                        )

                    with col2:
                        type_options = ["Bank", "Investment", "Pension", "Commodity", "Other"]
                        type_index = type_options.index(account['account_type']) if account['account_type'] in type_options else 0
                        new_type = st.selectbox(
                            "Account Type",
                            type_options,
                            index=type_index,
                            key=f"{key_prefix}type_{account['id']}"
                        )
                        
                        # Show currency or commodity dropdown based on account type
                        if new_type == "Commodity":
                            commodity_names = [c['name'] for c in commodity_list]
                            current_commodity = account.get('commodity', commodity_names[0] if commodity_names else '')
                            comm_index = commodity_names.index(current_commodity) if current_commodity in commodity_names else 0
                            new_commodity = st.selectbox(
                                "Commodity",
                                commodity_names,
                                index=comm_index,
                                key=f"{key_prefix}commodity_{account['id']}"
                            )
                            
                            # Get unit from account data or extract from name as fallback
                            current_unit = account.get('unit')
                            if not current_unit:
                                # Fallback: extract from account name (format: "Gold (ounce)")
                                current_unit = "ounce"  # default
                                if '(' in account['name'] and ')' in account['name']:
                                    unit_part = account['name'].split('(')[1].split(')')[0]
                                    if unit_part in UNIT_OPTIONS:
                                        current_unit = unit_part
                            
                            unit_index = UNIT_OPTIONS.index(current_unit) if current_unit in UNIT_OPTIONS else 1
                            new_unit = st.selectbox(
                                "Unit",
                                UNIT_OPTIONS,
                                index=unit_index,
                                key=f"{key_prefix}unit_{account['id']}"
                            )
                            new_currency = ""  # Empty for commodity accounts
                        else:
                            curr_index = currency_codes.index(account['currency']) if account['currency'] in currency_codes else 0
                            new_currency = st.selectbox(
                                "Currency",
                                currency_codes,
                                index=curr_index,
                                key=f"{key_prefix}currency_{account['id']}"
                            )
                            new_commodity = None
                            new_unit = None

                    # Update button
                    if st.button(f"💾 Update Account", key=f"{key_prefix}update_btn_{account['id']}", width="stretch"):
                        if new_type == "Commodity":
                            # Auto-generate name for commodity accounts with unit
                            auto_name = f"{new_commodity} ({new_unit})"
                            db.update_account(account['id'], auto_name, new_owner, new_type, "", new_commodity, new_unit)
                            st.success(f"Account updated!")
                            st.rerun()
                        else:
                            if new_name:
                                db.update_account(account['id'], new_name, new_owner, new_type, new_currency, None, None)
                                st.success(f"Account updated!")
                                st.rerun()
                            else:
                                st.error("Please enter an account name")

                    st.divider()

                    # Remove account button
                    if st.button(f"🗑️ Remove {account['name']}", key=f"{key_prefix}remove_btn_{account['id']}", width="stretch", type="secondary"):
                        db.delete_account(account['id'])
                        st.success(f"Account '{account['name']}' removed!")
                        st.rerun()

            st.write("")  # Add spacing between owners
    else:
        st.warning("No accounts found!")

    st.divider()

    # Add new account section
    st.subheader("Add New Account")

    if not owner_names:
        st.warning("Please add at least one owner first in the Owners page!")
    else:
        col1, col2 = st.columns(2)

        # Initialize variables
        account_name = ""
        currency = ""
        selected_commodity = None
        auto_account_name = None
        selected_commodity = None
        
        with col1:
            # Account type selector first to determine what to show
            account_type = st.selectbox("Account Type", ["Bank", "Investment", "Pension", "Commodity", "Other"], key=f"{key_prefix}add_account_type")
            owner = st.selectbox("Owner", owner_names, key=f"{key_prefix}add_account_owner")

        with col2:
            # Show currency or commodity dropdown based on account type
            if account_type == "Commodity":
                commodity_names = [c['name'] for c in commodity_list]
                if commodity_names:
                    selected_commodity = st.selectbox("Commodity", commodity_names, key=f"{key_prefix}add_account_commodity")
                    selected_unit = st.selectbox("Unit", UNIT_OPTIONS, index=1, key=f"{key_prefix}add_account_unit")  # Default to "ounce"
                    # Auto-generate account name with unit
                    auto_account_name = f"{selected_commodity} ({selected_unit})"
                    st.text_input("Account Name", value=auto_account_name, key=f"{key_prefix}add_account_name_display", disabled=True, help="Auto-generated for commodity accounts")
                else:
                    st.warning("No commodities available. Please add commodities first!")
                    selected_unit = None
            else:
                account_name = st.text_input("Account Name", placeholder="e.g., TD Chequing", key=f"{key_prefix}add_account_name")
                currency = st.selectbox("Currency", currency_codes, key=f"{key_prefix}add_account_currency")
                selected_unit = None

        # Add button
        if st.button("➕ Add Account", width="stretch", type="primary", key=f"{key_prefix}add_account_btn"):
            if account_type == "Commodity":
                if selected_commodity and auto_account_name and selected_unit:
                    db.add_account(auto_account_name, owner, account_type, "", selected_commodity, selected_unit)
                    st.session_state.account_added = True
                    st.session_state.added_account_name = auto_account_name
                    st.rerun()
                else:
                    st.error("Please select a commodity")
            else:
                if account_name:
                    db.add_account(account_name, owner, account_type, currency, None, None)
                    st.session_state.account_added = True
                    st.session_state.added_account_name = account_name
                    st.rerun()
                else:
                    st.error("Please enter an account name")

