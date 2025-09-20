"""Tool to search for hotels using SerpApi's Google Hotels API engine."""
import os
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
import requests
from pydantic import BaseModel, Field, field_validator, model_validator


class HotelSearchInput(BaseModel):
    #Input for hotel search queries
    search_query: str = Field(..., description="The location or place to search hotels in (e.g. city name, address, or latitude/longitude)")
    check_in_date: str = Field(..., description="The check-in date in the format -> YYYY-MM-DD. e.g. 2025-09-20")
    check_out_date: str = Field(..., description="The check-out date in the format -> YYYY-MM-DD. e.g. 2025-09-25")
    num_passengers: Optional[int] = Field(default=2, description="Number of guests (adults). Defaults to 2.")
    budget: Optional[float] = Field(default=10000.0, description="The budget or upper bound of price range for the hotel search. Defaults to 10000.0")
    min_rating: Optional[Literal[7, 8, 9]] = Field(default=7, description="Hotel rating filter: 7 → 3.5+, 8 → 4.0+, 9 → 4.5+. Defaults to 7 (3.5+).")
    hotel_class: Optional[str] = Field(default="2, 3, 4, 5", description="Comma-separated hotel star ratings: 2=2-star, 3=3-star, 4=4-star, 5=5-star. Example: '3,4,5'")
    currency: Optional[str] = Field(default="INR", description="The currency for the budget (ISO code, e.g. INR, USD)")

# ---- Date Parsing ----
@field_validator("check_in_date", "check_out_date")
@classmethod
def validate_dates(cls, v):
    # Try multiple date formats, fallback to YYYY-MM-DD
    """
    Validates and normalizes date strings.
    - Tries multiple common date formats.
    - Converts to standard YYYY-MM-DD format.
    - Raises error if parsing fails.
    """
    formats = ["%Y-%m-%d", "%Y/%m/%d", "%b %d %Y", "%d-%m-%Y"]
    for fmt in formats:
        try:
            parsed_date = datetime.strptime(v, fmt)
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            continue
    raise ValueError(f"Date '{v}' is invalid. Please use YYYY-MM-DD format.")


# ---- Auto-swap Dates if Wrong Order ----
@model_validator(mode="after")
def swap_dates_if_needed(self):
    """
    Ensures check_out_date is always after check_in_date.
    - If user provides dates in the wrong order, they are automatically swapped.
    """
    in_date = datetime.strptime(self.check_in_date, "%Y-%m-%d")
    out_date = datetime.strptime(self.check_out_date, "%Y-%m-%d")
    if out_date < in_date:
        self.check_in_date, self.check_out_date = self.check_out_date, self.check_in_date
    return self


@field_validator("hotel_class")
@classmethod
def validate_hotel_class(cls, v):
    """
    Validates hotel_class string.
    - Allows only '2', '3', '4', '5'.
    - Returns a normalized, comma-separated string of valid values.
    - Returns None if no valid values found.
    """
    if v is None:
        return v
    allowed = {"2", "3", "4", "5"}
    values = {val.strip() for val in v.split(",")}
    valid_values = values.intersection(allowed)  # keep only allowed ones
    return ",".join(sorted(valid_values)) if valid_values else None


@field_validator("min_rating")
@classmethod
def validate_min_rating(cls, v):
    """
    Validates minimum rating.
    - Allowed values: {7, 8, 9}.
    - Defaults to 7 if user input is invalid.
    """
    allowed = {7, 8, 9}
    default_rating = 7
    return v if v in allowed else default_rating


# ---------------- Output Models ----------------

class GPSCoordinates(BaseModel):
    latitude: float
    longitude: float

class RateInfo(BaseModel):
    lowest: Optional[str]
    extracted_lowest: Optional[float]

class HotelSearchResult(BaseModel):
    name: str
    description: Optional[str]
    link: Optional[str]
    gps_coordinates: Optional[GPSCoordinates]
    check_in_time: Optional[str]
    check_out_time: Optional[str]
    rate_per_night: Optional[RateInfo]
    total_rate: Optional[RateInfo]
    deal: Optional[str]
    hotel_class: Optional[str]
    overall_rating: Optional[float]
    reviews: Optional[int]
    location_rating: Optional[float]
    amenities: Optional[List[str]]
    excluded_amenities: Optional[List[str]]
    essential_info: Optional[List[str]]
    rawSearchData: Optional[Dict[str, Any]] = None  # keep raw JSON for debugging / advanced use

class HotelSearchOutput(BaseModel):
    # Output for hotel search results
    hotels: List[HotelSearchResult] = Field(description="A list of hotel options matching the search criteria")


# ---------------- API Call & Extraction ----------------

def extract_hotel_data(raw: dict) -> HotelSearchResult:
    """Map SerpAPI Google Hotels GET API response dict into Pydantic HotelSearchResult."""
    return HotelSearchResult(
        name=raw.get("name"),
        description=raw.get("description"),
        link=raw.get("link"),
        gps_coordinates=GPSCoordinates(**raw["gps_coordinates"]) if "gps_coordinates" in raw else None,
        check_in_time=raw.get("check_in_time"),
        check_out_time=raw.get("check_out_time"),
        rate_per_night=RateInfo(**raw["rate_per_night"]) if "rate_per_night" in raw else None,
        total_rate=RateInfo(**raw["total_rate"]) if "total_rate" in raw else None,
        deal=raw.get("deal"),
        hotel_class=raw.get("hotel_class"),
        overall_rating=raw.get("overall_rating"),
        reviews=raw.get("reviews"),
        location_rating=raw.get("location_rating"),
        amenities=raw.get("amenities"),
        excluded_amenities=raw.get("excluded_amenities"),
        essential_info=raw.get("essential_info"),
        rawSearchData=raw
    )


def hotels_search(hotel_search_input: HotelSearchInput) -> HotelSearchOutput:
    """
    Search hotels using SerpAPI's Google Hotels API and return structured hotel data (HotelSearchOutput).

    This function:
      - Builds a query using the input search parameters.
      - Calls the SerpAPI Google Hotels API to fetch hotel listings.
      - Extracts and maps the API response into the defined Pydantic models - HotelSearchOutput.
      - Returns a structured list of hotel search results for further use.

    Args:
        hotel_search_input (HotelSearchInput):
            Input parameters for the hotel search, including:
              - search_query: Destination or hotel search term.
              - check_in_date / check_out_date: Stay period.
              - num_passengers: Number of adults.
              - currency: Currency for pricing.
              - budget: Maximum price per night (optional).
              - min_rating: Minimum overall rating filter (optional).
              - hotel_class: Desired hotel class/star rating (optional).

    Returns:
        HotelSearchOutput:
            A structured object containing:
              - hotels: List of hotels mapped to HotelSearchResult Pydantic models.

    Raises:
        RuntimeError: If SERPAPI_API_KEY environment variable is missing.
        requests.HTTPError: If the API request fails with a non-2xx status.
        ValueError: If response parsing fails unexpectedly.

    Notes:
        - Uses SerpAPI Google Hotels engine (`engine=google_hotels`).
        - `rawSearchData` field in output retains raw hotel JSON for debugging or advanced usage.
        - Can be extended to filter results or sort by ratings/prices as needed.
    """

    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        raise RuntimeError("SERPAPI_API_KEY environment variable is required")
    
    base_url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_hotels",
        "q": hotel_search_input.search_query,
        "check_in_date": hotel_search_input.check_in_date,
        "check_out_date": hotel_search_input.check_out_date,
        "adults": hotel_search_input.num_passengers,
        "currency": hotel_search_input.currency,
        "max_price": int(hotel_search_input.budget),
        "rating": hotel_search_input.min_rating,
        "hotel_class": hotel_search_input.hotel_class,
        "api_key": api_key
    }

    response = requests.get(base_url, params=params)
    response.raise_for_status()
    data = response.json()

    hotels_raw = data.get("properties", [])
    hotels = [extract_hotel_data(h) for h in hotels_raw]

    # Optional: filter by min_rating
    # hotels = [h for h in hotels if (h.overall_rating or 0) >= hotel_search_input.min_rating]

    # Sort by rating descending
    # hotels.sort(key=lambda x: x.overall_rating or 0, reverse=True)
    return HotelSearchOutput(hotels=hotels)

