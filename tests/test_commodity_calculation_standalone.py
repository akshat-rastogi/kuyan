"""
Standalone test for commodity calculation logic
"""

def convert_commodity_unit(price_per_ounce: float, from_unit: str, to_unit: str) -> float:
    """
    Convert commodity price from one unit to another
    """
    units_per_ounce = {
        "ounce": 1.0,
        "gram": 31.1035,
        "kilogram": 0.0311035,
        "pound": 0.0685714,
        "ton": 0.0000311035,
    }
    
    if from_unit not in units_per_ounce or to_unit not in units_per_ounce:
        return price_per_ounce
    
    if from_unit == "ounce":
        price_per_target_unit = price_per_ounce / units_per_ounce[to_unit]
    else:
        price_per_target_unit = price_per_ounce * units_per_ounce[from_unit] / units_per_ounce[to_unit]
    
    return price_per_target_unit


def get_commodity_value(quantity, commodity_name, target_currency, commodity_prices, commodity_configs):
    """Calculate commodity value in target currency"""
    if not commodity_name or commodity_name not in commodity_prices:
        return 0.0
    
    price_per_ounce = commodity_prices[commodity_name].get(target_currency, 0)
    
    if price_per_ounce == 0:
        return 0.0
    
    commodity_unit = "ounce"
    if commodity_name in commodity_configs:
        commodity_unit = commodity_configs[commodity_name].get('unit', 'ounce')
    
    price_per_unit = convert_commodity_unit(
        price_per_ounce,
        "ounce",
        commodity_unit
    )
    
    return quantity * price_per_unit


# Test data
commodity_prices = {
    "Gold": {
        "EUR": 3987.93,
        "USD": 4200.00
    }
}

commodity_configs = {
    "Gold": {
        "name": "Gold",
        "unit": "gram",
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
print("Test 1: Commodity Value Calculation (GRAM unit)")
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
        "unit": "ounce",
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
print("SUMMARY")
print("=" * 70)
print("The new get_commodity_value() function correctly:")
print("1. Takes the price per troy ounce from the API")
print("2. Converts it to price per configured unit (gram, ounce, kg, etc.)")
print("3. Multiplies by the quantity to get total value")
print("=" * 70)

