"""
KUYAN - Monthly Net Worth Tracker
Commodities Page Module - Manages commodity settings
Licensed under MIT License - see LICENSE file for details
"""

import streamlit as st
from constants import AVAILABLE_COMMODITIES, COMMODITIES_COLOR_OPTIONS
from database import Database


def commodities_settings(db: Database, key_prefix=""):
    """
    Render the commodities management page.
    
    Args:
        db: Database instance
        key_prefix: Prefix for widget keys to avoid conflicts when used in tabs
    """

    # Show success message if commodity was just added
    if st.session_state.get('commodity_added', False):
        commodity_name = st.session_state.get('added_commodity_name', '')
        st.toast(f"Commodity '{commodity_name}' added successfully!", icon="🥇")
        st.session_state.commodity_added = False

    # Get enabled commodities
    enabled_commodities = db.get_commodities()
    enabled_names = [c['name'] for c in enabled_commodities]
    commodity_count = len(enabled_commodities)

    st.info(f"**{commodity_count}/2 commodities enabled** (Minimum: 0, Maximum: 2)")

    st.divider()

    # Show enabled commodities with inline editing and removal
    st.subheader("Enabled Commodities")

    if enabled_commodities:
        for comm in enabled_commodities:
            commodity_desc = AVAILABLE_COMMODITIES.get(comm['name'], {}).get('description', comm['name'])
            is_in_use = db.commodity_in_use(comm['name'])
            in_use_text = "Yes" if is_in_use else "No"

            # Create expandable section for each commodity
            with st.expander(f"{comm['symbol']} {comm['name']} - {commodity_desc}", expanded=False):
                st.write(f"**In Use:** {in_use_text}")

                st.write("**Change Color:**")
                col1, col2, col3 = st.columns([2, 3, 2])

                with col1:
                    # Current color preview - aligned with dropdown center
                    st.markdown("<div style='text-align: center;'>Current</div>", unsafe_allow_html=True)
                    st.markdown(
                        f"<div style='width: 40px; height: 40px; background-color: {comm['color']}; "
                        f"border-radius: 50%; border: 2px solid #666; margin-left: auto; margin-right: auto;'></div>",
                        unsafe_allow_html=True
                    )

                with col2:
                    # Color selector
                    new_color = st.selectbox(
                        "Select Color",
                        list(COMMODITIES_COLOR_OPTIONS.keys()),
                        key=f"{key_prefix}color_select_{comm['id']}"
                    )

                with col3:
                    # New color preview - aligned with dropdown center
                    st.markdown("<div style='text-align: center;'>New</div>", unsafe_allow_html=True)
                    new_color_value = COMMODITIES_COLOR_OPTIONS[new_color]
                    st.markdown(
                        f"<div style='width: 40px; height: 40px; background-color: {new_color_value}; "
                        f"border-radius: 50%; border: 2px solid #666; margin-left: auto; margin-right: auto;'></div>",
                        unsafe_allow_html=True
                    )

                # Update button
                if st.button(f"🎨 Update Color", key=f"{key_prefix}update_btn_{comm['id']}", width="stretch"):
                    success = db.update_commodity_color(comm['id'], new_color_value)
                    if success:
                        st.success(f"Color updated!")
                        st.rerun()
                    else:
                        st.error("Failed to update color")

                st.divider()

                # Remove commodity button
                if is_in_use:
                    st.warning(f"Cannot remove {comm['name']} - it's currently used by existing accounts.")
                else:
                    if st.button(f"🗑️ Remove {comm['name']}", key=f"{key_prefix}remove_btn_{comm['id']}", width="stretch", type="secondary"):
                        success = db.delete_commodity(comm['id'])
                        if success:
                            st.success(f"Commodity {comm['name']} removed!")
                            st.rerun()
                        else:
                            st.error("Failed to remove commodity")
    else:
        st.warning("No commodities enabled!")

    # Add new commodity section
    if commodity_count < 2:  # Only allow adding if less than 2 commodities
        st.subheader("Add New Commodity")

        # Filter out already enabled commodities
        available_to_add = {k: v for k, v in AVAILABLE_COMMODITIES.items() if k not in enabled_names}

        if available_to_add:
            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                # Commodity selector
                commodity_options = [f"{v['symbol']} {k} - {v['description']}" for k, v in sorted(available_to_add.items())]
                selected = st.selectbox("Select Commodity", commodity_options, key=f"{key_prefix}add_commodity_selector")

                # Extract commodity name from selection
                selected_name = selected.split()[1] if selected else None

            with col2:
                # Color selector
                color_name = st.selectbox("Select Color", list(COMMODITIES_COLOR_OPTIONS.keys()), key=f"{key_prefix}add_color_selector")
                color_value = COMMODITIES_COLOR_OPTIONS[color_name]

            with col3:
                # Color preview - aligned with dropdown center
                st.markdown("<div style='text-align: center;'>Preview</div>", unsafe_allow_html=True)
                st.markdown(
                    f"<div style='width: 40px; height: 40px; background-color: {color_value}; "
                    f"border-radius: 50%; border: 2px solid #666; margin-left: auto; margin-right: auto;'></div>",
                    unsafe_allow_html=True
                )

            # Add button with proper spacing
            if st.button("➕ Add Commodity", width="stretch", type="primary", key=f"{key_prefix}add_commodity_btn"):
                if selected_name:
                    symbol = AVAILABLE_COMMODITIES[selected_name]['symbol']
                    # Default unit is 'ounce' - will be set when creating account
                    db.add_commodity(selected_name, symbol, color_value, "ounce")
                    st.session_state.commodity_added = True
                    st.session_state.added_commodity_name = selected_name
                    st.rerun()
        else:
            st.info("All available commodities have been added!")
    else:
        st.warning("Maximum of 2 commodities reached. Remove a commodity to add a new one.")

    st.divider()

    st.info("""
**About Commodities**

- Track precious and industrial metals
- Commodities can be used for investment tracking
- Colors help distinguish different commodities in charts
- Commodities cannot be removed if they're used by accounts
    """)
