from fastapi import APIRouter
from app.models.plan_trip_request import PlanTripRequest
from app.services.itenerary import build_itenerary
router = APIRouter()

@router.post("/plan")
async def plan_trip(request: PlanTripRequest):
    print("Entered method - Routes.plan_trip with request",request)
    itenerary = await build_itenerary(request)
    print("Exited method - Routes.plan_trip")
    return {"itenerary" : itenerary}

@router.get("/test/agents")
async def test_agents():
    from app.services.ai_agents import ActivityAgent, FoodAgent, _AGENT
    
    trip = {"destination": "Goa", "preferences": {"interests": ["adventure"]}}
    
    activity_agent = ActivityAgent(_AGENT)
    food_agent = FoodAgent(_AGENT)
    
    activities_day1 = await activity_agent.recommend(trip, 1)
    activities_day2 = await activity_agent.recommend(trip, 2)
    food_day1 = await food_agent.recommend(trip, 1)
    food_day2 = await food_agent.recommend(trip, 2)
    
    return {
        "activities_day1": activities_day1,
        "activities_day2": activities_day2,
        "food_day1": food_day1,
        "food_day2": food_day2
    }
