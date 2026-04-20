"""
KUYAN - Currency Converter Module
Copyright (c) 2025 mycloudcondo inc.
Licensed under MIT License - see LICENSE file for details
"""

import requests
from typing import Dict, Optional, List


class CurrencyConverter:
    """Handles currency exchange rate fetching from frankfurter.app API"""

    BASE_URL = "https://api.frankfurter.dev"

    @staticmethod
    def get_exchange_rates(
        base_currency: str,
        target_currencies: list,
        date: Optional[str] = None,
        provider: Optional[str] = None
    ) -> Optional[Dict[str, float]]:
        """
        Fetch exchange rates from Frankfurter v2 API.

        Args:
            base_currency: Base currency or commodity code
            target_currencies: List of target currency codes
            date: Optional date in YYYY-MM-DD format. If None, uses latest rates.
            provider: Optional provider code such as "NBU"

        Returns:
            Dictionary with exchange rates or None if request fails
            Format: {"USD_CAD": 1.35, "USD_INR": 83.5, ...}
        """
        try:
            url = f"{CurrencyConverter.BASE_URL}/v2/rates"
            quotes = [c for c in target_currencies if c != base_currency]
            params = {
                "base": base_currency,
                "quotes": ",".join(quotes)
            }

            if date:
                params["date"] = date

            if provider:
                params["providers"] = provider

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            formatted_rates = {}
            if isinstance(data, list) and len(data) > 0:
                first_rate = data[0]
                first_date = first_rate.get("date")

                for rate_obj in data:
                    if rate_obj.get("date") == first_date:
                        quote = rate_obj.get("quote")
                        rate = rate_obj.get("rate")
                        if quote and rate is not None:
                            formatted_rates[f"{base_currency}_{quote}"] = rate
            elif isinstance(data, dict):
                rates = data.get("rates", {})
                for currency, rate in rates.items():
                    formatted_rates[f"{base_currency}_{currency}"] = rate

            formatted_rates[f"{base_currency}_{base_currency}"] = 1.0

            return formatted_rates

        except requests.exceptions.RequestException as e:
            print(f"Error fetching exchange rates: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    @staticmethod
    def get_all_cross_rates(currencies: Optional[List[str]] = None, date: Optional[str] = None) -> Optional[Dict[str, float]]:
        """
        Get all cross rates between provided currencies

        Args:
            currencies: List of currency codes. If None, uses default ["CAD", "USD", "INR"]
            date: Optional date in YYYY-MM-DD format

        Returns:
            Dictionary with all exchange rates between currencies
            Format: {"USD_CAD": 1.35, "CAD_USD": 0.74, "USD_INR": 83.5, ...}
        """
        # Use default currencies if none provided (for backward compatibility)
        if currencies is None:
            currencies = ["CAD", "USD", "INR"]

        all_rates = {}

        for base in currencies:
            rates = CurrencyConverter.get_exchange_rates(base, currencies, date)
            if rates:
                all_rates.update(rates)

        # If API fails, return fallback rates
        if not all_rates:
            print("Warning: Using fallback exchange rates")
            return CurrencyConverter._get_fallback_rates(currencies)
        
        return all_rates

    @staticmethod
    def convert(amount: float, from_currency: str, to_currency: str, rates: Dict[str, float]) -> float:
        """
        Convert amount from one currency to another using provided rates

        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            rates: Dictionary of exchange rates

        Returns:
            Converted amount
        """
        if from_currency == to_currency:
            return amount

        # Try direct conversion
        direct_key = f"{from_currency}_{to_currency}"
        if direct_key in rates:
            return amount * rates[direct_key]

        # Try inverse conversion
        inverse_key = f"{to_currency}_{from_currency}"
        if inverse_key in rates:
            return amount / rates[inverse_key]

        # Try conversion through USD as intermediary
        from_to_usd_key = f"{from_currency}_USD"
        usd_to_target_key = f"USD_{to_currency}"

        if from_to_usd_key in rates and usd_to_target_key in rates:
            usd_amount = amount * rates[from_to_usd_key]
            return usd_amount * rates[usd_to_target_key]

        return amount


    @staticmethod
    def get_commodity_prices(
        commodities: List[str],
        currencies: List[str],
        date: Optional[str] = None,
        provider: Optional[str] = "NBU"
    ) -> Optional[Dict[str, Dict[str, float]]]:
        """
        Fetch commodity prices in multiple currencies using Frankfurter API
        
        The API returns prices per troy ounce. When weekend/holiday is chosen,
        the API automatically returns the last working day's price.
        
        Args:
            commodities: List of commodity names (e.g., ["Gold", "Silver", "Platinum", "Palladium"])
            currencies: List of currency codes (e.g., ["USD", "EUR", "GBP"])
            date: Optional date in YYYY-MM-DD format. If None, uses latest prices.
                  If weekend/holiday, API returns last working day's price.
        
        Returns:
            Dictionary with commodity prices per troy ounce in each currency
            Format: {"Gold": {"USD": 2000.50, "EUR": 1850.25}, "Silver": {...}}
            Note: All prices are per troy ounce (base unit from API)
        """
        try:
            # Map commodity names to Frankfurter API symbols (ISO 4217 codes)
            commodity_map = {
                "Gold": "XAU",      # Available from 2005–present
                "Silver": "XAG",    # Available from 2019–present
                "Platinum": "XPT",  # Available from 2026–present
                "Palladium": "XPD"  # Available from 2026–present
            }
            
            # Filter to only supported commodities
            supported_commodities = [c for c in commodities if c in commodity_map]
            if not supported_commodities:
                return None
            
            results = {}
            
            # First, get exchange rates between all currencies for cross-currency calculation
            currency_rates = {}
            if len(currencies) > 1:
                # Get all cross rates between currencies
                for base_curr in currencies:
                    rates = CurrencyConverter.get_exchange_rates(base_curr, currencies, date, provider)
                    if rates:
                        currency_rates.update(rates)
            
            # Fetch commodity prices - use first currency as base, then convert to others
            base_currency = currencies[0] if currencies else "USD"
            
            for commodity in supported_commodities:
                symbol = commodity_map[commodity]
                results[commodity] = {}
                
                try:
                    # Fetch rate with commodity as BASE and currency as QUOTE
                    # API format: /v2/rates?date=YYYY-MM-DD&quotes=EUR&base=XAU&providers=NBU
                    # This returns a single-response list of quote objects for the requested date
                    # The rate represents: 1 troy ounce of XAU = quote currency amount
                    rates = CurrencyConverter.get_exchange_rates(symbol, currencies, date, provider)
                    
                    if rates:
                        # Extract price for base currency
                        base_key = f"{symbol}_{base_currency}"
                        if base_key in rates:
                            base_price = rates[base_key]
                            results[commodity][base_currency] = round(base_price, 2)
                            
                            # Calculate prices in other currencies using exchange rates
                            for currency in currencies:
                                if currency != base_currency:
                                    # Try direct rate from API first
                                    direct_key = f"{symbol}_{currency}"
                                    if direct_key in rates:
                                        results[commodity][currency] = round(rates[direct_key], 2)
                                    else:
                                        # Calculate using currency exchange rates
                                        # Price in target currency = Price in base currency * (base_currency to target_currency rate)
                                        rate_key = f"{base_currency}_{currency}"
                                        if rate_key in currency_rates:
                                            converted_price = base_price * currency_rates[rate_key]
                                            results[commodity][currency] = round(converted_price, 2)
                        else:
                            # If base currency not found, try to get any available price
                            for currency in currencies:
                                price_key = f"{symbol}_{currency}"
                                if price_key in rates:
                                    results[commodity][currency] = round(rates[price_key], 2)
                                    
                except Exception as e:
                    print(f"Error fetching {commodity} prices: {e}")
                    continue
            
            return results if results else None
            
        except Exception as e:
            print(f"Error fetching commodity prices: {e}")
            # Return fallback estimates
            return CurrencyConverter._get_commodity_prices_fallback(commodities, currencies, date)
    
    @staticmethod
    def _get_commodity_prices_fallback(commodities: List[str], currencies: List[str], date: Optional[str] = None) -> Optional[Dict[str, Dict[str, float]]]:
        """
        Fallback method with approximate commodity prices when API fails
        Uses approximate USD prices and converts to other currencies
        
        Args:
            commodities: List of commodity names
            currencies: List of currency codes
            date: Optional date in YYYY-MM-DD format for historical rates
        """
        try:
            # Approximate prices per troy ounce in USD (as of 2026)
            base_prices_usd = {
                "Gold": 2050.00,
                "Silver": 24.50,
                "Platinum": 950.00,
                "Palladium": 1000.00
            }
            
            # Get currency exchange rates from USD
            exchange_rates = CurrencyConverter.get_exchange_rates("USD", currencies, date)
            if not exchange_rates:
                return None
            
            results = {}
            for commodity in commodities:
                if commodity in base_prices_usd:
                    results[commodity] = {}
                    base_price = base_prices_usd[commodity]
                    
                    for currency in currencies:
                        rate_key = f"USD_{currency}"
                        if rate_key in exchange_rates:
                            price_in_currency = base_price * exchange_rates[rate_key]
                            results[commodity][currency] = round(price_in_currency, 2)
                        elif currency == "USD":
                            results[commodity]["USD"] = base_price
            
            return results if results else None
            
        except Exception as e:
            print(f"Error in fallback commodity prices: {e}")
            return None
    
    @staticmethod
    def convert_commodity_unit(price_per_ounce: float, from_unit: str, to_unit: str) -> float:
        """
        Convert commodity price from one unit to another
        
        Args:
            price_per_ounce: Price per troy ounce (base unit)
            from_unit: Source unit (should be 'ounce' for base prices)
            to_unit: Target unit to convert to
        
        Returns:
            Converted price in the target unit
        
        Example:
            If gold is $2000 per troy ounce and 1 troy ounce = 31.1035 grams,
            then price per gram = $2000 / 31.1035 = $64.30 per gram
        """
        # Conversion factors: how many of each unit equals 1 troy ounce
        units_per_ounce = {
            "ounce": 1.0,           # Troy ounce (base unit)
            "gram": 31.1035,        # 1 troy ounce = 31.1035 grams
            "kilogram": 0.0311035,  # 1 troy ounce = 0.0311035 kg
            "pound": 0.0685714,     # 1 troy ounce = 0.0685714 pounds
            "ton": 0.0000311035,    # 1 troy ounce = 0.0000311035 metric tons
        }
        
        if from_unit not in units_per_ounce or to_unit not in units_per_ounce:
            return price_per_ounce
        
        # If converting from ounce to another unit:
        # Price per target unit = Price per ounce / (number of target units per ounce)
        # Example: $2000 per ounce / 31.1035 grams per ounce = $64.30 per gram
        if from_unit == "ounce":
            price_per_target_unit = price_per_ounce / units_per_ounce[to_unit]
        else:
            # If converting from another unit to ounce (reverse conversion):
            # Price per ounce = Price per unit * (number of units per ounce)
            price_per_target_unit = price_per_ounce * units_per_ounce[from_unit] / units_per_ounce[to_unit]
        
        return price_per_target_unit
    
    @staticmethod
    def _get_fallback_rates(currencies: List[str]) -> Dict[str, float]:
        """
        Provide fallback exchange rates when API is unavailable
        Uses approximate rates as of 2025
        """
        # Base rates relative to USD
        base_rates_to_usd = {
            "USD": 1.0,
            "CAD": 1.35,    # 1 USD = 1.35 CAD
            "EUR": 0.92,    # 1 USD = 0.92 EUR
            "GBP": 0.79,    # 1 USD = 0.79 GBP
            "INR": 83.0,    # 1 USD = 83 INR
            "JPY": 148.0,   # 1 USD = 148 JPY
            "AUD": 1.52,    # 1 USD = 1.52 AUD
            "CHF": 0.88,    # 1 USD = 0.88 CHF
            "CNY": 7.24,    # 1 USD = 7.24 CNY
            "MXN": 17.0,    # 1 USD = 17 MXN
        }
        
        fallback_rates = {}
        
        # Generate all cross rates
        for from_curr in currencies:
            for to_curr in currencies:
                if from_curr == to_curr:
                    fallback_rates[f"{from_curr}_{to_curr}"] = 1.0
                elif from_curr in base_rates_to_usd and to_curr in base_rates_to_usd:
                    # Convert through USD
                    # from_curr -> USD -> to_curr
                    from_to_usd = 1.0 / base_rates_to_usd[from_curr]
                    usd_to_target = base_rates_to_usd[to_curr]
                    rate = from_to_usd * usd_to_target
                    fallback_rates[f"{from_curr}_{to_curr}"] = round(rate, 6)
        
        return fallback_rates
