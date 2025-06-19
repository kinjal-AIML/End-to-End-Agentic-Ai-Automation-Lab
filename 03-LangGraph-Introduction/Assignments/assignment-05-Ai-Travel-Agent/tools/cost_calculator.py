# tools/cost_calculator.py
from langchain_core.tools import tool

class CostCalculator:
    @tool
    def calculate_total_cost(hotel_cost: float, activity_cost: float, transport_cost: float) -> float:
        """
        Calculate the total cost of the trip.
        Args:
            hotel_cost (float): Total hotel cost.
            activity_cost (float): Total activity cost.
            transport_cost (float): Total transportation cost.
        Returns: float: Total trip cost.
        """
        return round(hotel_cost + activity_cost + transport_cost, 2)

    @tool
    def calculate_daily_budget(total_cost: float, days: int) -> float:
        """
        Calculate daily budget based on total cost and number of days.
        Args:
            total_cost (float): Total trip cost.
            days (int): Number of days.
        Returns: float: Daily budget.
        """
        if days <= 0:
            raise ValueError("Days must be greater than zero.")
        return round(total_cost / days, 2)