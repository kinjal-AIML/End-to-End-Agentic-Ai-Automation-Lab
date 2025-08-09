## python function to get time

def get_time(city: str) -> str:
    """Get the current time in the specific city"""
    if city.lower() == "dhaka":
        return f"the time is 11 am"
    elif city.lower() == "khulna":
        return f"time is 4 pm"
    else:
        return f"Sorry i don't know the time of the {city}."