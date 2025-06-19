# tools/attraction_finder.py
from langchain_tavily import TavilySearch
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.tools import tool
from config import Config

class AttractionFinder:
    @tool
    def search_attractions(city: str) -> dict:
        """
        Search top tourist attractions in a given city.
        Args: city (str): Name of the city.
        Returns: dict: List of attractions.
        """
        tavily = TavilySearch(max_results=5)
        return tavily.invoke(f"top tourist attractions in {city}")

    @tool
    def search_restaurants(city: str) -> dict:
        """
        Search the best restaurants in a given city.
        Args: city (str): Name of the city.
        Returns: dict: List of restaurants.
        """
        tavily = TavilySearch(max_results=5)
        return tavily.invoke(f"best restaurants to try in {city}")

    @tool
    def search_activities(city: str) -> dict:
        """
        Search top activities or things to do in a city.
        Args: city (str): Name of the city.
        Returns: dict: List of activities.
        """
        tavily = TavilySearch(max_results=5)
        return tavily.invoke(f"fun activities to do in {city}")

    @tool
    def search_transportation(city: str) -> dict:
        """
        Search transportation options in a city.
        Args: city (str): Name of the city.
        Returns: dict: Transportation options.
        """
        tavily = TavilySearch(max_results=5)
        return tavily.invoke(f"list of transportation options in {city} for tourists")