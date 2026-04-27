"""
Test the exact scenario from the bug report:
Gold account with unit=gram should calculate value correctly
"""
from currencyConverter import CurrencyConverter

print("=" * 70)
print("Testing Gold Calculation Bug Fix - Gram Unit Scenario")
print("=" * 70)

# Simulate the scenario: User has 100 grams of gold
quantity_grams = 100.0
gold_price_per_ounce_usd = 2000.0  # Example: $2000 per troy ounce

print(f"\nScenario:")
print(f"  - User has: {quantity_grams} grams of gold")
print(f"  - Gold price: ${gold_price_per_ounce_usd:,.2f} per troy ounce (from API)")
print(f"  - Unit configured in account: gram")

# Step 1: Convert price from per-ounce to per-gram
price_per_gram = CurrencyConverter.convert_commodity_unit(
    gold_price_per_ounce_usd,
    "ounce",  # API returns per troy ounce
    "gram"    # User's configured unit
)

print(f"\nStep 1: Convert price to per-gram")
print(f"  Price per gram = ${gold_price_per_ounce_usd:,.2f} / 31.1035 grams")
print(f"  Price per gram = ${price_per_gram:.2f}")

# Step 2: Calculate total value
total_value = quantity_grams * price_per_gram

print(f"\nStep 2: Calculate total value")
print(f"  Total value = {quantity_grams} grams × ${price_per_gram:.2f}/gram")
print(f"  Total value = ${total_value:,.2f}")

# Verification
expected_value = (quantity_grams / 31.1035) * gold_price_per_ounce_usd
print(f"\nVerification:")
print(f"  Expected: ({quantity_grams} grams / 31.1035) × ${gold_price_per_ounce_usd:,.2f}")
print(f"  Expected: ${expected_value:,.2f}")
print(f"  Actual:   ${total_value:,.2f}")
print(f"  Match: {'✓ YES' if abs(total_value - expected_value) < 0.01 else '✗ NO'}")

print("\n" + "=" * 70)
print("BEFORE THE FIX:")
print("  The bug was dividing by the conversion factor incorrectly,")
print("  which would have resulted in the WRONG calculation.")
print("\nAFTER THE FIX:")
print("  The conversion now correctly divides price by units per ounce,")
print("  giving the correct price per gram and total value.")
print("=" * 70)

