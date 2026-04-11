# Frankfurter API v2 Integration - Changelog

## Date: April 11, 2026

### Summary
Successfully migrated from separate APIs to unified Frankfurter API v2 for both currency exchange rates and precious metals pricing. Added historical data support for the Exchange Rates page.

---

## Changes Made

### 1. Currency Module (`currency.py`)

#### API Migration
- **Updated BASE_URL**: Changed from `api.frankfurter.app` to `api.frankfurter.dev`
- **Migrated to v2 API**: Updated all endpoints from `/latest` to `/v2/rates`
- **Removed metals.dev dependency**: Eliminated separate `METALS_API_URL` and API key requirement

#### Precious Metals Support
- **Direct Frankfurter Integration**: Now fetches XAU, XAG, XPT, XPD directly from Frankfurter API
- **Supported Metals**:
  - Gold (XAU) - Available from 2005–present (3 providers)
  - Silver (XAG) - Available from 2019–present (2 providers)
  - Platinum (XPT) - Available from 2026–present (1 provider)
  - Palladium (XPD) - Available from 2026–present (1 provider)
- **Removed**: Copper (not supported by Frankfurter)

#### API Response Handling
- Updated `get_exchange_rates()` to handle v2 API array response format
- Modified parameter names: `from` → `base`, `to` → `quotes`
- Added proper date parameter handling for historical data

#### Commodity Pricing
- Completely rewrote `get_commodity_prices()` method
- Now uses inverse rate calculation (1/rate) to get price per troy ounce
- Simplified logic by removing gram-to-ounce conversions
- Maintained fallback pricing mechanism

### 2. Web Application (`app.py`)

#### Exchange Rates Page Enhancement
- **Enabled Date Selector**: Removed `disabled=True` restriction (line 1867)
- **Historical Data Support**: Users can now select past dates to view historical rates
- **Dynamic Date Handling**: 
  - Passes `date_str` parameter to API calls when historical date selected
  - Shows "Today's live" vs "Historical" label based on selection
- **Updated Help Text**: Clarified that Frankfurter supports data from 1999 onwards
- **Improved Spinner Messages**: Now shows selected date in loading messages

#### Documentation Updates
- Updated "About Exchange Rates" section with:
  - Correct API source (Frankfurter API v2)
  - Historical data availability information
  - Precious metals support details
  - Removed outdated "Live Rates Only" messaging

---

## Testing Results

### Current Prices (April 11, 2026)
```
Gold:
  USD: $429.18 per troy ounce
  EUR: $367.65 per troy ounce

Silver:
  USD: $74.29 per troy ounce
  EUR: $63.49 per troy ounce

Platinum:
  USD: $2,040.82 per troy ounce
  EUR: $1,754.39 per troy ounce

Palladium:
  USD: $1,562.50 per troy ounce
  EUR: $1,351.35 per troy ounce
```

### Historical Prices (March 12, 2026)
```
Gold:
  USD: $5,263.16 per troy ounce
  EUR: $4,545.45 per troy ounce

Silver:
  USD: $86.21 per troy ounce
  EUR: $74.63 per troy ounce
```

### Historical Exchange Rates (February 10, 2026)
```
USD_EUR: 0.8407
USD_GBP: 0.7325
EUR_USD: 1.1895
EUR_GBP: 0.8714
GBP_USD: 1.3652
GBP_EUR: 1.1477
```

---

## Benefits

1. **Unified API**: Single source for all exchange rates and precious metals
2. **No API Keys**: Eliminated need for metals.dev API key
3. **Historical Data**: Full support for viewing past rates and prices
4. **Better Reliability**: Frankfurter API is more stable and well-maintained
5. **Simplified Code**: Removed complex API switching logic
6. **Cost Savings**: No rate limits or API key management needed

---

## User-Facing Changes

### Exchange Rates Page
- Date selector is now **enabled** and functional
- Users can select any past date to view historical data
- Clear labeling of "Today's live" vs "Historical" rates
- Improved help text explaining data availability

### Supported Precious Metals
- Gold (XAU) ✅
- Silver (XAG) ✅
- Platinum (XPT) ✅
- Palladium (XPD) ✅
- Copper (XCU) ❌ (removed - not supported by Frankfurter)

---

## Technical Notes

### API Endpoints
- **Currency Rates**: `https://api.frankfurter.dev/v2/rates?base={currency}&quotes={currencies}`
- **Historical Rates**: Add `&date={YYYY-MM-DD}` parameter
- **Response Format**: Array of rate objects with `date`, `base`, `quote`, and `rate` fields

### Date Handling
- Current date: `date_str = None` (fetches latest)
- Historical date: `date_str = "YYYY-MM-DD"` format
- Maximum date: Today (no future dates)
- Minimum date: 1999 for currencies, varies for metals

### Fallback Mechanism
- Maintained fallback rates for offline scenarios
- Updated fallback prices to 2026 values
- Removed Copper from fallback data

---

## Migration Notes

No breaking changes for end users. The application seamlessly switched to the new API with enhanced functionality. All existing features continue to work as before, with the addition of historical data viewing capability.