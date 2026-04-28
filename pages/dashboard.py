"""
KUYAN - Dashboard Page Module
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
    get_converted_account_value,
    calculate_total_net_worth,
    get_current_mortgage_balance,
    get_all_mortgage_balances,
    get_theme_colors,
    generate_amortization_schedule,
    format_currency,
    get_property_equity_data,
    calculate_total_property_assets,
    calculate_total_property_liabilities
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
    # Note: excluded_types will be set later in the UI, so we'll recalculate after the filter is shown
    net_worths = {}
    for currency in enabled_currencies:
        net_worths[currency['code']] = calculate_total_net_worth(latest_snapshots, currency['code'], db)

    # Get all mortgage balances
    all_mortgage_balances = get_all_mortgage_balances(db)
    
    # Calculate total debt across all mortgages
    total_debt_by_currency = {}
    
    if all_mortgage_balances:
        # Get exchange rates for currency conversion
        rates = json.loads(latest_snapshots[0]["exchange_rates"]) if latest_snapshots[0].get("exchange_rates") else {}
        
        # Calculate total debt in each enabled currency
        for currency in enabled_currencies:
            total_debt = 0.0
            for mortgage in all_mortgage_balances:
                # Convert each mortgage balance to the target currency
                converted_balance = get_converted_value(
                    mortgage["balance"],
                    mortgage["currency"],
                    currency['code'],
                    rates
                )
                total_debt += converted_balance
            total_debt_by_currency[currency['code']] = total_debt
    
    # Get theme colors for metric cards (used in multiple sections)
    colors = get_theme_colors()
    
    # Add filter for account types to exclude
    # Get all unique account types from latest snapshots
    all_account_types = sorted(list(set([s["account_type"] for s in latest_snapshots])))
    
    # Add "Property" as a special filter option
    all_filter_options = all_account_types + ["Property"]
    
    # Create a multiselect for excluding account types
    # Default to excluding "Property" and "Pension"
    default_excluded = ["Property", "Pension"]  # Property and Pension excluded by default
    
    col_filter1, col_filter2 = st.columns([2, 2])
    with col_filter1:
        # Display current net worth in all currencies with flags
        st.subheader("Current Net Worth")
        st.caption("Total value across all accounts and currencies")
    with col_filter2:
        excluded_types = st.multiselect(
            "Exclude Account Types from Net Worth:",
            options=all_filter_options,
            default=default_excluded,
            key="excluded_account_types",
            help="Select account types to exclude from net worth calculations. Property equity and Pension are excluded by default."
        )
    
    # Check if Property should be included in net worth
    include_property_equity = "Property" not in excluded_types
    
    # Get exchange rates for property equity calculations
    rates = json.loads(latest_snapshots[0]["exchange_rates"]) if latest_snapshots[0].get("exchange_rates") else {}
    
    # Recalculate net worths with excluded account types
    net_worths = {}
    for currency in enabled_currencies:
        net_worth = calculate_total_net_worth(
            latest_snapshots,
            currency['code'],
            db,
            excluded_account_types=excluded_types
        )
        
        # Add property equity if not excluded
        if include_property_equity:
            property_equity = calculate_total_property_assets(db, currency['code'], rates) - \
                            calculate_total_property_liabilities(db, currency['code'], rates)
            net_worth += property_equity
        
        net_worths[currency['code']] = net_worth

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

    # Display Total Debt section if there are any mortgages
    if all_mortgage_balances and any(m["balance"] > 0 for m in all_mortgage_balances):
        st.subheader("Total Debt")
        
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
        
        for row_currencies in debt_rows:
            cols = st.columns(len(row_currencies))
            
            for idx, currency in enumerate(row_currencies):
                with cols[idx]:
                    curr_symbol = get_currency_symbol(currency['code'])
                    debt_in_currency = total_debt_by_currency.get(currency['code'], 0.0)
                    
                    st.markdown(f"""
                    <div style="background-color: {colors['bg_secondary']}; padding: 20px; border-radius: 10px; border-left: 5px solid #dc3545;">
                        <p style="margin: 0; font-size: 14px; color: {colors['text_secondary']};">{currency['flag_emoji']} {currency['code']}</p>
                        <p style="margin: 0; font-size: 28px; font-weight: bold; color: #dc3545;">{curr_symbol}{debt_in_currency:,.2f}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            if row_currencies != debt_rows[-1]:
                st.write("")
        
        # Show breakdown of individual mortgages in an expander
        if len(all_mortgage_balances) > 1:
            st.write("")
            with st.expander(f"📋 Mortgage Breakdown ({len(all_mortgage_balances)} mortgages)", expanded=False):
                for mortgage in all_mortgage_balances:
                    mortgage_symbol = get_currency_symbol(mortgage["currency"])
                    st.markdown(f"**{mortgage['mortgage_name']}**: {mortgage_symbol}{mortgage['balance']:,.2f} {mortgage['currency']}")
        
        st.divider()

    # Account breakdown table
    col_header, col_currency = st.columns([2, 2])
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
        # Filter snapshots based on excluded account types
        filtered_snapshots = [s for s in latest_snapshots if s.get("account_type") not in excluded_types]
        
        if not filtered_snapshots:
            st.info("All accounts are excluded. Adjust the filter to see account breakdown.")
        else:
            rates = json.loads(filtered_snapshots[0]["exchange_rates"]) if filtered_snapshots[0].get("exchange_rates") else {}
            
            # Fetch commodity prices for the snapshot date
            snapshot_date_str = filtered_snapshots[0]["snapshot_date"]
            commodity_accounts = [s for s in filtered_snapshots if s["account_type"] == "Commodity"]
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

            for snapshot in filtered_snapshots:
                is_commodity = snapshot["account_type"] == "Commodity"
                
                # Use the new unified function to get converted value
                converted_value = get_converted_account_value(
                    snapshot,
                    base_currency,
                    rates,
                    commodity_prices,
                    commodity_configs
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

    # Time-series graphs (only show if multiple snapshots exist)
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
            net_worth = calculate_total_net_worth(snapshots, selected_currency, db, excluded_account_types=excluded_types)

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
            
            # Filter snapshots based on excluded account types
            filtered_snapshots_for_chart = [s for s in snapshots if s.get("account_type") not in excluded_types]

            # Calculate totals for each currency (not converted) - dynamically initialize
            currency_totals = {curr: 0.0 for curr in enabled_currency_codes}

            for snapshot in filtered_snapshots_for_chart:
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
    else:
        # Show message only for time-series graphs
        st.info("Add more monthly snapshots to see trends over time")
        st.divider()
    
    # Create two columns for pie charts (show regardless of snapshot count)
    pie_col1, pie_col2 = st.columns(2)
    
    # Get latest snapshots for pie charts
    latest_snapshots_for_pie = db.get_latest_snapshots()
    
    if latest_snapshots_for_pie:
        # Filter snapshots based on excluded account types
        filtered_snapshots_for_pie = [s for s in latest_snapshots_for_pie if s.get("account_type") not in excluded_types]
        
        if not filtered_snapshots_for_pie:
            st.info("All accounts are excluded. Adjust the filter to see pie charts.")
        else:
            # Prepare data for pie charts
            rates = json.loads(filtered_snapshots_for_pie[0]["exchange_rates"]) if filtered_snapshots_for_pie[0].get("exchange_rates") else {}
            snapshot_date_str = filtered_snapshots_for_pie[0]["snapshot_date"]
            
            # Fetch commodity prices
            commodity_accounts = [s for s in filtered_snapshots_for_pie if s["account_type"] == "Commodity"]
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
            
            for snapshot in filtered_snapshots_for_pie:
                # Use the unified function to get converted value (handles both regular and commodity accounts)
                converted_value = get_converted_account_value(
                    snapshot,
                    base_currency,
                    rates,
                    commodity_prices,
                    commodity_configs
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

    # Property Assets & Liabilities Section
    property_equity_data = get_property_equity_data(db)
    
    if property_equity_data:
        st.subheader("🏘️ Property Assets & Liabilities")
        
        # Calculate totals across all properties
        total_property_assets = sum(p['market_value'] for p in property_equity_data)
        total_property_liabilities = sum(p['total_debt'] for p in property_equity_data)
        total_equity = total_property_assets - total_property_liabilities
        
        # Display summary metrics
        prop_col1, prop_col2, prop_col3 = st.columns(3)
        
        with prop_col1:
            st.markdown(f"""
            <div style="background-color: {colors['bg_secondary']}; padding: 20px; border-radius: 10px; border-left: 5px solid #28a745;">
                <p style="margin: 0; font-size: 14px; color: {colors['text_secondary']};">Total Property Assets</p>
                <p style="margin: 0; font-size: 28px; font-weight: bold; color: #28a745;">{get_currency_symbol(base_currency)}{total_property_assets:,.2f}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with prop_col2:
            st.markdown(f"""
            <div style="background-color: {colors['bg_secondary']}; padding: 20px; border-radius: 10px; border-left: 5px solid #dc3545;">
                <p style="margin: 0; font-size: 14px; color: {colors['text_secondary']};">Total Property Liabilities</p>
                <p style="margin: 0; font-size: 28px; font-weight: bold; color: #dc3545;">{get_currency_symbol(base_currency)}{total_property_liabilities:,.2f}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with prop_col3:
            equity_color = "#28a745" if total_equity >= 0 else "#dc3545"
            st.markdown(f"""
            <div style="background-color: {colors['bg_secondary']}; padding: 20px; border-radius: 10px; border-left: 5px solid {equity_color};">
                <p style="margin: 0; font-size: 14px; color: {colors['text_secondary']};">Total Equity</p>
                <p style="margin: 0; font-size: 28px; font-weight: bold; color: {equity_color};">{get_currency_symbol(base_currency)}{total_equity:,.2f}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.write("")
        
        # Display individual property details in an expander
        with st.expander(f"📋 Property Details ({len(property_equity_data)} properties)", expanded=False):
            for prop in property_equity_data:
                st.markdown(f"### {prop['property_name']}")
                
                detail_col1, detail_col2, detail_col3, detail_col4 = st.columns(4)
                
                with detail_col1:
                    st.metric("Type", prop['property_type'])
                    st.metric("Owner", prop['owner'])
                
                with detail_col2:
                    st.metric("Market Value", format_currency(prop['market_value'], prop['currency']))
                    if prop['valuation_date']:
                        st.caption(f"As of {prop['valuation_date']}")
                
                with detail_col3:
                    st.metric("Total Debt", format_currency(prop['total_debt'], prop['currency']))
                    if prop['linked_mortgages']:
                        st.caption(f"{len(prop['linked_mortgages'])} mortgage(s)")
                
                with detail_col4:
                    equity_delta = f"{prop['equity_percentage']:.1f}%" if prop['market_value'] > 0 else "N/A"
                    st.metric("Equity", format_currency(prop['equity'], prop['currency']), delta=equity_delta)
                
                # Show linked mortgages
                if prop['linked_mortgages']:
                    st.markdown("**Linked Mortgages:**")
                    for mortgage in prop['linked_mortgages']:
                        mortgage_symbol = get_currency_symbol(mortgage['currency'])
                        st.markdown(f"- {mortgage['name']}: {mortgage_symbol}{mortgage['balance']:,.2f}")
                
                # Add ownership split chart for this property
                st.markdown("**Ownership Split:**")
                chart_col1, chart_col2 = st.columns([1, 1])
                
                with chart_col1:
                    # Create donut chart for property ownership
                    ownership_data = pd.DataFrame([
                        {"Category": "Your Equity", "Value": prop['equity']},
                        {"Category": "Mortgage Balance", "Value": prop['total_debt']}
                    ])
                    
                    fig_ownership = px.pie(
                        ownership_data,
                        values="Value",
                        names="Category",
                        title=f"Ownership Split",
                        hole=0.5,
                        color="Category",
                        color_discrete_map={
                            "Your Equity": "#10b981",
                            "Mortgage Balance": "#ef4444"
                        }
                    )
                    
                    currency_symbol = get_currency_symbol(prop['currency'])
                    fig_ownership.update_traces(
                        textposition='inside',
                        textinfo='percent',
                        hovertemplate=f'<b>%{{label}}</b><br>Value: {currency_symbol}%{{value:,.2f}}<br>Percentage: %{{percent}}<extra></extra>',
                        textfont_size=16
                    )
                    
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
                                text=f"{prop['equity_percentage']:.1f}%<br>Owned",
                                x=0.5, y=0.5,
                                font_size=20,
                                font_color=colors['text_primary'],
                                showarrow=False
                            )
                        ]
                    )
                    
                    st.plotly_chart(fig_ownership, use_container_width=True)
                
                with chart_col2:
                    st.write("")  # Empty column for spacing
                
                st.divider()
        
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
            total = calculate_total_net_worth(snapshots, yoy_currency, db, excluded_account_types=excluded_types)
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
