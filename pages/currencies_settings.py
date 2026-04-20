"""
KUYAN - Monthly Net Worth Tracker
Currencies Page Module - Manages currency settings
Copyright (c) 2025 mycloudcondo inc.
Licensed under MIT License - see LICENSE file for details
"""

import streamlit as st
from database import Database
from constants import AVAILABLE_CURRENCIES, COLOR_OPTIONS


def currencies_settings(db: Database, key_prefix=""):
    """
    Render the currencies management page.
    
    Args:
        db: Database instance
        key_prefix: Prefix for widget keys to avoid conflicts when used in tabs
    """

    # Show success message if currency was just added
    if st.session_state.get('currency_added', False):
        currency_code = st.session_state.get('added_currency_code', '')
        st.toast(f"Currency '{currency_code}' added successfully!", icon="💱")
        st.session_state.currency_added = False

    # Get enabled currencies
    enabled_currencies = db.get_currencies()
    enabled_codes = [c['code'] for c in enabled_currencies]
    currency_count = len(enabled_currencies)

    st.info(f"**{currency_count}/9 currencies enabled** (Minimum: 1, Maximum: 9)")

    st.divider()

    # Show enabled currencies with inline editing and removal
    st.subheader("Enabled Currencies")

    if enabled_currencies:
        for curr in enabled_currencies:
            currency_name = AVAILABLE_CURRENCIES.get(curr['code'], {}).get('name', curr['code'])
            is_in_use = db.currency_in_use(curr['code'])
            in_use_text = "Yes" if is_in_use else "No"

            # Create expandable section for each currency
            with st.expander(f"{curr['flag_emoji']} {curr['code']} - {currency_name}", expanded=False):
                st.write(f"**In Use:** {in_use_text}")

                st.write("**Change Color:**")
                col1, col2, col3 = st.columns([2, 3, 2])

                with col1:
                    # Current color preview - aligned with dropdown center
                    st.markdown("<div style='text-align: center;'>Current</div>", unsafe_allow_html=True)
                    st.markdown(f"""
                        <div style="
                            width: 40px;
                            height: 40px;
                            background-color: {curr['color']};
                            border-radius: 50%;
                            border: 2px solid #666;
                            margin-left: auto;
                            margin-right: auto;
                        "></div>
                    """, unsafe_allow_html=True)

                with col2:
                    # Color selector
                    new_color = st.selectbox(
                        "Select Color",
                        list(COLOR_OPTIONS.keys()),
                        key=f"{key_prefix}color_select_{curr['id']}"
                    )

                with col3:
                    # New color preview - aligned with dropdown center
                    st.markdown("<div style='text-align: center;'>New</div>", unsafe_allow_html=True)
                    new_color_value = COLOR_OPTIONS[new_color]
                    st.markdown(f"""
                        <div style="
                            width: 40px;
                            height: 40px;
                            background-color: {new_color_value};
                            border-radius: 50%;
                            border: 2px solid #666;
                            margin-left: auto;
                            margin-right: auto;
                        "></div>
                    """, unsafe_allow_html=True)

                # Update button
                if st.button(f"🎨 Update Color", key=f"{key_prefix}update_btn_{curr['id']}", width="stretch"):
                    success = db.update_currency_color(curr['id'], new_color_value)
                    if success:
                        st.success(f"Color updated!")
                        st.rerun()
                    else:
                        st.error("Failed to update color")

                st.divider()

                # Remove currency button
                if currency_count <= 1:
                    st.info("Cannot remove the last currency. At least one currency is required.")
                elif is_in_use:
                    st.warning(f"Cannot remove {curr['code']} - it's currently used by existing accounts.")
                else:
                    if st.button(f"🗑️ Remove {curr['code']}", key=f"{key_prefix}remove_btn_{curr['id']}", width="stretch", type="secondary"):
                        success = db.delete_currency(curr['id'])
                        if success:
                            st.success(f"Currency {curr['code']} removed!")
                            st.rerun()
                        else:
                            st.error("Failed to remove currency")
    else:
        st.warning("No currencies enabled!")

    # Add new currency section
    if currency_count < 9:  # Only allow adding if less than 9 currencies
        st.subheader("Add New Currency")

        # Filter out already enabled currencies
        available_to_add = {k: v for k, v in AVAILABLE_CURRENCIES.items() if k not in enabled_codes}

        if available_to_add:
            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                # Currency selector
                currency_options = [f"{v['flag']} {k} - {v['name']}" for k, v in sorted(available_to_add.items())]
                selected = st.selectbox("Select Currency", currency_options, key=f"{key_prefix}add_currency_selector")

                # Extract currency code from selection
                selected_code = selected.split()[1] if selected else None

            with col2:
                # Color selector
                color_name = st.selectbox("Select Color", list(COLOR_OPTIONS.keys()), key=f"{key_prefix}add_color_selector")
                color_value = COLOR_OPTIONS[color_name]

            with col3:
                # Color preview - aligned with dropdown center
                st.markdown("<div style='text-align: center;'>Preview</div>", unsafe_allow_html=True)
                st.markdown(f"""
                    <div style="
                        width: 40px;
                        height: 40px;
                        background-color: {color_value};
                        border-radius: 50%;
                        border: 2px solid #666;
                        margin-left: auto;
                        margin-right: auto;
                    "></div>
                """, unsafe_allow_html=True)

            # Add button with proper spacing
            if st.button("➕ Add Currency", width="stretch", type="primary", key=f"{key_prefix}add_currency_btn"):
                if selected_code:
                    flag_emoji = AVAILABLE_CURRENCIES[selected_code]['flag']
                    db.add_currency(selected_code, flag_emoji, color_value)
                    st.session_state.currency_added = True
                    st.session_state.added_currency_code = selected_code
                    st.rerun()
        else:
            st.info("All available currencies have been added!")
    else:
        st.warning("Maximum of 9 currencies reached. Remove a currency to add a new one.")

    st.divider()

    st.info("""
**About Currencies**

- Exchange rates are fetched from the [Frankfurter API](https://frankfurter.dev/)
- Rates are effective as of the 1st of each month
- View current rates using the **Exchange Rate** tool in the sidebar
- Currencies cannot be removed if they're used by accounts
    """)
