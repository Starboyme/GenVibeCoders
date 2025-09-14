from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, model_validator


class DecisionRequest(BaseModel):
    origin: Optional[str] = None
    destination: str
    start_date: datetime
    end_date: datetime
    no_of_people: int
    budget: Optional[int] = None
    currency: Optional[str] = None
    mode_of_travel: Literal["public", "own", "rental"]
    mileage_of_vehicle: Optional[int] = None

    @model_validator(mode="after")
    def validate_mileage(self):
        """
        Validate the mileage of the vehicle if the mode of travel is own.
        """
        if self.mode_of_travel == "own" and self.mileage_of_vehicle is None:
            raise ValueError("Mileage of vehicle is required if the mode of travel is own.")
        return self