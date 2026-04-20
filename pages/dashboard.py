"""
KUYAN - Dashboard Page Module
Copyright (c) 2025 mycloudcondo inc.
Licensed under MIT License - see LICENSE file for details
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import json
from currencyConverter import CurrencyConverter
from components import render_currency_selector, render_data_table
from helper import (
    get_default_currency,
    get_currency_symbol,
    get_converted_value,
    calculate_total_net_worth,
    get_current_mortgage_balance,
    get_theme_colors,
    generate_amortization_schedule,
    format_currency
)


def dashboard(db):
    """
    Render the dashboard page showing net worth, account breakdown, and charts.
    
    Args:
        db: Database instance
    """
    # Get default base currency (first enabled currency)
    default_currency = get_default_currency(db)
    base_currency = st.session_state.get("base_currency", default_currency)

    # Get latest snapshots
    latest_snapshots = db.get_latest_snapshots()

    if not latest_snapshots:
        st.info("No data available. Add accounts and create your first monthly snapshot!")
        return

    # Get enabled currencies
    enabled_currencies = db.get_currencies()

    # Calculate current net worth in all enabled currencies
    net_worths = {}
    for currency in enabled_currencies:
        net_worths[currency['code']] = calculate_total_net_worth(latest_snapshots, currency['code'], db)

    # Get current mortgage balance (debt) and its currency
    mortgage_balance, mortgage_currency = get_current_mortgage_balance(db)
    
    # Display Total Debt section if there is a mortgage
    if mortgage_balance > 0:
        st.subheader("Total Debt")
        
        # Get theme colors for metric cards
        colors = get_theme_colors()
        
        # Display debt in all enabled currencies
        debt_rows = []
        num_currencies = len(enabled_currencies)
        
        if num_currencies <= 4:
            debt_rows = [enabled_currencies]
        elif num_currencies <= 6:
            mid = (num_currencies + 1) // 2
            debt_rows = [enabled_currencies[:mid], enabled_currencies[mid:]]
        else:
            third = (num_currencies + 2) // 3
            debt_rows = [
                enabled_currencies[:third],
                enabled_currencies[third:third*2],
                enabled_currencies[third*2:]
            ]
        
        # Get exchange rates for currency conversion
        rates = json.loads(latest_snapshots[0]["exchange_rates"]) if latest_snapshots[0].get("exchange_rates") else {}
        
        for row_currencies in debt_rows:
            cols = st.columns(len(row_currencies))
            
            for idx, currency in enumerate(row_currencies):
                with cols[idx]:
                    curr_symbol = get_currency_symbol(currency['code'])
                    # Convert mortgage balance from its currency to target currency
                    debt_in_currency = get_converted_value(mortgage_balance, mortgage_currency, currency['code'], rates)
                    
                    st.markdown(f"""
                    <div style="background-color: {colors['bg_secondary']}; padding: 20px; border-radius: 10px; border-left: 5px solid #dc3545;">
                        <p style="margin: 0; font-size: 14px; color: {colors['text_secondary']};">{currency['flag_emoji']} {currency['code']}</p>
                        <p style="margin: 0; font-size: 28px; font-weight: bold; color: #dc3545;">{curr_symbol}{debt_in_currency:,.2f}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            if row_currencies != debt_rows[-1]:
                st.write("")
        
        st.divider()

    # Display current net worth in all currencies with flags
    st.subheader("Current Net Worth")

    # Get theme colors for metric cards
    colors = get_theme_colors()

    # Smart row distribution to prevent wrapping
    # 1-4 currencies: 1 row (up to 4 columns)
    # 5-6 currencies: 2 rows (3 columns each)
    # 7-9 currencies: 3 rows (3 columns each)
    num_currencies = len(enabled_currencies)

    if num_currencies <= 4:
        rows = [enabled_currencies]  # All in one row
    elif num_currencies <= 6:
        # Split into 2 rows of 3 each
        mid = (num_currencies + 1) // 2
        rows = [enabled_currencies[:mid], enabled_currencies[mid:]]
    else:
        # Split into 3 rows of 3 each
        third = (num_currencies + 2) // 3
        rows = [
            enabled_currencies[:third],
            enabled_currencies[third:third*2],
            enabled_currencies[third*2:]
        ]

    # Render each row
    for row_currencies in rows:
        cols = st.columns(len(row_currencies))

        for idx, currency in enumerate(row_currencies):
            with cols[idx]:
                curr_symbol = get_currency_symbol(currency['code'])
                net_worth = net_worths[currency['code']]

                st.markdown(f"""
                <div style="background-color: {colors['bg_secondary']}; padding: 20px; border-radius: 10px; border-left: 5px solid {currency['color']};">
                    <p style="margin: 0; font-size: 14px; color: {colors['text_secondary']};">{currency['flag_emoji']} {currency['code']}</p>
                    <p style="margin: 0; font-size: 28px; font-weight: bold; color: {colors['text_primary']};">{curr_symbol}{net_worth:,.2f}</p>
                </div>
                """, unsafe_allow_html=True)

        # Add small spacing between rows
        if row_currencies != rows[-1]:
            st.write("")

    st.divider()

    # Account breakdown table
    col_header, col_currency = st.columns([3, 1])
    with col_header:
        st.subheader("Account Breakdown")
        st.caption("Currency conversions use exchange rates from the 1st of the snapshot month")
    with col_currency:
        base_currency = render_currency_selector(
            label="Select Currency",
            default_index=0,
            key="currency_selector"
        )
        # Update session state for other pages
        st.session_state.base_currency = base_currency

    if latest_snapshots:
        rates = json.loads(latest_snapshots[0]["exchange_rates"]) if latest_snapshots[0].get("exchange_rates") else {}
        
        # Fetch commodity prices for the snapshot date
        snapshot_date_str = latest_snapshots[0]["snapshot_date"]
        commodity_accounts = [s for s in latest_snapshots if s["account_type"] == "Commodity"]
        commodity_prices = {}
        commodity_configs = {}
        
        if commodity_accounts:
            # Get unique commodities and enabled currencies
            commodity_list = [s.get("commodity") for s in commodity_accounts if s.get("commodity")]
            unique_commodities = list(set([c for c in commodity_list if c is not None]))  # Remove duplicates and None
            enabled_currencies = db.get_currency_codes()
            
            # Fetch commodity prices for the snapshot date (prices are per troy ounce)
            commodity_prices = CurrencyConverter.get_commodity_prices(
                unique_commodities,
                enabled_currencies,
                date=snapshot_date_str
            ) or {}
            
            # Get commodity configurations to know the units
            commodity_configs = {c['name']: c for c in db.get_commodities()}

        breakdown_data = []
        total_converted = 0.0

        for snapshot in latest_snapshots:
            is_commodity = snapshot["account_type"] == "Commodity"
            
            if is_commodity:
                # For commodity accounts: quantity * price per unit in target currency
                commodity_name = snapshot.get("commodity")
                quantity = snapshot["balance"]
                
                # Get commodity price in base currency (API returns price per troy ounce)
                if commodity_name and commodity_name in commodity_prices:
                    price_per_ounce = commodity_prices[commodity_name].get(base_currency, 0)
                    
                    # Get the unit for this commodity from database
                    commodity_unit = "ounce"  # Default to ounce
                    if commodity_name in commodity_configs:
                        commodity_unit = commodity_configs[commodity_name].get('unit', 'ounce')
                    
                    # Convert price from per-ounce to per-unit
                    price_per_unit = CurrencyConverter.convert_commodity_unit(
                        price_per_ounce,
                        "ounce",  # API always returns per troy ounce
                        commodity_unit  # Convert to the commodity's configured unit
                    )
                    
                    # Calculate total value: quantity * price per unit
                    converted_value = quantity * price_per_unit
                else:
                    # Fallback: if no price available, use 0
                    converted_value = 0.0
                    
            else:
                # For regular accounts: use currency conversion
                converted_value = get_converted_value(
                    snapshot["balance"],
                    snapshot["currency"],
                    base_currency,
                    rates
                )
            
            total_converted += converted_value

            # For commodity accounts, show commodity name instead of currency
            native_currency_display = snapshot.get("commodity", snapshot["currency"]) if is_commodity else snapshot["currency"]
            
            # For commodity accounts, show balance without currency symbol (just the amount with unit)
            if is_commodity:
                # Extract unit from account name (e.g., "Gold (ounce)" -> "ounce")
                account_name = snapshot["name"]
                unit = "units"
                if "(" in account_name and ")" in account_name:
                    unit = account_name[account_name.rfind("(")+1:account_name.rfind(")")]
                native_balance_display = f"{snapshot['balance']:,.2f} {unit}"
            else:
                native_balance_display = f"{get_currency_symbol(snapshot['currency'])}{snapshot['balance']:,.2f}"
            
            breakdown_data.append({
                "Account": snapshot["name"],
                "Owner": snapshot["owner"],
                "Type": snapshot["account_type"],
                "Native Currency": native_currency_display,
                "Native Balance": native_balance_display,
                f"{base_currency} Value": f"{get_currency_symbol(base_currency)}{converted_value:,.2f}"
            })

        # Get theme colors
        colors = get_theme_colors()
        
        # Use Streamlit's native expander with custom styling for the header
        # Create a styled header that looks like the total row
        st.markdown(f"""
        <style>
        div[data-testid="stExpander"] {{
            border: none;
            box-shadow: none;
        }}
        div[data-testid="stExpander"] > div:first-child {{
            padding: 15px;
            background-color: {colors['bg_secondary']};
            border-top: 2px solid {colors['border']};
            border-radius: 5px;
        }}
        div[data-testid="stExpander"] > div:first-child:hover {{
            opacity: 0.9;
        }}
        </style>
        """, unsafe_allow_html=True)
        
        # Create expander with styled label showing total
        with st.expander(f"**TOTAL {base_currency}** — {get_currency_symbol(base_currency)}{total_converted:,.2f}", expanded=False):
            # Display account breakdown table
            render_data_table(breakdown_data)

    st.divider()

    snapshot_dates = db.get_all_snapshot_dates()

    if len(snapshot_dates) > 1:
        # Create two columns for side-by-side graphs
        graph_col1, graph_col2 = st.columns(2)
        
        # Left column: Net Worth Over Time
        with graph_col1:
            # Net worth over time with currency selector
            st.markdown("#### Net Worth Over Time")

            # Currency selector
            selected_currency = render_currency_selector(
                label="Select Currency",
                default_index=0,
                key="networth_currency_selector"
            )

        # Right column: Currency Holdings Growth header and baseline selector
        with graph_col2:
            st.markdown("#### Currency Holdings Growth (Normalized)")
            
            # Baseline month selector
            # Convert dates to month labels for display (descending order - newest first)
            month_labels = [datetime.fromisoformat(d).strftime("%b %Y") for d in snapshot_dates]
            baseline_month_label = st.selectbox(
                "Baseline Month (100%)",
                options=month_labels,
                index=len(month_labels) - 1,  # Default to oldest month
                key="baseline_month_selector"
            )
            # Get the index of selected baseline (adjusted for reversed loop below)
            baseline_index = len(month_labels) - 1 - month_labels.index(baseline_month_label)

        # Collect data for selected currency
        history_data = []

        for snapshot_date in reversed(snapshot_dates):
            snapshots = db.get_snapshots_by_date(date.fromisoformat(snapshot_date))
            net_worth = calculate_total_net_worth(snapshots, selected_currency, db)

            # Use month label instead of full date (uppercase month, year on next line)
            dt = datetime.fromisoformat(snapshot_date)
            month_label = f"{dt.strftime('%b').upper()}<br>{dt.year}"
            history_data.append({
                "Month": month_label,
                "Net Worth": net_worth,
                "Date": snapshot_date  # Keep actual date for proper sorting
            })

        df_history = pd.DataFrame(history_data)
        # Sort by actual date to ensure chronological order
        df_history = df_history.sort_values('Date')

        # Build dynamic currency color map from database
        color_map = {}
        for curr in db.get_currencies():
            color_map[curr['code']] = curr['color']

        currency_symbol = get_currency_symbol(selected_currency)

        fig_line = px.line(
            df_history,
            x="Month",
            y="Net Worth",
            title=f"Total Net Worth in {selected_currency}",
            markers=True
        )

        # Apply color based on selected currency
        fig_line.update_traces(
            line_color=color_map[selected_currency],
            line=dict(width=3),
            marker=dict(size=8),
            hovertemplate=f'Net Worth: {currency_symbol}' + '%{y:,.2f}<br>' +
                         '<extra></extra>'
        )

        # Get theme colors
        colors = get_theme_colors()

        fig_line.update_layout(
            xaxis_title="Month",
            yaxis_title=f"Net Worth ({selected_currency})",
            hovermode="x unified",
            xaxis=dict(
                showline=True,
                linewidth=2,
                linecolor=colors['plot_axis'],
                mirror=False,
                showgrid=True,
                gridwidth=1,
                gridcolor=colors['plot_grid'],
                title_font=dict(size=14, family='Arial, sans-serif', color=colors['plot_text'], weight='bold'),
                showspikes=True,
                spikecolor=colors['plot_axis'],
                spikethickness=1,
                type='category',  # Treat as categorical to preserve order
                categoryorder='array',  # Use array order
                categoryarray=df_history['Month'].tolist()  # Explicit order from sorted data
            ),
            yaxis=dict(
                showline=True,
                linewidth=2,
                linecolor=colors['plot_axis'],
                mirror=False,
                showgrid=True,
                gridwidth=1,
                gridcolor=colors['plot_grid'],
                title_font=dict(size=14, family='Arial, sans-serif', color=colors['plot_text'], weight='bold'),
                showspikes=True,
                spikecolor=colors['plot_axis'],
                spikethickness=1
            ),
            plot_bgcolor=colors['plot_bg'],
            paper_bgcolor=colors['plot_bg'],
            font=dict(color=colors['plot_text']),
            title_font=dict(color=colors['text_primary']),
            hoverlabel=dict(
                bgcolor=colors['surface'],
                font_size=13,
                font_family="Arial, sans-serif",
                font_color=colors['text_primary']
            )
        )
        
        # Collect data for amounts held in each currency
        currency_split_data = []
        baseline_holdings = {}

        # Get all enabled currencies dynamically
        enabled_currency_codes = db.get_currency_codes()

        for i, snapshot_date in enumerate(reversed(snapshot_dates)):
            snapshots = db.get_snapshots_by_date(date.fromisoformat(snapshot_date))

            # Calculate totals for each currency (not converted) - dynamically initialize
            currency_totals = {curr: 0.0 for curr in enabled_currency_codes}

            for snapshot in snapshots:
                curr = snapshot["currency"]
                balance = snapshot["balance"]
                if curr in currency_totals:
                    currency_totals[curr] += balance

            # Store baseline values from selected month
            if i == baseline_index:
                for curr in enabled_currency_codes:
                    baseline_holdings[curr] = currency_totals[curr] if currency_totals[curr] > 0 else 1

            # Calculate percentage relative to baseline for each currency
            if baseline_holdings:  # Only calculate if baseline is set
                for currency, total in currency_totals.items():
                    pct = (total / baseline_holdings[currency] * 100) if baseline_holdings[currency] > 0 else 100
                    # Use month label instead of full date (uppercase month, year on next line)
                    dt = datetime.fromisoformat(snapshot_date)
                    month_label = f"{dt.strftime('%b').upper()}<br>{dt.year}"
                    currency_split_data.append({
                        "Month": month_label,
                        "Currency": currency,
                        "Growth %": pct
                    })

        df_currency_split = pd.DataFrame(currency_split_data)

        fig_split = px.line(
            df_currency_split,
            x="Month",
            y="Growth %",
            color="Currency",
            color_discrete_map=color_map,
            title=f"Currency Holdings Growth (Baseline: {baseline_month_label} = 100%)",
            markers=True
        )

        fig_split.update_traces(
            line=dict(width=3),
            marker=dict(size=8),
            hovertemplate='Growth: %{y:.1f}%<br>' +
                         '<extra></extra>'
        )

        # Get theme colors
        colors = get_theme_colors()

        fig_split.update_layout(
            xaxis_title="Month",
            yaxis_title=f"Growth Index ({baseline_month_label} = 100%)",
            hovermode="x unified",
            xaxis=dict(
                showline=True,
                linewidth=2,
                linecolor=colors['plot_axis'],
                mirror=False,
                showgrid=True,
                gridwidth=1,
                gridcolor=colors['plot_grid'],
                title_font=dict(size=14, family='Arial, sans-serif', color=colors['plot_text'], weight='bold'),
                showspikes=True,
                spikecolor=colors['plot_axis'],
                spikethickness=1
            ),
            yaxis=dict(
                showline=True,
                linewidth=2,
                linecolor=colors['plot_axis'],
                mirror=False,
                showgrid=True,
                gridwidth=1,
                gridcolor=colors['plot_grid'],
                title_font=dict(size=14, family='Arial, sans-serif', color=colors['plot_text'], weight='bold'),
                showspikes=True,
                spikecolor=colors['plot_axis'],
                spikethickness=1
            ),
            plot_bgcolor=colors['plot_bg'],
            paper_bgcolor=colors['plot_bg'],
            font=dict(color=colors['plot_text']),
            title_font=dict(color=colors['text_primary']),
            hoverlabel=dict(
                bgcolor=colors['surface'],
                font_size=13,
                font_family="Arial, sans-serif",
                font_color=colors['text_primary']
            ),
            legend=dict(
                title=dict(text="Currency", font=dict(weight='bold', color=colors['text_primary'])),
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor=colors['surface'],
                bordercolor=colors['border'],
                borderwidth=1,
                font=dict(color=colors['text_primary'])
            )
        )
        
        # Render both charts in their respective columns
        with graph_col1:
            st.plotly_chart(fig_line, use_container_width=True)
            st.markdown(
                '<p style="text-align: right; font-size: 0.6rem; margin-top: -10px;">* Monthly exchange rates are derived from rates effective on the 1st of each month</p>',
                unsafe_allow_html=True
            )
        
        with graph_col2:
            st.plotly_chart(fig_split, use_container_width=True)
        
        st.divider()
                
        # Create two columns for pie charts
        pie_col1, pie_col2 = st.columns(2)
        
        # Get latest snapshots for pie charts
        latest_snapshots = db.get_latest_snapshots()
        
        if latest_snapshots:
            # Prepare data for pie charts
            rates = json.loads(latest_snapshots[0]["exchange_rates"]) if latest_snapshots[0].get("exchange_rates") else {}
            snapshot_date_str = latest_snapshots[0]["snapshot_date"]
            
            # Fetch commodity prices
            commodity_accounts = [s for s in latest_snapshots if s["account_type"] == "Commodity"]
            commodity_prices = {}
            commodity_configs = {}
            
            if commodity_accounts:
                commodity_list = [s.get("commodity") for s in commodity_accounts if s.get("commodity")]
                unique_commodities = list(set([c for c in commodity_list if c is not None]))
                enabled_currencies = db.get_currency_codes()
                
                commodity_prices = CurrencyConverter.get_commodity_prices(
                    unique_commodities,
                    enabled_currencies,
                    date=snapshot_date_str
                ) or {}
                
                commodity_configs = {c['name']: c for c in db.get_commodities()}
            
            # Calculate values by owner and type
            value_by_owner = {}
            value_by_type = {}
            
            for snapshot in latest_snapshots:
                is_commodity = snapshot["account_type"] == "Commodity"
                
                if is_commodity:
                    commodity_name = snapshot.get("commodity")
                    quantity = snapshot["balance"]
                    
                    if commodity_name and commodity_name in commodity_prices:
                        price_per_ounce = commodity_prices[commodity_name].get(base_currency, 0)
                        commodity_unit = "ounce"
                        if commodity_name in commodity_configs:
                            commodity_unit = commodity_configs[commodity_name].get('unit', 'ounce')
                        
                        price_per_unit = CurrencyConverter.convert_commodity_unit(
                            price_per_ounce,
                            "ounce",
                            commodity_unit
                        )
                        converted_value = quantity * price_per_unit
                    else:
                        converted_value = 0.0
                else:
                    converted_value = get_converted_value(
                        snapshot["balance"],
                        snapshot["currency"],
                        base_currency,
                        rates
                    )
                
                # Aggregate by owner
                owner = snapshot["owner"]
                if owner not in value_by_owner:
                    value_by_owner[owner] = 0.0
                value_by_owner[owner] += converted_value
                
                # Aggregate by type
                acc_type = snapshot["account_type"]
                if acc_type not in value_by_type:
                    value_by_type[acc_type] = 0.0
                value_by_type[acc_type] += converted_value
            
            # Get theme colors
            colors = get_theme_colors()
            
            # Get currency symbol for pie charts
            currency_symbol = get_currency_symbol(base_currency)
            
            # Pie chart 1: Value by Owner
            with pie_col1:
                st.markdown("#### Value by Owner")
                
                df_owner = pd.DataFrame([
                    {"Owner": owner, "Value": value}
                    for owner, value in value_by_owner.items()
                ])
                
                fig_owner = px.pie(
                    df_owner,
                    values="Value",
                    names="Owner",
                    title=f"Value by Owner ({base_currency})"
                )
                
                fig_owner.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    hovertemplate=f'<b>%{{label}}</b><br>Value: {currency_symbol}%{{value:,.2f}}<br>Percentage: %{{percent}}<extra></extra>'
                )
                
                fig_owner.update_layout(
                    plot_bgcolor=colors['plot_bg'],
                    paper_bgcolor=colors['plot_bg'],
                    font=dict(color=colors['plot_text']),
                    title_font=dict(color=colors['text_primary']),
                    hoverlabel=dict(
                        bgcolor=colors['surface'],
                        font_size=13,
                        font_family="Arial, sans-serif",
                        font_color=colors['text_primary']
                    ),
                    showlegend=True,
                    legend=dict(
                        bgcolor=colors['surface'],
                        bordercolor=colors['border'],
                        borderwidth=1,
                        font=dict(color=colors['text_primary'])
                    )
                )
                
                st.plotly_chart(fig_owner, use_container_width=True)
            
            # Pie chart 2: Value by Type
            with pie_col2:
                st.markdown("#### Value by Type")
                
                df_type = pd.DataFrame([
                    {"Type": acc_type, "Value": value}
                    for acc_type, value in value_by_type.items()
                ])
                
                fig_type = px.pie(
                    df_type,
                    values="Value",
                    names="Type",
                    title=f"Value by Type ({base_currency})"
                )
                
                fig_type.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    hovertemplate=f'<b>%{{label}}</b><br>Value: {currency_symbol}%{{value:,.2f}}<br>Percentage: %{{percent}}<extra></extra>'
                )
                
                fig_type.update_layout(
                    plot_bgcolor=colors['plot_bg'],
                    paper_bgcolor=colors['plot_bg'],
                    font=dict(color=colors['plot_text']),
                    title_font=dict(color=colors['text_primary']),
                    hoverlabel=dict(
                        bgcolor=colors['surface'],
                        font_size=13,
                        font_family="Arial, sans-serif",
                        font_color=colors['text_primary']
                    ),
                    showlegend=True,
                    legend=dict(
                        bgcolor=colors['surface'],
                        bordercolor=colors['border'],
                        borderwidth=1,
                        font=dict(color=colors['text_primary'])
                    )
                )
                
                st.plotly_chart(fig_type, use_container_width=True)
        
        st.divider()
        
        # House Ownership Chart (if mortgage config exists)
        # Initialize mortgage configuration if not present in session state
        if "mortgage_config" not in st.session_state:
            # Try to load from database
            db_settings = db.get_mortgage_settings()
            if db_settings:
                st.session_state.mortgage_config = {
                    "lender_name": db_settings["lender_name"],
                    "loan_amount": float(db_settings["loan_amount"]),
                    "interest_rate": float(db_settings["interest_rate"]),
                    "loan_term_years": float(db_settings["loan_term_years"]),
                    "payments_per_year": int(db_settings["payments_per_year"]),
                    "start_date": date.fromisoformat(db_settings["start_date"]),
                    "recurring_extra_payment": float(db_settings["recurring_extra_payment"]),
                    "purchase_value": float(db_settings["purchase_value"]),
                    "present_value": float(db_settings["present_value"])
                }
        
        if "mortgage_config" in st.session_state:
            mortgage_config = st.session_state.mortgage_config
            
            # Check if we have the necessary mortgage data
            if (mortgage_config.get("loan_amount", 0) > 0 and
                mortgage_config.get("present_value", 0) > 0):
                
                st.markdown("#### House Ownership Overview")
                
                # Calculate ownership metrics
                present_value = mortgage_config.get("present_value", 0)
                purchase_value = mortgage_config.get("purchase_value", 0)
                
                # Calculate current mortgage balance from schedule (nearest date)
                try:
                    # Get mortgage settings from database
                    mortgage_settings = db.get_mortgage_settings()
                    if mortgage_settings:
                        # Get extra payments from database
                        extra_payments_data = db.get_mortgage_extra_payments()
                        custom_extra_payments = pd.DataFrame(extra_payments_data) if extra_payments_data else pd.DataFrame()
                        if not custom_extra_payments.empty:
                            custom_extra_payments = custom_extra_payments.rename(columns={
                                'payment_number': 'PMT NO',
                                'extra_payment_amount': 'EXTRA PAYMENT'
                            })
                        
                        # Generate amortization schedule
                        schedule_df, _ = generate_amortization_schedule(
                            loan_amount=mortgage_settings['loan_amount'],
                            annual_interest_rate=mortgage_settings['interest_rate'],
                            loan_term_years=mortgage_settings['loan_term_years'],
                            payments_per_year=mortgage_settings['payments_per_year'],
                            start_date=date.fromisoformat(mortgage_settings['start_date']),
                            recurring_extra_payment=mortgage_settings.get('recurring_extra_payment', 0.0),
                            custom_extra_payments=custom_extra_payments
                        )
                        
                        # Find the payment that has occurred most recently (on or before today)
                        today = date.today()
                        # Filter to only past/current payments
                        past_payments = schedule_df[schedule_df['PAYMENT DATE'] <= today]
                        
                        if not past_payments.empty:
                            # Use the most recent past payment's ending balance
                            loan_amount = past_payments.iloc[-1]['ENDING BALANCE']
                        else:
                            # If no payments have been made yet, use the original loan amount
                            loan_amount = mortgage_settings['loan_amount']
                    else:
                        # Fallback to initial loan amount if no settings found
                        loan_amount = mortgage_config.get("loan_amount", 0)
                except Exception as e:
                    # Fallback to initial loan amount on any error
                    # Print error for debugging
                    import traceback
                    print(f"Error calculating mortgage balance: {e}")
                    print(traceback.format_exc())
                    loan_amount = mortgage_config.get("loan_amount", 0)
                
                # Calculate equity (what you own)
                equity = present_value - loan_amount
                equity_percentage = (equity / present_value * 100) if present_value > 0 else 0
                mortgage_percentage = (loan_amount / present_value * 100) if present_value > 0 else 0
                
                # Create three columns for metrics and chart
                ownership_col1, ownership_col2, ownership_col3 = st.columns([1, 1, 2])
                
                with ownership_col1:
                    st.metric("Present Value", format_currency(present_value))
                    st.metric("Purchase Value", format_currency(purchase_value))
                
                with ownership_col2:
                    st.metric("Your Equity", format_currency(equity))
                    st.metric("Mortgage Balance", format_currency(loan_amount))
                
                with ownership_col3:
                    # Create donut chart showing ownership split
                    ownership_data = pd.DataFrame([
                        {"Category": "Your Equity", "Value": equity},
                        {"Category": "Mortgage Balance", "Value": loan_amount}
                    ])
                    
                    fig_ownership = px.pie(
                        ownership_data,
                        values="Value",
                        names="Category",
                        title=f"Ownership Split",
                        hole=0.5,  # Makes it a donut chart
                        color="Category",
                        color_discrete_map={
                            "Your Equity": "#10b981",  # Green for equity
                            "Mortgage Balance": "#ef4444"  # Red for mortgage
                        }
                    )
                    
                    fig_ownership.update_traces(
                        textposition='inside',
                        textinfo='percent',
                        hovertemplate='<b>%{label}</b><br>Value: €%{value:,.2f}<br>Percentage: %{percent}<extra></extra>',
                        textfont_size=16
                    )
                    
                    # Get theme colors
                    colors = get_theme_colors()
                    
                    fig_ownership.update_layout(
                        plot_bgcolor=colors['plot_bg'],
                        paper_bgcolor=colors['plot_bg'],
                        font=dict(color=colors['plot_text']),
                        title_font=dict(color=colors['text_primary'], size=16),
                        hoverlabel=dict(
                            bgcolor=colors['surface'],
                            font_size=13,
                            font_family="Arial, sans-serif",
                            font_color=colors['text_primary']
                        ),
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=-0.2,
                            xanchor="center",
                            x=0.5,
                            bgcolor=colors['surface'],
                            bordercolor=colors['border'],
                            borderwidth=1,
                            font=dict(color=colors['text_primary'])
                        ),
                        annotations=[
                            dict(
                                text=f"{equity_percentage:.1f}%<br>Owned",
                                x=0.5, y=0.5,
                                font_size=20,
                                font_color=colors['text_primary'],
                                showarrow=False
                            )
                        ]
                    )
                    
                    st.plotly_chart(fig_ownership, use_container_width=True)
                
                st.caption("💡 Based on present market value and current mortgage balance from Settings → Mortgage")
                st.divider()

        # Year-over-year comparison if we have enough data
        if len(snapshot_dates) >= 12:
            st.subheader("Year-over-Year Comparison")

            # Currency selector for YoY graph
            col1, col2 = st.columns([1, 3])
            with col1:
                yoy_currency = render_currency_selector(
                    label="Select Currency",
                    default_index=0,
                    key="yoy_currency_selector"
                )

            # Get all unique years from snapshots
            years = sorted(list(set([datetime.fromisoformat(d).year for d in snapshot_dates])))

            # Month names in order (uppercase)
            month_names = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

            # Create data structure with only months that have data
            yoy_data = []

            # Create a lookup dict for existing data
            data_lookup = {}
            for snapshot_date in snapshot_dates:
                dt = datetime.fromisoformat(snapshot_date)
                snapshots = db.get_snapshots_by_date(date.fromisoformat(snapshot_date))
                total = calculate_total_net_worth(snapshots, yoy_currency, db)
                key = (dt.year, dt.month)
                data_lookup[key] = total

            # Populate only months that have data (include year in x-axis label)
            for year in years:
                for month_num in range(1, 13):
                    key = (year, month_num)
                    if key in data_lookup:
                        yoy_data.append({
                            "Month": f"{month_names[month_num - 1]}<br>{year}",
                            "Year": str(year),
                            "Net Worth": data_lookup[key]
                        })

            df_yoy = pd.DataFrame(yoy_data)

            currency_symbol = get_currency_symbol(yoy_currency)
            fig_yoy = px.line(
                df_yoy,
                x="Month",
                y="Net Worth",
                color="Year",
                title=f"Year-over-Year Comparison ({yoy_currency})",
                markers=True
            )

            # Set month order
            fig_yoy.update_xaxes(categoryorder='array', categoryarray=month_names)

            fig_yoy.update_traces(
                line=dict(width=3),
                marker=dict(size=8),
                hovertemplate=f'Net Worth: {currency_symbol}' + '%{y:,.2f}<br>' +
                             '<extra></extra>'
            )

            # Get theme colors
            colors = get_theme_colors()

            fig_yoy.update_layout(
                hovermode="x unified",
                xaxis=dict(
                    showline=True,
                    linewidth=2,
                    linecolor=colors['plot_axis'],
                    mirror=False,
                    showgrid=True,
                    gridwidth=1,
                    gridcolor=colors['plot_grid'],
                    title_font=dict(size=14, family='Arial, sans-serif', color=colors['plot_text'], weight='bold'),
                    showspikes=True,
                    spikecolor=colors['plot_axis'],
                    spikethickness=1
                ),
                yaxis=dict(
                    showline=True,
                    linewidth=2,
                    linecolor=colors['plot_axis'],
                    mirror=False,
                    showgrid=True,
                    gridwidth=1,
                    gridcolor=colors['plot_grid'],
                    title_font=dict(size=14, family='Arial, sans-serif', color=colors['plot_text'], weight='bold'),
                    showspikes=True,
                    spikecolor=colors['plot_axis'],
                    spikethickness=1
                ),
                plot_bgcolor=colors['plot_bg'],
                paper_bgcolor=colors['plot_bg'],
                font=dict(color=colors['plot_text']),
                title_font=dict(color=colors['text_primary']),
                hoverlabel=dict(
                    bgcolor=colors['surface'],
                    font_size=13,
                    font_family="Arial, sans-serif",
                    font_color=colors['text_primary']
                ),
                legend=dict(
                    title=dict(text="Year", font=dict(weight='bold', color=colors['text_primary'])),
                    bgcolor=colors['surface'],
                    bordercolor=colors['border'],
                    borderwidth=1,
                    font=dict(color=colors['text_primary'])
                )
            )
            st.plotly_chart(fig_yoy, use_container_width=True)
            st.markdown(
                '<p style="text-align: right; font-size: 0.6rem; margin-top: -10px;">* Monthly exchange rates are derived from rates effective on the 1st of each month</p>',
                unsafe_allow_html=True
            )
            st.divider()
    else:
        st.info("Add more monthly snapshots to see trends over time")
