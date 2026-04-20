"""
KUYAN - Monthly Net Worth Tracker
Owners Page Module - Manages account owners
Copyright (c) 2025 mycloudcondo inc.
Licensed under MIT License - see LICENSE file for details
"""

import streamlit as st
from database import Database
from components import show_success_toast


def owners_settings(db: Database, key_prefix=""):
    """
    Render the owners management page.
    
    Args:
        db: Database instance
        key_prefix: Prefix for widget keys to avoid conflicts when used in tabs
    """
    # Show success message if owner was just added
    show_success_toast('owner')

    # List existing owners
    st.subheader("Existing Owners")

    owners = db.get_owners()
    owner_count = len(owners)

    if owners:
        for owner in owners:
            has_accounts = db.owner_has_accounts(owner['name'])
            has_accounts_text = "Yes" if has_accounts else "No"

            # Create expandable section for each owner
            with st.expander(f"👤 {owner['name']} - {owner['owner_type']}", expanded=False):
                st.write(f"**Has Accounts:** {has_accounts_text}")

                st.write("**Edit Owner:**")
                col1, col2 = st.columns(2)

                with col1:
                    new_name = st.text_input(
                        "Owner Name",
                        value=owner['name'],
                        key=f"{key_prefix}name_{owner['id']}"
                    )

                with col2:
                    type_options = ["Individual", "Company", "Joint/Shared", "Trust", "Other"]
                    current_index = type_options.index(owner['owner_type']) if owner['owner_type'] in type_options else 0
                    new_type = st.selectbox(
                        "Owner Type",
                        type_options,
                        index=current_index,
                        key=f"{key_prefix}type_{owner['id']}"
                    )

                # Update button
                if st.button(f"💾 Update Owner", key=f"{key_prefix}update_btn_{owner['id']}", width="stretch"):
                    if new_name:
                        try:
                            db.update_owner(owner['id'], new_name, new_type)
                            st.success(f"Owner updated!")
                            st.rerun()
                        except Exception as e:
                            if "UNIQUE constraint failed" in str(e):
                                st.error(f"Owner '{new_name}' already exists!")
                            else:
                                st.error(f"Error updating owner: {str(e)}")
                    else:
                        st.error("Please enter an owner name")

                st.divider()

                # Remove owner button
                if owner_count <= 1:
                    st.info("Cannot remove the last owner. At least one owner is required.")
                elif has_accounts:
                    st.warning(f"Cannot remove {owner['name']} - this owner has existing accounts.")
                else:
                    if st.button(f"🗑️ Remove {owner['name']}", key=f"{key_prefix}remove_btn_{owner['id']}", width="stretch", type="secondary"):
                        success = db.delete_owner(owner['id'])
                        if success:
                            st.success(f"Owner '{owner['name']}' removed!")
                            st.rerun()
                        else:
                            st.error("Failed to remove owner")
    else:
        st.warning("No owners found!")

    st.divider()

    # Add new owner section
    st.subheader("Add New Owner")

    col1, col2 = st.columns(2)

    with col1:
        owner_name = st.text_input("Owner Name", placeholder="e.g., John, Acme Corp", key=f"{key_prefix}add_owner_name")

    with col2:
        owner_type = st.selectbox("Owner Type", ["Individual", "Company", "Joint/Shared", "Trust", "Other"], key=f"{key_prefix}add_owner_type")

    # Add button
    if st.button("➕ Add Owner", width="stretch", type="primary", key=f"{key_prefix}add_owner_btn"):
        if owner_name:
            try:
                db.add_owner(owner_name, owner_type)
                st.session_state.owner_added = True
                st.session_state.added_owner_name = owner_name
                st.rerun()
            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    st.error(f"Owner '{owner_name}' already exists!")
                else:
                    st.error(f"Error adding owner: {str(e)}")
        else:
            st.error("Please enter an owner name")
