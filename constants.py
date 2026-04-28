"""
KUYAN - Monthly Net Worth Tracker
Currency Constants Module
Licensed under MIT License - see LICENSE file for details
"""

# Currency metadata (Frankfurter API supported currencies with flags)
AVAILABLE_CURRENCIES = {
    "AUD": {"name": "Australian Dollar", "flag": "🇦🇺", "symbol": "A$"},
    "BGN": {"name": "Bulgarian Lev", "flag": "🇧🇬", "symbol": "лв"},
    "BRL": {"name": "Brazilian Real", "flag": "🇧🇷", "symbol": "R$"},
    "CAD": {"name": "Canadian Dollar", "flag": "🇨🇦", "symbol": "C$"},
    "CHF": {"name": "Swiss Franc", "flag": "🇨🇭", "symbol": "CHF"},
    "CNY": {"name": "Chinese Yuan", "flag": "🇨🇳", "symbol": "¥"},
    "CZK": {"name": "Czech Koruna", "flag": "🇨🇿", "symbol": "Kč"},
    "DKK": {"name": "Danish Krone", "flag": "🇩🇰", "symbol": "kr"},
    "EUR": {"name": "Euro", "flag": "🇪🇺", "symbol": "€"},
    "GBP": {"name": "British Pound", "flag": "🇬🇧", "symbol": "£"},
    "HKD": {"name": "Hong Kong Dollar", "flag": "🇭🇰", "symbol": "HK$"},
    "HUF": {"name": "Hungarian Forint", "flag": "🇭🇺", "symbol": "Ft"},
    "IDR": {"name": "Indonesian Rupiah", "flag": "🇮🇩", "symbol": "Rp"},
    "ILS": {"name": "Israeli Shekel", "flag": "🇮🇱", "symbol": "₪"},
    "INR": {"name": "Indian Rupee", "flag": "🇮🇳", "symbol": "₹"},
    "ISK": {"name": "Icelandic Króna", "flag": "🇮🇸", "symbol": "kr"},
    "JPY": {"name": "Japanese Yen", "flag": "🇯🇵", "symbol": "¥"},
    "KRW": {"name": "South Korean Won", "flag": "🇰🇷", "symbol": "₩"},
    "MXN": {"name": "Mexican Peso", "flag": "🇲🇽", "symbol": "$"},
    "MYR": {"name": "Malaysian Ringgit", "flag": "🇲🇾", "symbol": "RM"},
    "NOK": {"name": "Norwegian Krone", "flag": "🇳🇴", "symbol": "kr"},
    "NZD": {"name": "New Zealand Dollar", "flag": "🇳🇿", "symbol": "NZ$"},
    "PHP": {"name": "Philippine Peso", "flag": "🇵🇭", "symbol": "₱"},
    "PLN": {"name": "Polish Złoty", "flag": "🇵🇱", "symbol": "zł"},
    "RON": {"name": "Romanian Leu", "flag": "🇷🇴", "symbol": "lei"},
    "RUB": {"name": "Russian Ruble", "flag": "🇷🇺", "symbol": "₽"},
    "SEK": {"name": "Swedish Krona", "flag": "🇸🇪", "symbol": "kr"},
    "SGD": {"name": "Singapore Dollar", "flag": "🇸🇬", "symbol": "S$"},
    "THB": {"name": "Thai Baht", "flag": "🇹🇭", "symbol": "฿"},
    "TRY": {"name": "Turkish Lira", "flag": "🇹🇷", "symbol": "₺"},
    "USD": {"name": "US Dollar", "flag": "🇺🇸", "symbol": "$"},
    "ZAR": {"name": "South African Rand", "flag": "🇿🇦", "symbol": "R"},
}

# Theme-friendly colors (work well in both light and dark mode)
COLOR_OPTIONS = {
    "Crimson Red": "#DC143C",
    "Navy Blue": "#003366",
    "Dark Orange": "#FF8C00",
    "Forest Green": "#228B22",
    "Purple": "#8B008B",
    "Teal": "#008080",
    "Maroon": "#800000",
    "Olive": "#808000",
    "Steel Blue": "#4682B4",
}

# Commodity metadata - Only Gold and Silver are supported
AVAILABLE_COMMODITIES = {
    "Gold": {"symbol": "🥇", "description": "Precious metal - Gold"},
    "Silver": {"symbol": "🥈", "description": "Precious metal - Silver"},
}

# Theme-friendly colors (work well in both light and dark mode)
COMMODITIES_COLOR_OPTIONS = {
    "Gold": "#FFD700",
    "Silver": "#C0C0C0",
    "Copper": "#B87333",
    "Crimson Red": "#DC143C",
    "Navy Blue": "#003366",
    "Dark Orange": "#FF8C00",
    "Forest Green": "#228B22",
    "Purple": "#8B008B",
    "Teal": "#008080",
    "Maroon": "#800000",
    "Olive": "#808000",
    "Steel Blue": "#4682B4",
}