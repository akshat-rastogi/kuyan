"""
Test script to verify commodity price fetching works correctly
"""

from currency import CurrencyConverter

def test_commodity_prices():
    """Test fetching commodity prices"""
    print("Testing commodity price fetching...")
    print("-" * 50)
    
    # Test with common commodities and currencies
    commodities = ["Gold", "Silver", "Copper"]
    currencies = ["USD", "CAD", "EUR"]
    
    print(f"Fetching prices for: {commodities}")
    print(f"In currencies: {currencies}")
    print()
    
    prices = CurrencyConverter.get_commodity_prices(commodities, currencies)
    
    if prices:
        print("✓ Successfully fetched commodity prices!")
        print()
        
        for commodity, currency_prices in prices.items():
            print(f"{commodity}:")
            for currency, price in currency_prices.items():
                print(f"  {currency}: ${price:,.2f} per troy ounce")
            print()
    else:
        print("✗ Failed to fetch commodity prices")
        print("This might be expected if using fallback prices")
    
    print("-" * 50)
    
    # Test unit conversion
    print("\nTesting unit conversion...")
    test_price = 2000.0  # $2000 per troy ounce
    
    units = ["ounce", "gram", "kilogram", "pound"]
    print(f"Base price: ${test_price:,.2f} per troy ounce")
    print()
    
    for unit in units:
        converted = CurrencyConverter.convert_commodity_unit(test_price, "ounce", unit)
        print(f"  Per {unit}: ${converted:,.2f}")
    
    print("-" * 50)

if __name__ == "__main__":
    test_commodity_prices()

