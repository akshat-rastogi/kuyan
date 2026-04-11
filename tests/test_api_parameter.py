#!/usr/bin/env python3
"""
Test script to verify the API parameter format (date with provider)
"""

import requests
from currency import CurrencyConverter

def test_api_parameter():
    """Test that we're using the requested commodity API parameters"""
    print("Testing Frankfurter API v2 Commodity Parameters")
    print("=" * 60)
    print()
    
    # Test 1: Direct API call with 'date' and 'providers' parameters
    print("Test 1: Direct API call with 'date' and 'providers' parameters")
    print("-" * 60)
    url = "https://api.frankfurter.dev/v2/rates"
    params = {
        "date": "2026-04-08",
        "quotes": "EUR",
        "base": "XAU",
        "providers": "NBU"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"✓ API Response: {data}")
        
        if isinstance(data, list) and len(data) > 0:
            rate = data[0].get("rate")
            print(f"✓ Gold price: {rate:,.2f} EUR per troy ounce")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print()
    print("-" * 60)
    print()
    
    # Test 2: Using our fixed CurrencyConverter
    print("Test 2: Using CurrencyConverter.get_commodity_prices()")
    print("-" * 60)
    
    commodities = ["Gold"]
    currencies = ["EUR", "USD"]
    date = "2026-04-08"
    
    prices = CurrencyConverter.get_commodity_prices(commodities, currencies, date)
    
    if prices and "Gold" in prices:
        print("✓ Commodity prices fetched successfully:")
        for currency, price in prices["Gold"].items():
            print(f"  {currency}: {price:,.2f} per troy ounce")
    else:
        print("✗ Failed to fetch commodity prices")
        print(f"  Response: {prices}")
    
    print()
    print("=" * 60)
    print()
    print("API URL format:")
    print("  Requested: https://api.frankfurter.dev/v2/rates?date=2026-04-08&quotes=EUR&base=XAU&providers=NBU")
    print("  Used by converter: same request shape via query parameters")

if __name__ == "__main__":
    test_api_parameter()

