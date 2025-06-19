# tools/trip_summary.py
from langchain_core.tools import tool
from prompts.summary_prompts import SummaryPrompts

class TripSummary:
    @tool
    def create_trip_summary(city: str, days: int, total_cost: float, currency: str = "USD") -> str:
        """
        Generate a high-level trip summary.
        Args:
            city (str): Destination city.
            days (int): Number of days.
            total_cost (float): Total cost.
            currency (str): Currency code.
        Returns: str: Summary prompt.
        """
        return SummaryPrompts.create_trip_summary_prompt(city, days, total_cost, currency)