# prompts/itinerary_prompts.py
class ItineraryPrompts:
    @staticmethod
    def get_day_plan_prompt(city: str, interests: str) -> str:
        return (
            f"You are planning a 1-day trip in {city}. "
            f"Generate a time-based schedule from 9:00 AM to 9:00 PM, including {interests}. "
            f"Include breakfast, lunch, dinner, 3-5 key attractions, and time for rest/shopping."
        )

    @staticmethod
    def create_full_itinerary_prompt(city: str, days: int, interests: str) -> str:
        return (
            f"Create a {days}-day itinerary for {city}, including activities based on {interests}. "
            f"Each day should include breakfast, lunch, dinner, 3–4 attractions, and cultural or relaxing activities. "
            f"Keep plans balanced and avoid repeating the same spots."
        )