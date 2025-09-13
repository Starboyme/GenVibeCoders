from app.agents.orchestrator import TripOrchestrator
from app.models.plan_trip_request import PlanTripRequest
from app.models.plan_trip_llm_request import PlanTripLLMRequest, TripDetails, Preferences, TravelPreferences, AccommodationPreferences

async def build_itenerary(request: PlanTripRequest):
    # Based on the request fetch the data from DB and form the below JSON
    print("Entered method - Services.build_itenerary with request -",request)
    orchestrator = TripOrchestrator()
    
    # Create the proper PlanTripLLMRequest object
    llm_request = PlanTripLLMRequest(
        trip=TripDetails(
            from_location="Bangalore",
            destination="Goa",
            start_date="01/10/2025",
            end_date="07/10/2025",
            budget="100000",
            currency="INR",
            transport="flight",
            status="draft",
            phase="planning",
            preferences=Preferences(
                travel_preferences=TravelPreferences(
                    onward="flight",
                    within_destination="selfDrivingCar",
                    return_="train"
                ),
                accommodation_preferences=AccommodationPreferences(
                    types=["airbnb", "hotel", "hostel"],
                    min_rating=3.5,
                    amenities=["wifi", "breakfast", "pool"],
                    room_type="private",
                    proximity_preference="city_center"
                ),
                food_preferences=["veg", "italian", "north indian"],
                interests=["adventure", "nightlife", "heritage"],
                special_constraints=[]
            )
        )
    )
    
    itenerary = await orchestrator.plan_trip(llm_request)
    print("Exited the method - Services.build_itenerary")
    return itenerary
    