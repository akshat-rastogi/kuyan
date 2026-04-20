#!/usr/bin/env python3
"""Test script for commodity unit conversion"""

from currencyConverter import CurrencyConverter

# Test unit conversion
print("Testing Commodity Unit Conversion")
print("=" * 50)

# Test price: $2000 per troy ounce (typical gold price)
base_price = 2000.0

units = ["ounce", "gram", "kilogram", "pound", "ton"]

print(f"\nBase price: ${base_price:,.2f} per troy ounce\n")

for unit in units:
    converted_price = CurrencyConverter.convert_commodity_unit(base_price, "ounce", unit)
    print(f"Price per {unit:10s}: ${converted_price:,.2f}")

print("\n" + "=" * 50)
print("✓ Unit conversion test completed successfully!")

