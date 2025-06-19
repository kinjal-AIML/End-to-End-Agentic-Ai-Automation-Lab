import requests
from langchain_core.tools import tool

class WeatherService:
    @tool
    def get_weather_forecast(city: str, days: int = 5) -> str:
        """
        Fetches the weather forecast for a given city.
        """
        try:
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
            geo_response = requests.get(geo_url).json()
            if not geo_response.get('results'):
                return f"Error: Could not find {city}"
            lat = geo_response['results'][0]['latitude']
            lon = geo_response['results'][0]['longitude']
            
            forecast_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,weather_code&forecast_days={days}"
            data = requests.get(forecast_url).json()
            
            conditions = {
                0: "Clear", 1: "Mostly clear", 2: "Partly cloudy", 3: "Overcast",
                45: "Foggy", 51: "Light drizzle", 61: "Light rain", 63: "Rain",
                71: "Light snow", 95: "Thunderstorm"
            }
            
            forecast_text = f"Weather forecast for {city}:\n"
            for i in range(len(data['daily']['time'])):
                date = data['daily']['time'][i]
                max_temp = data['daily']['temperature_2m_max'][i]
                min_temp = data['daily']['temperature_2m_min'][i]
                code = data['daily']['weather_code'][i]
                condition = conditions.get(code, "Unknown")
                forecast_text += f"{date}: {condition}, High {max_temp}°C, Low {min_temp}°C\n"
            return forecast_text
        except Exception as e:
            return f"Error: {str(e)}"