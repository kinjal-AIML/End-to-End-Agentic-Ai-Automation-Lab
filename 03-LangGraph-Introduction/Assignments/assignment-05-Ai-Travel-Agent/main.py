# main.py
from travel_planner import TravelPlanner

def main():
    planner = TravelPlanner()
    
    # Example user input (can be replaced with input() for interactivity)
    city = "Dhaka"
    days = 5
    hotel_budget = 70
    native_currency = "USD"
    target_currency = "BDT"
    interests = "sightseeing, local food, public transport"
    
    # Generate travel plan
    plan = planner.plan_trip(
        city=city,
        days=days,
        hotel_budget=hotel_budget,
        native_currency=native_currency,
        target_currency=target_currency,
        interests=interests
    )
    
    print(plan)

if __name__ == "__main__":
    main()