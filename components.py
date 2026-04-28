"""
KUYAN - Monthly Net Worth Tracker
Licensed under MIT License - see LICENSE file for details

Component rendering functions for the KUYAN application.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Optional
from database import Database
from currencyConverter import CurrencyConverter
from helper import get_theme_colors, has_multiple_currencies


# Global variables that need to be accessible
db: Optional[Database] = None
is_sandbox: bool = False


def set_globals(database, sandbox_mode):
    """Set global variables for components"""
    global db, is_sandbox
    db = database
    is_sandbox = sandbox_mode

def show_success_toast(item_type):
    """
    Display success toast if an item was just added

    Args:
        item_type: Type of item (e.g., 'account', 'currency', 'owner')
    """
    state_key = f'{item_type}_added'
    name_key = f'added_{item_type}_name'
    code_key = f'added_{item_type}_code'

    if st.session_state.get(state_key, False):
        # Try to get name first, fall back to code
        item_name = st.session_state.get(name_key, st.session_state.get(code_key, ''))
        icons = {'account': '🏦', 'currency': '💱', 'owner': '👥'}
        icon = icons.get(item_type, '✅')
        st.toast(f"{item_type.capitalize()} '{item_name}' added successfully!", icon=icon)
        st.session_state[state_key] = False

def render_sandbox_banner():
    """Render a floating top banner for sandbox mode"""
    if is_sandbox:
        st.markdown("""
        <div style="
            position: fixed;
            top: 0;
            left: 50px;
            right: 0;
            background: #fef9f3;
            color: #7a6f5d;
            padding: 10px 20px;
            text-align: center;
            font-size: 15px;
            z-index: 1000000;
            border-bottom: 1px solid #e8dcc8;
        ">
            Sandbox Mode
        </div>
        <div style="height: 40px;"></div>
        """, unsafe_allow_html=True)


def render_data_table(data, columns=None, hide_index=True):
    """
    Render a styled dataframe with consistent theme-aware formatting.

    Args:
        data: List of dictionaries or pandas DataFrame
        columns: Optional list of column names to display (in order)
        hide_index: Whether to hide the index column (default: True)

    Returns:
        Displays the styled dataframe
    """
    import pandas as pd

    # Convert to DataFrame if needed
    if not isinstance(data, pd.DataFrame):
        df = pd.DataFrame(data)
    else:
        df = data

    # Select and order columns if specified
    if columns:
        df = df[columns]

    # Apply alternating row colors using theme palette
    colors = get_theme_colors()
    styled_df = df.style.apply(
        lambda x: [f'background-color: {colors["table_row_even"]}' if i % 2 == 0
                   else f'background-color: {colors["table_row_odd"]}' for i in range(len(x))],
        axis=0
    )

    st.dataframe(styled_df, width="stretch", hide_index=hide_index)


def render_currency_selector(label="Select Currency", default_index=0, key=None):
    """
    Render a currency selector dropdown with consistent formatting.

    Args:
        label: Label for the dropdown (default: "Select Currency")
        default_index: Index of default selection (defaults to first currency)
        key: Unique key for the selectbox (required if multiple selectors on same page)

    Returns:
        str: Selected currency code
    """
    if db is None:
        raise RuntimeError("Database not initialized. Call set_globals() first.")
    
    # Get enabled currencies from database
    enabled_currencies = db.get_currency_codes()

    # Ensure default_index is valid
    if default_index >= len(enabled_currencies):
        default_index = 0

    selected = st.selectbox(
        label,
        options=enabled_currencies,
        index=default_index,
        key=key
    )
    return selected


def render_tool_button(icon, label, state_key, widget_renderer):
    """
    Render a tool button with arrow that expands to show a widget

    Args:
        icon: Emoji icon for the button
        label: Button label text
        state_key: Session state key for tracking open/closed state
        widget_renderer: Function to render the widget content
    """
    colors = get_theme_colors()

    # Check if widget is open
    is_open = st.session_state.get(state_key, False)
    arrow = "▼" if is_open else "▲"

    # Render button
    if st.button(f"{icon} {label} {arrow}", width="stretch", key=f"{state_key}_btn"):
        # Toggle state
        st.session_state[state_key] = not is_open
        st.rerun()

    # Render widget if open
    if is_open:
        widget_renderer()


def render_exchange_rate_widget_inline():
    """Exchange Rate widget content"""
    if db is None:
        raise RuntimeError("Database not initialized. Call set_globals() first.")
    
    # Check if multiple currencies exist
    if not has_multiple_currencies(db):
        st.info("💡 Exchange rates are not available with the current configuration.")
        st.write("To enable exchange rate functionality, you need:")
        st.write("- At least 1 currency AND 1 commodity, OR")
        st.write("- At least 2 currencies (without commodities), OR")
        st.write("- More than 2 currencies AND more than 2 commodities")
        st.write("\nConfigure currencies and commodities in the settings to enable this feature.")
        return

    # Date selector (disabled - live rates are always shown for today)
    current_date = date.today()
    selected_date = current_date
    with st.expander("📅 Select Date", expanded=False):
        st.date_input(
            "Select Date",
            value=current_date,
            max_value=current_date,
            key="exchange_rate_date",
            label_visibility="collapsed",
            disabled=True
        )

    st.write("")  # Add spacing

    # Fetch exchange rates
    with st.spinner("Fetching rates..."):
        enabled_currencies = db.get_currency_codes()
        exchange_rates = CurrencyConverter.get_all_cross_rates(enabled_currencies)

    if not exchange_rates:
        st.error("Unable to fetch rates.")
        return

    # Display date caption
    st.caption(f"📅 {selected_date.strftime('%B %d, %Y')}")

    st.divider()

    # Get enabled currencies
    enabled_currencies = db.get_currency_codes()

    # Currency Exchange Rates Section
    st.subheader("💱 Currency Exchange Rates")
    
    # Generate all currency pairs (sorted alphabetically)
    rates_display = []
    for from_curr in enabled_currencies:
        for to_curr in enabled_currencies:
            if from_curr != to_curr:
                pair_key = f"{from_curr}_{to_curr}"
                rate_value = exchange_rates.get(pair_key, "N/A")
                rates_display.append((f"{from_curr} → {to_curr}", rate_value))

    # Sort alphabetically
    rates_display.sort(key=lambda x: x[0])

    # Display rates with better formatting
    for label, rate in rates_display:
        col1, col2 = st.columns([1.5, 1])
        with col1:
            st.markdown(f"**{label}**")
        with col2:
            if rate != "N/A":
                st.text(f"{rate:.4f}")
            else:
                st.text("N/A")
    
    # Commodity Prices Section
    commodities = db.get_commodities()
    if commodities:
        st.divider()
        st.subheader("🥇 Commodity Prices")
        
        # Unit selector dropdown
        unit_options = ["ounce", "gram", "kilogram", "pound", "ton"]
        
        # Initialize session state for selected unit if not exists
        if "commodity_display_unit" not in st.session_state:
            st.session_state.commodity_display_unit = "ounce"
        
        # Unit selector with callback
        col_unit1, col_unit2 = st.columns([1, 2])
        with col_unit1:
            selected_unit = st.selectbox(
                "Display Unit",
                options=unit_options,
                index=unit_options.index(st.session_state.commodity_display_unit),
                key="unit_selector",
                help="Select the unit for displaying commodity prices"
            )
        
        # Update session state if unit changed
        if selected_unit != st.session_state.commodity_display_unit:
            st.session_state.commodity_display_unit = selected_unit
            st.rerun()
        
        st.write("")  # Add spacing
        
        # Fetch commodity prices
        with st.spinner("Fetching commodity prices..."):
            commodity_names = [c['name'] for c in commodities]
            commodity_prices = CurrencyConverter.get_commodity_prices(commodity_names, enabled_currencies)
        
        if commodity_prices:
            # Display commodity prices in compact format like currency pairs
            commodity_display = []
            for commodity in commodities:
                commodity_name = commodity['name']
                commodity_unit = commodity.get('unit', 'ounce')
                if commodity_name in commodity_prices:
                    prices = commodity_prices[commodity_name]
                    for currency_code in enabled_currencies:
                        if currency_code in prices:
                            # Get base price (per ounce from API)
                            base_price = prices[currency_code]
                            
                            # Convert price to selected unit
                            converted_price = CurrencyConverter.convert_commodity_unit(
                                base_price,
                                "ounce",  # API returns prices per ounce
                                commodity_unit
                            )
                            
                            # Get currency details for emoji
                            curr_details = db.get_currency_by_code(currency_code)
                            emoji = curr_details['flag_emoji'] if curr_details else ""
                            commodity_display.append((
                                f"{commodity['symbol']} {commodity_name} ({selected_unit}) → {emoji} {currency_code}",
                                converted_price
                            ))
            
            # Sort alphabetically
            commodity_display.sort(key=lambda x: x[0])
            
            # Display in same format as currency rates
            for label, price in commodity_display:
                col1, col2 = st.columns([1.5, 1])
                with col1:
                    st.markdown(f"**{label}**")
                with col2:
                    st.text(f"{price:,.2f}")
        else:
            st.info("💡 Commodity prices are currently unavailable. Please try again later.")


def render_calendar_widget():
    """Calendar Invite widget for monthly balance update reminders"""
    from datetime import datetime, timedelta

    st.write("**Create Monthly Reminder**")
    st.caption("Set up a calendar invite to remind you to update monthly balances")

    # Initialize previous date in session state if not exists
    if "prev_calendar_start_date" not in st.session_state:
        st.session_state.prev_calendar_start_date = datetime.now().date() + timedelta(days=30)

    # Date selector for first reminder
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "First Reminder Date",
            value=st.session_state.prev_calendar_start_date,
            key="calendar_start_date"
        )
        
        # Update previous date when changed
        if start_date != st.session_state.prev_calendar_start_date:
            st.session_state.prev_calendar_start_date = start_date

    with col2:
        reminder_time = st.time_input(
            "Reminder Time",
            value=datetime.strptime("09:00", "%H:%M").time(),
            key="calendar_time"
        )

    # Email input
    emails = st.text_input(
        "Invite additional attendees",
        placeholder="email1@example.com, email2@example.com",
        help="Add comma-separated email addresses",
        key="calendar_emails"
    )

    # Generate invite button
    if st.button("Generate Calendar Invite", width="stretch", type="primary", key="gen_calendar"):
        if emails:
            # Create .ics file content
            event_datetime = datetime.combine(start_date, reminder_time)

            ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//KUYAN//Monthly Balance Reminder//EN
BEGIN:VEVENT
UID:{event_datetime.strftime('%Y%m%d%H%M%S')}@kuyan
DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}
DTSTART:{event_datetime.strftime('%Y%m%dT%H%M%S')}
DTEND:{(event_datetime + timedelta(hours=1)).strftime('%Y%m%dT%H%M%S')}
RRULE:FREQ=MONTHLY;COUNT=12
SUMMARY:Update Monthly Balances in KUYAN
DESCRIPTION:Monthly reminder to update account balances in KUYAN
LOCATION:KUYAN App
ATTENDEE:MAILTO:{emails.split(',')[0].strip()}
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR"""

            # Offer download
            st.download_button(
                label="📅 Download .ics File",
                data=ics_content,
                file_name=f"kuyan_reminder_{start_date.strftime('%Y%m%d')}.ics",
                mime="text/calendar",
                width="stretch"
            )
            st.success("Calendar invite generated! Click above to download.")
        else:
            st.error("Please enter at least one email address")

def render_calculator_widget():
    """Calculator widget content"""

    # Initialize calculator history in session state
    if "calc_history" not in st.session_state:
        st.session_state.calc_history = []
    if "calc_trigger" not in st.session_state:
        st.session_state.calc_trigger = False

    # Callback to trigger calculation on Enter
    def on_enter():
        st.session_state.calc_trigger = True

    # Calculator input
    expression = st.text_input(
        "Enter calculation",
        placeholder="e.g., 1500 * 1.35 + 200",
        key="calc_input",
        help="Use +, -, *, /, (), and numbers. Press Enter to calculate.",
        on_change=on_enter
    )

    # Calculate and Clear buttons
    col1, col2 = st.columns([1, 1])
    with col1:
        calculate = st.button("Calculate", width="stretch", type="primary", key="calc_button")
    with col2:
        clear_history = st.button("Clear History", width="stretch", key="clear_calc_history")

    # Check if calculation should be triggered (by Enter or button click)
    should_calculate = calculate or st.session_state.calc_trigger
    if st.session_state.calc_trigger:
        st.session_state.calc_trigger = False  # Reset trigger

    # Clear history
    if clear_history:
        st.session_state.calc_history = []
        st.rerun()

    # Perform calculation
    if should_calculate and expression:
        try:
            # Avoid double-processing when both Enter and button click trigger the same expression
            last_expression = st.session_state.get("last_calc_expression")
            last_result = st.session_state.get("last_calc_result")

            if expression != last_expression:
                # Safe evaluation of mathematical expressions
                result = eval(expression, {"__builtins__": {}}, {})

                # Add to history
                st.session_state.calc_history.insert(0, {
                    "expression": expression,
                    "result": result
                })

                # Keep only last 5 calculations
                st.session_state.calc_history = st.session_state.calc_history[:5]

                st.session_state.last_calc_expression = expression
                st.session_state.last_calc_result = result
            else:
                result = last_result

            # Display result
            st.success(f"**Result:** {result:,.2f}")

        except Exception as e:
            st.error(f"Invalid expression: {str(e)}")

    # Display calculation history
    if st.session_state.calc_history:
        st.divider()
        st.caption("Recent Calculations")

        for calc in st.session_state.calc_history:
            with st.container():
                col1, col2 = st.columns([1.5, 1])
                with col1:
                    st.text(calc["expression"])
                with col2:
                    st.text(f"= {calc['result']:,.2f}")


def render_export_widget():
    """Export Dashboard widget for exporting as PDF/PNG"""

    st.write("**Export Dashboard**")
    st.caption("Export the dashboard view in various formats")

    # Format selector
    export_format = st.selectbox(
        "Select Format",
        options=["PNG (Image)", "PDF (Document)", "HTML (Interactive)"],
        key="export_format"
    )

    st.write("")

    # Export instructions
    if export_format == "PNG (Image)":
        st.info("""
**PNG Export Instructions:**
1. Navigate to the Dashboard tab
2. Use your browser's screenshot tool or:
   - **Windows**: Win + Shift + S
   - **Mac**: Cmd + Shift + 4
   - **Linux**: Use Screenshot tool
3. Select the dashboard area to capture
        """)

    elif export_format == "PDF (Document)":
        st.info("""
**PDF Export Instructions:**
1. Navigate to the Dashboard tab
2. Use browser's Print function:
   - **Chrome/Edge**: Ctrl/Cmd + P
   - Select "Save as PDF" as destination
   - Choose "Save"
        """)

    elif export_format == "HTML (Interactive)":
        st.info("""
**HTML Export Instructions:**
1. Navigate to the Dashboard tab
2. Use browser's Save Page function:
   - **Chrome/Edge**: Ctrl/Cmd + S
   - Select "Webpage, Complete"
   - Choose save location
        """)

    st.divider()
    st.caption("Tip: retract the side bar using the top arrow before exporting")



def render_navbar():
    """Render horizontal navbar with tool buttons for dashboard pages"""
    colors = get_theme_colors()
    
    # Initialize modal states in session state
    if "show_exchange_rate_modal" not in st.session_state:
        st.session_state.show_exchange_rate_modal = False
    
    # Create navbar with buttons
    st.markdown(f"""
        <style>
        .navbar-container {{
            background-color: {colors['bg_secondary']};
            padding: 10px 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            border: 1px solid {colors['border']};
        }}
        </style>
    """, unsafe_allow_html=True)
    
    # Create columns for navbar buttons
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Exchange Rate Tool Button
        render_tool_button(
            icon="💱",
            label="Exchange Rates",
            state_key="exchange_rate_widget",
            widget_renderer=render_exchange_rate_widget_inline
        )
    
    with col2:
        # Calendar Reminder Tool Button
        render_tool_button(
            icon="📅",
            label="Calendar Reminder",
            state_key="calendar_widget",
            widget_renderer=render_calendar_widget
        )
