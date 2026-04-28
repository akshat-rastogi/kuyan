# Property Assets & Liabilities Feature

## Overview

The Property Assets & Liabilities feature provides comprehensive tracking of real estate properties, their market values, and associated mortgages. This feature helps you understand your property equity and overall real estate portfolio health.

## Key Features

### 1. Property Management
- **Track Multiple Properties**: Manage residential, commercial, land, investment, vacation, and other property types
- **Property Details**: Store property name, type, address, owner, and currency
- **Property Valuations**: Track property market values over time with different valuation types

### 2. Asset Tracking
- **Market Valuations**: Record property values with dates and valuation types
- **Valuation Types**: 
  - Purchase Price
  - Market Appraisal
  - Tax Assessment
  - Online Estimate
  - Professional Valuation
  - Other
- **Historical Tracking**: Maintain history of property valuations over time

### 3. Liability Management
- **Mortgage Linking**: Link one or more mortgages to each property
- **Automatic Calculations**: System automatically calculates current mortgage balances
- **Multi-Currency Support**: Properties and mortgages can be in different currencies

### 4. Equity Calculations
- **Property Equity**: Automatically calculated as Market Value - Total Debt
- **Equity Percentage**: Shows equity as percentage of market value
- **Portfolio Overview**: View total assets, liabilities, and equity across all properties

## Database Schema

### Properties Table
```sql
CREATE TABLE properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_name TEXT NOT NULL UNIQUE,
    property_type TEXT NOT NULL,
    address TEXT,
    owner TEXT NOT NULL,
    currency TEXT NOT NULL DEFAULT 'EUR',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Property Assets Table
```sql
CREATE TABLE property_assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL,
    valuation_date DATE NOT NULL,
    market_value DECIMAL(15,2) NOT NULL,
    valuation_type TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
)
```

### Property Liabilities Table
```sql
CREATE TABLE property_liabilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL,
    mortgage_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE,
    FOREIGN KEY (mortgage_id) REFERENCES mortgage_settings(id) ON DELETE CASCADE,
    UNIQUE(property_id, mortgage_id)
)
```

## How to Use

### Adding a Property

1. Go to **Settings** → **Properties** tab
2. Click **"➕ Add New Property"**
3. Fill in property details:
   - Property Name (e.g., "Primary Residence", "Rental Property 1")
   - Property Type (Residential, Commercial, etc.)
   - Address
   - Owner
   - Currency

### Adding Property Valuation

1. In the property settings, enter:
   - Valuation Date
   - Market Value
   - Valuation Type
2. Optionally add notes about the valuation
3. Click **"💾 Save"**

### Linking Mortgages to Properties

1. First, ensure mortgages are configured in **Settings** → **Mortgage** tab
2. In the property settings, use the **"Link Mortgages to This Property"** multiselect
3. Select one or more mortgages associated with the property
4. Click **"💾 Save"**

### Viewing Property Equity

#### Dashboard View
The dashboard displays:
- **Total Property Assets**: Sum of all property market values
- **Total Property Liabilities**: Sum of all mortgage balances
- **Total Equity**: Assets minus Liabilities

Click the **"📋 Property Details"** expander to see:
- Individual property details
- Market value and valuation date
- Total debt and number of mortgages
- Equity amount and percentage
- List of linked mortgages with current balances

## API Methods

### Property Operations

```python
# Get all properties
properties = db.get_all_properties()

# Get property by ID
property = db.get_property_by_id(property_id)

# Get property by name
property = db.get_property_by_name("Primary Residence")

# Add property
property_id = db.add_property(
    property_name="My Home",
    property_type="Residential",
    address="123 Main St",
    owner="Me",
    currency="EUR"
)

# Update property
db.update_property(
    property_id=1,
    property_name="Updated Name",
    property_type="Residential",
    address="123 Main St",
    owner="Me",
    currency="EUR"
)

# Delete property
db.delete_property(property_id)
```

### Property Asset Operations

```python
from datetime import date

# Get property assets
assets = db.get_property_assets(property_id)

# Get latest asset valuation
latest = db.get_latest_property_asset(property_id)

# Add property asset
asset_id = db.add_property_asset(
    property_id=1,
    valuation_date=date.today(),
    market_value=500000.0,
    valuation_type="Market Appraisal",
    notes="Professional appraisal"
)

# Update property asset
db.update_property_asset(
    asset_id=1,
    valuation_date=date.today(),
    market_value=520000.0,
    valuation_type="Market Appraisal",
    notes="Updated valuation"
)

# Delete property asset
db.delete_property_asset(asset_id)
```

### Property Liability Operations

```python
# Link mortgage to property
db.link_mortgage_to_property(property_id=1, mortgage_id=1)

# Unlink mortgage from property
db.unlink_mortgage_from_property(property_id=1, mortgage_id=1)

# Get property mortgages
mortgages = db.get_property_mortgages(property_id)

# Get mortgage property
property = db.get_mortgage_property(mortgage_id)

# Get all properties with financials
properties = db.get_all_properties_with_financials()
```

### Helper Functions

```python
# Get property equity data
equity_data = get_property_equity_data(db)

# Calculate total property assets
total_assets = calculate_total_property_assets(db, base_currency, rates)

# Calculate total property liabilities
total_liabilities = calculate_total_property_liabilities(db, base_currency, rates)
```

## Benefits

1. **Complete Picture**: See your real estate portfolio alongside other assets
2. **Equity Tracking**: Monitor how much equity you have in each property
3. **Mortgage Management**: Keep mortgages organized by property
4. **Historical Data**: Track property values over time
5. **Multi-Property Support**: Manage multiple properties with different mortgages
6. **Currency Flexibility**: Handle properties and mortgages in different currencies

## Example Use Cases

### Single Property with One Mortgage
- Primary residence
- One mortgage from a bank
- Track equity growth over time

### Investment Property Portfolio
- Multiple rental properties
- Each with its own mortgage
- Track total portfolio equity

### Mixed Portfolio
- Primary residence with mortgage
- Vacation home paid off (no mortgage)
- Investment property with multiple mortgages (first and second mortgage)

## Notes

- Properties can exist without mortgages (fully paid off)
- Mortgages can exist without being linked to properties (for backward compatibility)
- Property valuations are optional but recommended for equity calculations
- The system uses the most recent valuation for each property
- Mortgage balances are calculated automatically based on amortization schedules
- All existing mortgage functionality remains unchanged

## Migration

The feature is designed to be backward compatible:
- Existing mortgages continue to work without being linked to properties
- The dashboard shows both linked and unlinked mortgages
- No data migration is required
- Users can gradually link mortgages to properties as needed