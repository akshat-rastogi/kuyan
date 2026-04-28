"""
KUYAN - Monthly Net Worth Tracker
Exchange Rates Page Module - Displays live exchange rates and commodity prices
Licensed under MIT License - see LICENSE file for details
"""

import streamlit as st
from datetime import date
from database import Database
from currencyConverter import CurrencyConverter
from helper import has_multiple_currencies


def exchange_rates(db: Database):
    """
    Render the exchange rates page showing live currency rates and commodity prices.
    
    Args:
        db: Database instance
    """
    st.title("💹 Exchange Rates")
    st.caption("View today's live exchange rates for supported currencies and commodities")
    
    # Check if multiple currencies exist
    if not has_multiple_currencies(db):
        st.info("💡 Exchange rates are not available with the current configuration.")
        st.write("To enable exchange rate functionality, you need:")
        st.write("- At least 1 currency AND 1 commodity, OR")
        st.write("- At least 2 currencies (without commodities), OR")
        st.write("- More than 2 currencies AND more than 2 commodities")
        st.write("\nConfigure currencies and commodities in the settings to enable this feature.")
        return

    # Date selector - allows viewing historical rates
    current_date = date.today()
    selected_date = st.date_input(
        "Select Date",
        value=current_date,
        max_value=current_date,
        disabled=False,
        help="Select a date to view historical exchange rates and commodity prices. Frankfurter API supports historical data from 1999 onwards."
    )
    
    # Convert date to string format for API (YYYY-MM-DD)
    date_str = selected_date.strftime('%Y-%m-%d') if selected_date != current_date else None

    st.divider()

    # Fetch exchange rates for selected date
    with st.spinner(f"Fetching exchange rates for {selected_date.strftime('%B %d, %Y')}..."):
        enabled_currencies = db.get_currency_codes()
        exchange_rates = CurrencyConverter.get_all_cross_rates(enabled_currencies, date=date_str)

    if not exchange_rates:
        st.error("⚠️ Unable to fetch live exchange rates from API. Using fallback rates.")
        st.info("💡 Fallback rates are approximate values. For accurate rates, please check your internet connection and try again.")
        # Get fallback rates
        exchange_rates = CurrencyConverter._get_fallback_rates(enabled_currencies)
        if not exchange_rates:
            st.error("Unable to generate exchange rates. Please try again later.")
            return
        rates_source = "Fallback"
    else:
        rates_source = "Live API"

    date_label = "Today's live" if selected_date == current_date else "Historical"
    st.success(f"✅ {date_label} exchange rates for {selected_date.strftime('%B %d, %Y')} ({rates_source})")

    st.divider()

    # Display exchange rates dynamically for all saved currencies
    st.subheader("💱 Currency Exchange Rates")
    
    # Get all saved currencies with their details
    currencies = db.get_currencies()
    
    if len(currencies) < 2:
        st.info("Add more currencies to see exchange rates between them.")
    else:
        # Create a grid layout based on number of currencies
        num_currencies = len(currencies)
        
        # Display rates in a table format
        st.write("**All Currency Pairs:**")
        
        # Create columns for better layout
        cols_per_row = 3
        rate_pairs = []
        
        # Generate all currency pairs
        for i, from_curr in enumerate(currencies):
            for j, to_curr in enumerate(currencies):
                if i != j:  # Don't show same currency conversions
                    from_code = from_curr['code']
                    to_code = to_curr['code']
                    rate_key = f"{from_code}_{to_code}"
                    rate_value = exchange_rates.get(rate_key, "N/A")
                    
                    rate_pairs.append({
                        'from': from_code,
                        'from_emoji': from_curr['flag_emoji'],
                        'to': to_code,
                        'to_emoji': to_curr['flag_emoji'],
                        'rate': rate_value
                    })
        
        # Display in columns
        for idx in range(0, len(rate_pairs), cols_per_row):
            cols = st.columns(cols_per_row)
            for col_idx, col in enumerate(cols):
                pair_idx = idx + col_idx
                if pair_idx < len(rate_pairs):
                    pair = rate_pairs[pair_idx]
                    with col:
                        if isinstance(pair['rate'], (int, float)):
                            st.metric(
                                f"{pair['from_emoji']} {pair['from']} → {pair['to_emoji']} {pair['to']}",
                                f"{pair['rate']:.4f}"
                            )
                        else:
                            st.metric(
                                f"{pair['from_emoji']} {pair['from']} → {pair['to_emoji']} {pair['to']}",
                                pair['rate']
                            )

    st.divider()

    # Display commodities section with prices
    st.subheader("🥇 Commodity Prices")
    
    commodities = db.get_commodities()
    
    if not commodities:
        st.info("No commodities configured yet. Add commodities in the **Commodities** settings.")
    else:
        # Unit selector dropdown
        unit_options = ["ounce", "gram", "kilogram", "pound", "ton"]
        
        # Initialize session state for selected unit if not exists
        if "commodity_display_unit" not in st.session_state:
            st.session_state.commodity_display_unit = "ounce"
        
        # Unit selector
        col_unit1, col_unit2 = st.columns([1, 3])
        with col_unit1:
            selected_unit = st.selectbox(
                "Display Unit",
                options=unit_options,
                index=unit_options.index(st.session_state.commodity_display_unit),
                key="page_unit_selector",
                help="Select the unit for displaying commodity prices"
            )
        
        # Update session state if unit changed
        if selected_unit != st.session_state.commodity_display_unit:
            st.session_state.commodity_display_unit = selected_unit
            st.rerun()
        
        st.write("")  # Add spacing
        
        # Fetch commodity prices for selected date
        commodity_names = [c['name'] for c in commodities]
        
        with st.spinner(f"Fetching commodity prices for {selected_date.strftime('%B %d, %Y')}..."):
            commodity_prices = CurrencyConverter.get_commodity_prices(commodity_names, enabled_currencies, date=date_str)
        
        if commodity_prices:
            st.write(f"**Current Commodity Prices (per {selected_unit}):**")
            
            # Display each commodity with its prices in different currencies
            for commodity in commodities:
                commodity_name = commodity['name']
                
                if commodity_name in commodity_prices:
                    st.markdown(f"### {commodity['symbol']} {commodity_name}")
                    
                    # Display prices in columns
                    cols_per_row = min(3, len(enabled_currencies))
                    prices = commodity_prices[commodity_name]
                    
                    currency_list = list(prices.keys())
                    for idx in range(0, len(currency_list), cols_per_row):
                        cols = st.columns(cols_per_row)
                        for col_idx, col in enumerate(cols):
                            curr_idx = idx + col_idx
                            if curr_idx < len(currency_list):
                                currency_code = currency_list[curr_idx]
                                # Get base price (per ounce from API)
                                base_price = prices[currency_code]
                                
                                # Convert price to selected unit
                                converted_price = CurrencyConverter.convert_commodity_unit(
                                    base_price,
                                    "ounce",  # API returns prices per ounce
                                    selected_unit
                                )
                                
                                # Get currency details for emoji
                                curr_details = db.get_currency_by_code(currency_code)
                                emoji = curr_details['flag_emoji'] if curr_details else ""
                                
                                with col:
                                    st.metric(
                                        f"{emoji} {currency_code}",
                                        f"{converted_price:,.2f}",
                                        help=f"Price per {selected_unit} in {currency_code}"
                                    )
                    
                    st.write("")  # Spacing
        else:
            st.warning("⚠️ Unable to fetch commodity prices. Using configured commodities only.")
            st.write("**Configured Commodities:**")
            
            # Display commodities in a grid without prices
            cols_per_row = 3
            for idx in range(0, len(commodities), cols_per_row):
                cols = st.columns(cols_per_row)
                for col_idx, col in enumerate(cols):
                    comm_idx = idx + col_idx
                    if comm_idx < len(commodities):
                        commodity = commodities[comm_idx]
                        with col:
                            st.markdown(
                                f"""
                                <div style="padding: 1rem; border-radius: 0.5rem; background-color: {commodity['color']}20; border: 2px solid {commodity['color']};">
                                    <div style="font-size: 2rem; text-align: center;">{commodity['symbol']}</div>
                                    <div style="font-weight: bold; text-align: center; margin-top: 0.5rem;">{commodity['name']}</div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
        
        st.info("💡 **Note:** Commodity prices are fetched from live market data and displayed per troy ounce by default. Use the unit selector above to view prices in different units (gram, kilogram, pound, ton). When multiple currencies are configured, prices are calculated using current exchange rates.")

    st.divider()

    # Exchange rate information
    with st.expander("ℹ️ About Exchange Rates & Commodity Prices"):
        st.write("""
        **Source:** Exchange rates and commodity prices are fetched from the Frankfurter API (v2)

        **Update Frequency:** Rates are updated daily

        **Historical Data:** You can view historical exchange rates and commodity prices by selecting a past date.
        The Frankfurter API provides historical data from 1999 onwards for currencies, and from 2005 onwards for Gold (XAU),
        2019 onwards for Silver (XAG), and 2026 onwards for Platinum (XPT) and Palladium (XPD).
        
        **Weekend/Holiday Handling:** When you select a weekend or holiday date, the API automatically returns the last working day's prices.

        **Commodity Pricing:**
        - All commodity prices from the API are per **troy ounce** (the standard unit for precious metals)
        - 1 troy ounce = 31.1035 grams
        - When you change the display unit, prices are automatically converted from troy ounces
        - For multiple currencies, the base price is fetched from the API, then converted to other currencies using exchange rates

        **Usage:** These rates are automatically used when calculating net worth across different currencies

        **Supported Commodities:** Gold (XAU), Silver (XAG), Platinum (XPT), and Palladium (XPD) are supported directly through the Frankfurter API.
        """)
