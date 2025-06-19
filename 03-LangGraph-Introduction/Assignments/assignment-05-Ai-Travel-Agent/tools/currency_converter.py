# tools/currency_converter.py
import requests
from langchain_core.tools import tool
from config import Config

class CurrencyConverter:
    @tool
    def get_conversion_factor(base_currency: str, target_currency: str) -> float:
        """
        Fetch the currency conversion rate.
        Args:
            base_currency (str): Base currency code (e.g., USD).
            target_currency (str): Target currency code (e.g., BDT).
        Returns: float: Conversion rate.
        """
        url = f"https://v6.exchangerate-api.com/v6/{Config.EXCHANGE_RATE_API}/pair/{base_currency}/{target_currency}"
        response = requests.get(url).json()
        if response.get("conversion_rate"):
            return float(response["conversion_rate"])
        raise ValueError(f"Failed to get conversion rate: {response}")

    @tool
    def convert_currency(amount: float, conversion_rate: float) -> float:
        """
        Convert an amount using a conversion rate.
        Args:
            amount (float): Amount in base currency.
            conversion_rate (float): Conversion rate to target currency.
        Returns: float: Amount in target currency.
        """
        return round(amount * conversion_rate, 2)