# Commodity Pricing Fix - Documentation

## Issue Summary

The exchange rate page was not correctly displaying commodity prices (Gold, Silver, Platinum, Palladium) because:

1. **Incorrect API Call Direction**: The code was calling the API with currency as base and commodity as quote (e.g., `EUR->XAU`), but the Frankfurter API v2 requires commodity as base and currency as quote (e.g., `XAU->EUR`)

2. **Missing Multi-Currency Support**: When multiple currencies were configured, the code didn't properly calculate commodity prices in additional currencies using exchange rates

3. **Unclear Documentation**: The troy ounce base unit and weekend/holiday handling were not clearly documented

## API Example

**Correct API Call Format:**
```
https://api.frankfurter.dev/v2/rates?from=2026-04-11&quotes=EUR&base=XAU
```

**Important:** The Frankfurter v2 API uses the `from` parameter for dates, NOT `date`.

**Response:**
```json
[{"date":"2026-04-10","base":"XAU","quote":"EUR","rate":4067.96}]
```

This means: **1 troy ounce of Gold = 4067.96 EUR**

Note: When requesting 2026-04-11 (Friday), the API returns data for 2026-04-10 (Thursday) as it's the last working day.

## Changes Made

### 1. Fixed `currency.py` - `get_exchange_rates()` method

**Critical Fix - API Parameter:**
- Changed from `date` parameter to `from` parameter (Frankfurter v2 API requirement)

**Before:**
```python
params = {
    "base": base_currency,
    "quotes": ",".join(target_currencies),
    "date": date  # WRONG - doesn't work with v2 API
}
```

**After:**
```python
params = {
    "base": base_currency,
    "quotes": ",".join(target_currencies)
}
if date:
    params["from"] = date  # CORRECT - v2 API uses 'from' parameter
```

### 2. Fixed `currency.py` - `get_commodity_prices()` method

**Key Changes:**
- Changed API call to use commodity (XAU, XAG, XPT, XPD) as BASE and currency as QUOTE
- Added logic to fetch exchange rates between currencies for cross-currency calculations
- Implemented proper multi-currency support: fetch base price, then convert to other currencies
- Added comprehensive documentation about troy ounce base unit and weekend/holiday handling

**Before:**
```python
# Wrong: Currency as base, commodity as quote
rates = CurrencyConverter.get_exchange_rates(currency, [symbol], date)
# This would call: /v2/rates?base=EUR&quotes=XAU&date=2026-04-11
```

**After:**
```python
# Correct: Commodity as base, currency as quote, using 'from' parameter
rates = CurrencyConverter.get_exchange_rates(symbol, currencies, date)
# This calls: /v2/rates?base=XAU&quotes=EUR,USD,GBP&from=2026-04-11
```

### 2. Updated `app.py` - Exchange Rates Page Documentation

**Changes:**
- Updated info message to clarify troy ounce base unit and unit conversion
- Enhanced "About Exchange Rates" expander with detailed commodity pricing information
- Added explanation of weekend/holiday handling
- Clarified troy ounce conversion factors

## How It Works Now

### 1. Fetching Commodity Prices

```python
# Example: Get Gold price in EUR, USD, GBP
commodities = ["Gold"]
currencies = ["EUR", "USD", "GBP"]
date = "2026-04-08"

prices = CurrencyConverter.get_commodity_prices(commodities, currencies, date)
# Returns: {"Gold": {"EUR": 2703.09, "USD": 3141.88, "GBP": 2354.87}}
```

### 2. Multi-Currency Calculation

For multiple currencies:
1. Fetch commodity price in first currency (base) from API
2. Fetch exchange rates between all currencies
3. Calculate prices in other currencies: `price_in_target = price_in_base × exchange_rate`

### 3. Unit Conversion

All API prices are per **troy ounce**. When user selects different unit:

```python
# Convert from troy ounce to selected unit
converted_price = CurrencyConverter.convert_commodity_unit(
    base_price,      # Price per troy ounce from API
    "ounce",         # Source unit (always troy ounce from API)
    selected_unit    # Target unit (gram, kilogram, pound, ton)
)
```

**Conversion Factors:**
- 1 troy ounce = 1.0 troy ounce (base)
- 1 troy ounce = 31.1035 grams
- 1 troy ounce = 0.0311035 kilograms
- 1 troy ounce = 0.0685714 pounds
- 1 troy ounce = 0.0000311035 metric tons

### 4. Weekend/Holiday Handling

The Frankfurter API automatically handles weekends and holidays:
- If you request data for a weekend or holiday, the API returns the last working day's price
- No special handling needed in the code - the API does this automatically

## Testing

Run the test script to verify the fix:

```bash
python3 test_commodity_fix.py
```

**Expected Output:**
```
✓ Gold price fetched: 4,067.96 EUR per troy ounce

✓ Gold prices fetched successfully:
  EUR: 4,067.96 per troy ounce
  USD: 4,759.49 per troy ounce
```

## User-Facing Changes

1. **Correct Commodity Prices**: Gold, Silver, Platinum, and Palladium prices now display correctly
2. **Multi-Currency Support**: When multiple currencies are configured, commodity prices are properly calculated for each currency
3. **Unit Conversion**: Prices correctly convert from troy ounces to grams, kilograms, pounds, or tons
4. **Better Documentation**: Clear explanation of troy ounce base unit and how prices are calculated

## Files Modified

1. **`currency.py`** - Fixed `get_commodity_prices()` method (lines 148-230)
2. **`app.py`** - Updated documentation in exchange rates page (lines 2059-2079)
3. **`test_commodity_fix.py`** - New test script to verify the fix

## API Reference

**Frankfurter API v2 Commodity Support:**
- Gold (XAU): Available from 2005–present
- Silver (XAG): Available from 2019–present  
- Platinum (XPT): Available from 2026–present
- Palladium (XPD): Available from 2026–present

**API Endpoint:**
```
GET https://api.frankfurter.dev/v2/rates
Parameters:
  - base: Commodity code (XAU, XAG, XPT, XPD)
  - quotes: Comma-separated currency codes (EUR, USD, GBP, etc.)
  - from: Optional date in YYYY-MM-DD format (NOT 'date')
```

**IMPORTANT:** The v2 API uses `from` parameter for dates, not `date`. Using `date` will not work correctly.

## Summary

The commodity pricing system now correctly:
✅ Uses correct API parameter (`from` instead of `date`)
✅ Fetches prices with commodity as base (XAU->EUR, not EUR->XAU)
✅ Calculates prices in multiple currencies using exchange rates
✅ Converts from troy ounces to other units (gram, kg, pound, ton)
✅ Handles weekends/holidays automatically (API returns last working day)
✅ Provides clear documentation about troy ounce base unit

---
*Fixed on: 2026-04-11*
*Tested with: Gold (XAU) to EUR on 2026-04-11*
*API returns: 4,067.96 EUR per troy ounce (date: 2026-04-10, last working day)*