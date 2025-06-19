# travel_planner.py
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from tools.weather_service import WeatherService
from tools.attraction_finder import AttractionFinder
from tools.hotel_service import HotelService
from tools.currency_converter import CurrencyConverter
from tools.cost_calculator import CostCalculator
from tools.itinerary_builder import ItineraryBuilder
from tools.trip_summary import TripSummary
from config import Config

class TravelPlanner:
    def __init__(self):
        Config.set_environment()
        self.llm = ChatGroq(model="qwen/qwen3-32b")
        self.weather_service = WeatherService()
        self.attraction_finder = AttractionFinder()
        self.hotel_service = HotelService()
        self.currency_converter = CurrencyConverter()
        self.cost_calculator = CostCalculator()
        self.itinerary_builder = ItineraryBuilder()
        self.trip_summary = TripSummary()

    def plan_trip(self, city: str, days: int, hotel_budget: float, native_currency: str, target_currency: str, interests: str) -> str:
        """
        Generate a complete travel plan.
        Args:
            city (str): Destination city.
            days (int): Number of days.
            hotel_budget (float): Budget per night in USD.
            native_currency (str): User's native currency.
            target_currency (str): Currency for payments.
            interests (str): User preferences (e.g., local food, public transport).
        Returns: str: Complete travel plan.
        """
        # Get weather forecast
        weather = self.weather_service.get_weather_forecast.invoke({"city": city, "days": days})
        print(weather)

        # Get attractions
        attractions = self.attraction_finder.search_attractions(city=city)
        restaurants = self.attraction_finder.search_restaurants(city=city)
        activities = self.attraction_finder.search_activities(city=city)
        transport = self.attraction_finder.search_transportation(city=city)

        # Get hotel cost
        hotels = self.hotel_service.search_hotels(city=city, budget=hotel_budget)
        hotel_cost = self.hotel_service.estimate_hotel_cost(price_per_night=hotel_budget, total_days=days)

        # Currency conversion
        conversion_rate = self.currency_converter.get_conversion_factor(base_currency=native_currency, target_currency=target_currency)
        hotel_cost_target = self.currency_converter.convert_currency(amount=hotel_cost, conversion_rate=conversion_rate)

        # Estimate other costs (assumed for simplicity)
        food_cost = 30 * days  # $30/day
        transport_cost = 10 * days  # $10/day
        activity_cost = 10 * days  # $10/day
        total_cost = self.cost_calculator.calculate_total_cost(hotel_cost=hotel_cost, activity_cost=activity_cost, transport_cost=transport_cost)
        daily_budget = self.cost_calculator.calculate_daily_budget(total_cost=total_cost, days=days)
        total_cost_target = self.currency_converter.convert_currency(amount=total_cost, conversion_rate=conversion_rate)

        # Generate itinerary
        itinerary = self.itinerary_builder.create_full_itinerary(city=city, days=days, interests=interests)

        # Generate summary
        summary = self.trip_summary.create_trip_summary(city=city, days=days, total_cost=total_cost_target, currency=target_currency)

        # Format output (simplified for brevity)
        output = (
            f"# ✈️ {days}-Day Trip to {city} ✈️\n\n"
            f"## 🌤️ Weather Forecast\n{weather}\n\n"
            f"## 🏨 Hotel\n- Budget: ${hotel_budget}/night\n- Total: ${hotel_cost} ({hotel_cost_target} {target_currency})\n- Options: {hotels}\n\n"
            f"## 📍 Attractions\n{attractions}\n\n"
            f"## 🍽️ Restaurants\n{restaurants}\n\n"
            f"## 🎫 Activities\n{activities}\n\n"
            f"## 🚇 Transport\n{transport}\n\n"
            f"## 💰 Costs\n- Food: ${food_cost}\n- Transport: ${transport_cost}\n- Activities: ${activity_cost}\n- Total: ${total_cost} ({total_cost_target} {target_currency})\n- Daily Budget: ${daily_budget}/day\n\n"
            f"## 🗓️ Itinerary\n{itinerary}\n\n"
            f"## 📋 Summary\n{summary}"
        )
        return output