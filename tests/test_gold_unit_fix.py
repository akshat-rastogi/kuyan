"""
Test script to verify gold unit conversion fix
"""
from currencyConverter import CurrencyConverter

# Test case: Gold price per troy ounce
gold_price_per_ounce = 2000.0  # $2000 per troy ounce

print("=" * 60)
print("Testing Gold Unit Conversion Fix")
print("=" * 60)
print(f"\nBase price: ${gold_price_per_ounce:,.2f} per troy ounce")
print("\nConversion Results:")
print("-" * 60)

# Test conversions from ounce to various units
units = ["ounce", "gram", "kilogram", "pound", "ton"]

for unit in units:
    converted_price = CurrencyConverter.convert_commodity_unit(
        gold_price_per_ounce, 
        "ounce", 
        unit
    )
    print(f"Price per {unit:10s}: ${converted_price:,.2f}")

print("\n" + "=" * 60)
print("Expected Results (for verification):")
print("-" * 60)
print("Price per ounce     : $2,000.00  (1:1 ratio)")
print("Price per gram      : $64.30     (2000 / 31.1035)")
print("Price per kilogram  : $64,301.49 (2000 / 0.0311035)")
print("Price per pound     : $29,166.67 (2000 / 0.0685714)")
print("Price per ton       : $64,301,493.65 (2000 / 0.0000311035)")
print("=" * 60)

# Test with actual quantity calculation
print("\n" + "=" * 60)
print("Example: 10 grams of gold at $2000/oz")
print("-" * 60)
quantity_grams = 10.0
price_per_gram = CurrencyConverter.convert_commodity_unit(gold_price_per_ounce, "ounce", "gram")
total_value = quantity_grams * price_per_gram
print(f"Quantity: {quantity_grams} grams")
print(f"Price per gram: ${price_per_gram:.2f}")
print(f"Total value: ${total_value:.2f}")
print(f"Expected: ~$643.01 (10 * 64.30)")
print("=" * 60)

