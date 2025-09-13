from pydantic import BaseModel

class PlanTripRequest(BaseModel):
    user_id: str
    trip_id: str