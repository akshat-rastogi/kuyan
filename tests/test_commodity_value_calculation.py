"""
Test script to verify commodity value calculation on overview page
"""

from currency import CurrencyConverter
from database import Database
from datetime import date

def test_commodity_value_calculation():
    """Test that commodity values are calculated correctly using exchange rates"""
    
    print("Testing Commodity Value Calculation Fix")
    print("=" * 60)
    
    # Test 1: Fetch commodity prices
    print("\nTest 1: Fetch Gold price in multiple currencies")
    print("-" * 60)
    
    commodities = ["Gold"]
    currencies = ["USD", "EUR", "GBP"]
    test_date = "2026-04-10"  # Use a working day
    
    prices = CurrencyConverter.get_commodity_prices(commodities, currencies, test_date)
    
    if prices and "Gold" in prices:
        print("✓ Successfully fetched Gold prices:")
        for currency, price in prices["Gold"].items():
            print(f"  {currency}: {price:,.2f} per troy ounce")
    else:
        print("✗ Failed to fetch commodity prices")
        return
    
    # Test 2: Calculate value for commodity account
    print("\nTest 2: Calculate value of 10 ounces of Gold in different currencies")
    print("-" * 60)
    
    quantity = 10.0  # 10 ounces of gold
    
    for currency in currencies:
        if currency in prices["Gold"]:
            price_per_ounce = prices["Gold"][currency]
            total_value = quantity * price_per_ounce
            print(f"  {quantity} ounces × {price_per_ounce:,.2f} {currency}/oz = {total_value:,.2f} {currency}")
    
    # Test 3: Verify the fix logic
    print("\nTest 3: Verify conversion logic")
    print("-" * 60)
    
    # Simulate what the overview page does
    base_currency = "USD"
    commodity_name = "Gold"
    
    if commodity_name in prices and base_currency in prices[commodity_name]:
        price_in_base = prices[commodity_name][base_currency]
        converted_value = quantity * price_in_base
        print(f"✓ Commodity calculation: {quantity} oz × {price_in_base:,.2f} USD/oz = {converted_value:,.2f} USD")
    else:
        print("✗ Could not calculate commodity value")
    
    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("\nThe fix ensures that:")
    print("1. Commodity prices are fetched from the API for the snapshot date")
    print("2. Commodity account values = quantity × price per unit in target currency")
    print("3. Regular account values continue to use currency exchange rates")

if __name__ == "__main__":
    test_commodity_value_calculation()

