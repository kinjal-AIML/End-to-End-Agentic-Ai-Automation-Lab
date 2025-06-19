# tools/itinerary_builder.py
from langchain_core.tools import tool
from prompts.itinerary_prompts import ItineraryPrompts

class ItineraryBuilder:
    @tool
    def get_day_plan(city: str, interests: str = "sightseeing, local food, culture") -> str:
        """
        Generate a one-day itinerary for a city.
        Args:
            city (str): City name.
            interests (str): User interests.
        Returns: str: One-day plan prompt.
        """
        return ItineraryPrompts.get_day_plan_prompt(city, interests)

    @tool
    def create_full_itinerary(city: str, days: int, interests: str = "sightseeing, food") -> str:
        """
        Generate a multi-day itinerary for a city.
        Args:
            city (str): City name.
            days (int): Number of days.
            interests (str): User interests.
        Returns: str: Full itinerary prompt.
        """
        return ItineraryPrompts.create_full_itinerary_prompt(city, days, interests)