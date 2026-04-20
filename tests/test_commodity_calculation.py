"""
Test commodity calculation with different units
"""
from helper import get_commodity_value

# Test data
commodity_prices = {
    "Gold": {
        "EUR": 3987.93,  # Price per troy ounce in EUR
        "USD": 4200.00   # Price per troy ounce in USD
    }
}

commodity_configs = {
    "Gold": {
        "name": "Gold",
        "unit": "gram",  # User configured unit
        "symbol": "🥇",
        "color": "#FFD700"
    }
}

# Test 1: 219 grams of gold in EUR
quantity = 219.0
result_eur = get_commodity_value(
    quantity=quantity,
    commodity_name="Gold",
    target_currency="EUR",
    commodity_prices=commodity_prices,
    commodity_configs=commodity_configs
)

print("=" * 70)
print("Test: Commodity Value Calculation")
print("=" * 70)
print(f"\nCommodity: Gold")
print(f"Quantity: {quantity} grams")
print(f"Price per troy ounce (from API): €{commodity_prices['Gold']['EUR']:,.2f}")
print(f"Configured unit: {commodity_configs['Gold']['unit']}")
print(f"\nCalculation:")
print(f"  1 troy ounce = 31.1035 grams")
print(f"  Price per gram = €{commodity_prices['Gold']['EUR']:,.2f} / 31.1035")
print(f"  Price per gram = €{commodity_prices['Gold']['EUR'] / 31.1035:.2f}")
print(f"  Total value = {quantity} grams × €{commodity_prices['Gold']['EUR'] / 31.1035:.2f}/gram")
print(f"  Total value = €{result_eur:,.2f}")

expected = (quantity / 31.1035) * commodity_prices['Gold']['EUR']
print(f"\nExpected: €{expected:,.2f}")
print(f"Actual:   €{result_eur:,.2f}")
print(f"Match: {'✓ YES' if abs(result_eur - expected) < 0.01 else '✗ NO - BUG!'}")

# Test 2: Same quantity but with ounce unit
commodity_configs_ounce = {
    "Gold": {
        "name": "Gold",
        "unit": "ounce",  # Different unit
        "symbol": "🥇",
        "color": "#FFD700"
    }
}

result_ounce = get_commodity_value(
    quantity=quantity,
    commodity_name="Gold",
    target_currency="EUR",
    commodity_prices=commodity_prices,
    commodity_configs=commodity_configs_ounce
)

print(f"\n" + "=" * 70)
print("Test 2: Same quantity but unit is 'ounce'")
print("=" * 70)
print(f"Quantity: {quantity} ounces (troy)")
print(f"Price per troy ounce: €{commodity_prices['Gold']['EUR']:,.2f}")
print(f"Total value = {quantity} ounces × €{commodity_prices['Gold']['EUR']:,.2f}/ounce")
print(f"Total value = €{result_ounce:,.2f}")

expected_ounce = quantity * commodity_prices['Gold']['EUR']
print(f"\nExpected: €{expected_ounce:,.2f}")
print(f"Actual:   €{result_ounce:,.2f}")
print(f"Match: {'✓ YES' if abs(result_ounce - expected_ounce) < 0.01 else '✗ NO - BUG!'}")

print("\n" + "=" * 70)

# Made with Bob
