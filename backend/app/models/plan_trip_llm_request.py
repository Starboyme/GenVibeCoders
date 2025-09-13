from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, Field, validator
from pydantic import ConfigDict
from datetime import datetime


class TravelPreferences(BaseModel):
    onward: Literal["flight", "train", "bus", "car", "bike"]
    within_destination: Literal["selfDrivingCar", "taxi", "none"]
    return_: Literal["flight", "train", "bus", "car", "bike"] = Field(..., alias="return")
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class AccommodationPreferences(BaseModel):
    types: List[str]
    min_rating: float
    amenities: List[str]
    room_type: str
    proximity_preference: str

    @validator("min_rating")
    def validate_rating(cls, v: float) -> float:
        if not (0.0 <= v <= 5.0):
            raise ValueError("min_rating must be between 0.0 and 5.0")
        return v

    model_config = ConfigDict(extra="forbid")


class Preferences(BaseModel):
    travel_preferences: TravelPreferences
    accommodation_preferences: AccommodationPreferences
    food_preferences: List[str]
    interests: List[str]
    special_constraints: List[str] = []
    model_config = ConfigDict(extra="forbid")


class TripDetails(BaseModel):
    from_location: str = Field(..., alias="from")
    destination: str
    start_date: str
    end_date: str
    budget: str
    currency: str
    transport: Literal["flight", "train", "bus", "car", "bike"]
    status: Literal["draft", "confirmed", "in_progress", "completed", "cancelled"]
    phase: Literal["planning", "booking", "travelling", "completed"]
    preferences: Preferences

    @validator("start_date", "end_date")
    def validate_dates(cls, v: str) -> str:
        # Expect format DD/MM/YYYY
        try:
            datetime.strptime(v, "%d/%m/%Y")
        except Exception as exc:
            raise ValueError("Date must be in DD/MM/YYYY format") from exc
        return v

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class PlanTripLLMRequest(BaseModel):
    trip: TripDetails
    model_config = ConfigDict(extra="forbid")


