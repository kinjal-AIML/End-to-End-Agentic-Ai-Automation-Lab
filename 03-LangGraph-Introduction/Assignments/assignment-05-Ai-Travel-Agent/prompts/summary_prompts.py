# prompts/summary_prompts.py
class SummaryPrompts:
    @staticmethod
    def create_trip_summary_prompt(city: str, days: int, total_cost: float, currency: str) -> str:
        return (
            f"Generate a short and friendly trip summary for a {days}-day trip to {city}. "
            f"The estimated total cost is {total_cost} {currency}. "
            f"Include key highlights like attractions, food, and tips for the traveler."
        )