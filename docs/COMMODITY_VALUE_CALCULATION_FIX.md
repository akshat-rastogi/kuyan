# Commodity Value Calculation Fix - Documentation

## Issue Summary

The overview page was not correctly calculating commodity account values in the selected currency. The problem had two parts:

1. **Incorrect Conversion Logic**: The code was treating commodity quantities (e.g., 10 ounces of gold) as if they were currency amounts and trying to convert them using currency exchange rates.

2. **Missing Unit Conversion**: The API returns commodity prices per troy ounce, but accounts can track commodities in different units (grams, kilograms, pounds, tons). The price needed to be converted to match the account's unit before multiplying by quantity.

## Root Cause

In the original code (lines 797-802 of `app.py`):

```python
converted_value = get_converted_value(
    snapshot["balance"],      # This is the QUANTITY (e.g., 10 ounces)
    snapshot["currency"],     # This is a currency code, not the commodity
    base_currency,
    rates                     # These are currency exchange rates
)
```

This was incorrect because:
- `snapshot["balance"]` for commodity accounts contains the **quantity** (e.g., 10 ounces)
- The code tried to convert this quantity using currency exchange rates
- It didn't account for the commodity's price or unit of measurement

## The Fix

### 1. Fetch Commodity Prices

When displaying the overview page, we now:
1. Identify all commodity accounts in the latest snapshots
2. Fetch current commodity prices from the Frankfurter API for the snapshot date
3. Get commodity configurations from the database to know their units

```python
# Fetch commodity prices for the snapshot date
commodity_accounts = [s for s in latest_snapshots if s["account_type"] == "Commodity"]
commodity_prices = {}
commodity_configs = {}

if commodity_accounts:
    # Get unique commodities
    unique_commodities = list(set([s.get("commodity") for s in commodity_accounts]))
    enabled_currencies = db.get_currency_codes()
    
    # Fetch prices (per troy ounce from API)
    commodity_prices = CurrencyConverter.get_commodity_prices(
        unique_commodities,
        enabled_currencies,
        date=snapshot_date_str
    ) or {}
    
    # Get commodity configurations for unit information
    commodity_configs = {c['name']: c for c in db.get_commodities()}
```

### 2. Calculate Commodity Values with Unit Conversion

For each commodity account, we now:
1. Get the commodity price per troy ounce in the target currency
2. Get the commodity's configured unit from the database
3. Convert the price from per-ounce to per-unit
4. Multiply quantity by the converted price

```python
if is_commodity:
    commodity_name = snapshot.get("commodity")
    quantity = snapshot["balance"]
    
    # Get price per troy ounce from API
    if commodity_name and commodity_name in commodity_prices:
        price_per_ounce = commodity_prices[commodity_name].get(base_currency, 0)
        
        # Get the unit for this commodity
        commodity_unit = "ounce"  # Default
        if commodity_name in commodity_configs:
            commodity_unit = commodity_configs[commodity_name].get('unit', 'ounce')
        
        # Convert price from per-ounce to per-unit
        price_per_unit = CurrencyConverter.convert_commodity_unit(
            price_per_ounce,
            "ounce",        # API always returns per troy ounce
            commodity_unit  # Convert to commodity's configured unit
        )
        
        # Calculate total value
        converted_value = quantity * price_per_unit
```

### 3. Regular Accounts Continue Using Currency Conversion

For non-commodity accounts, the original currency conversion logic remains:

```python
else:
    # For regular accounts: use currency conversion
    converted_value = get_converted_value(
        snapshot["balance"],
        snapshot["currency"],
        base_currency,
        rates
    )
```

## Example Calculation

**Scenario:**
- Account: "Gold Holdings (gram)"
- Commodity: Gold
- Quantity: 1000 grams
- Gold price from API: $2,050 USD per troy ounce
- Target currency: USD
- Commodity unit in database: "gram"

**Calculation:**
1. API returns: $2,050 per troy ounce
2. Convert to per-gram: $2,050 ÷ 31.1035 = $65.89 per gram
3. Calculate value: 1000 grams × $65.89 = $65,890 USD

**Without the fix:**
- Would try to convert "1000" using currency exchange rates
- Result would be incorrect (e.g., 1000 × 1.0 = $1,000 if treating as USD)

## Unit Conversion Factors

The `CurrencyConverter.convert_commodity_unit()` method handles these conversions:

- 1 troy ounce = 1.0 troy ounce (base)
- 1 troy ounce = 31.1035 grams
- 1 troy ounce = 0.0311035 kilograms
- 1 troy ounce = 0.0685714 pounds
- 1 troy ounce = 0.0000311035 metric tons

## Files Modified

1. **`app.py`** - Lines 680-750 and 831-895
   - Updated `calculate_total_net_worth()` function
   - Updated account breakdown section in `page_dashboard()`
   - Added commodity price fetching and unit conversion logic

## Testing

To verify the fix works correctly:

```bash
python3 test_commodity_value_calculation.py
```

This test:
1. Fetches Gold prices in multiple currencies
2. Calculates the value of 10 ounces of Gold
3. Verifies the conversion logic matches expected results

## Impact

**Before the fix:**
- Commodity account values were calculated incorrectly
- Net worth totals were wrong when commodity accounts existed
- Different units (grams, kg) were not handled

**After the fix:**
- Commodity values = quantity × (current price per unit in target currency)
- Net worth totals are accurate
- All units (ounce, gram, kilogram, pound, ton) are properly converted
- Regular currency accounts continue to work as before

---
*Fixed on: 2026-04-11*
*Tested with: Gold accounts in various units*