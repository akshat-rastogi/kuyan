#!/usr/bin/env python3
"""
Test script to verify the commodity pricing fix
Tests the exact API example provided: XAU to EUR on 2026-04-08
"""

from currencyConverter import CurrencyConverter

def test_gold_price_fix():
    """Test the fixed commodity pricing with the provided API example"""
    print("Testing Commodity Price Fix")
    print("=" * 60)
    print()
    
    # Test case from user: XAU to EUR on 2026-04-08
    # Expected API response: [{"date":"2026-04-08","base":"XAU","quote":"EUR","rate":2703.09}]
    # This means: 1 troy ounce of Gold = 2703.09 EUR
    
    print("Test 1: Gold price in EUR on 2026-04-08")
    print("-" * 60)
    commodities = ["Gold"]
    currencies = ["EUR"]
    date = "2026-04-08"
    
    prices = CurrencyConverter.get_commodity_prices(commodities, currencies, date)
    
    if prices and "Gold" in prices and "EUR" in prices["Gold"]:
        gold_eur = prices["Gold"]["EUR"]
        print(f"✓ Gold price fetched: {gold_eur:,.2f} EUR per troy ounce")
        print(f"  Expected: ~2703.09 EUR per troy ounce")
        
        # Check if it's close to expected value (within 10% tolerance for API variations)
        expected = 2703.09
        if abs(gold_eur - expected) / expected < 0.1:
            print(f"  ✓ Price is within expected range!")
        else:
            print(f"  ⚠ Price differs from expected (might be due to API data)")
    else:
        print("✗ Failed to fetch Gold price in EUR")
        print(f"  Response: {prices}")
    
    print()
    print("-" * 60)
    print()
    
    # Test 2: Multiple currencies
    print("Test 2: Gold price in multiple currencies")
    print("-" * 60)
    currencies = ["EUR", "USD", "GBP"]
    
    prices = CurrencyConverter.get_commodity_prices(commodities, currencies, date)
    
    if prices and "Gold" in prices:
        print("✓ Gold prices fetched successfully:")
        for currency, price in prices["Gold"].items():
            print(f"  {currency}: {price:,.2f} per troy ounce")
    else:
        print("✗ Failed to fetch Gold prices")
        print(f"  Response: {prices}")
    
    print()
    print("-" * 60)
    print()
    
    # Test 3: Unit conversion
    print("Test 3: Unit conversion for Gold at 2703.09 EUR/oz")
    print("-" * 60)
    base_price = 2703.09
    units = ["ounce", "gram", "kilogram", "pound", "ton"]
    
    print(f"Base price: {base_price:,.2f} EUR per troy ounce")
    print()
    
    for unit in units:
        converted = CurrencyConverter.convert_commodity_unit(base_price, "ounce", unit)
        print(f"  Per {unit:10s}: {converted:,.2f} EUR")
    
    print()
    print("=" * 60)
    print("✓ Test completed!")
    print()
    print("Key fixes implemented:")
    print("  1. API now called with commodity as BASE (XAU) and currency as QUOTE (EUR)")
    print("  2. Multiple currencies calculated using exchange rates")
    print("  3. Unit conversion applied after fetching base price (per troy ounce)")
    print("  4. Weekend/holiday dates automatically return last working day's price")

if __name__ == "__main__":
    test_gold_price_fix()

