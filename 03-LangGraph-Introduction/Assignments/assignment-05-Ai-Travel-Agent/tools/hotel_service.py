# tools/hotel_service.py
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.tools import tool

class HotelService:
    @tool
    def search_hotels(city: str, budget: int) -> str:
        """
        Search hotels in a city under the user's budget.
        Args:
            city (str): City to search for hotels.
            budget (int): Maximum budget per night in USD.
        Returns: str: List of hotels and their costs.
        """
        search = GoogleSerperAPIWrapper()
        query = f"best hotel in {city} under ${budget}"
        return search.run(query)

    @tool
    def estimate_hotel_cost(price_per_night: float, total_days: int) -> float:
        """
        Estimate total hotel cost based on price per night and number of days.
        Args:
            price_per_night (float): Price per night in USD.
            total_days (int): Number of days.
        Returns: float: Total hotel cost.
        """
        return round(price_per_night * total_days, 2)