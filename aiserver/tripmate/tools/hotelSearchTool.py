"""Tool to search for hotels using SerpApi's Google Hotels API engine."""
import logging
import os
import math
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
    min_rating: Optional[Literal["7", "8", "9"]] = Field(default="7", description="Hotel rating filter: '7' → 3.5+, '8' → 4.0+, '9' → 4.5+. Defaults to '7' (3.5+).")
    hotel_class: Optional[str] = Field(default="2, 3, 4, 5", description="Comma-separated hotel star ratings: '2'=2-star, '3'=3-star, '4'=4-star, '5'=5-star. Example: '3,4,5'")
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
    - Allowed values: {'7', '8', '9'} (as strings).
    - Defaults to '7' if user input is invalid.
    - Converts to int before use.
    """
    allowed = {"7", "8", "9"}
    default_rating = "7"
    v = v if v in allowed else default_rating
    return int(v)  # convert to integer so API params use numbers


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
    hotel_class: Optional[int]
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
        hotel_class=raw.get("extracted_hotel_class"),
        overall_rating=raw.get("overall_rating"),
        reviews=raw.get("reviews"),
        location_rating=raw.get("location_rating"),
        amenities=raw.get("amenities"),
        excluded_amenities=raw.get("excluded_amenities"),
        essential_info=raw.get("essential_info"),
        rawSearchData=raw
    )


def compute_hotel_score(hotel, min_price, max_price, max_reviews, avg_stars, weights=None) -> float:
    """
    Compute weighted hotel score using:
    - Price (Non-linear price scaling for rate_per_night.extracted_lowest)
    - Hotel class (stars / 5)
    - Rating (rating / 5)
    - Reviews (log-scaled)
    - Location (location / 5)
    - Penalty for low-star hotels
    """
    if weights is None:
        weights = {
            "price": 0.15,
            "hotel_class": 0.3,
            "rating": 0.25,
            "reviews": 0.2,
            "location": 0.1
        }

    price = hotel.get('rate_per_night', {}).get('extracted_lowest', max_price)
    stars = hotel.get('hotel_class', avg_stars) or avg_stars
    rating = hotel.get('overall_rating', 0)
    reviews = hotel.get('reviews', 0)
    location = hotel.get('location_rating', 5)

    # --- Non-linear Price Scaling ---
    if max_price > min_price:
        price_norm = (price - min_price) / (max_price - min_price)
        price_score = 1 - math.sqrt(price_norm)  # smooth scaling: cheap != huge advantage
    else:
        price_score = 1

    # Penalize very low-star hotels so cheap 2-star doesn't dominate
    if stars < 3:
        price_score *= 0.7

    # --- Normalization for other features ---
    hotel_class_score = stars / 5
    rating_score = rating / 5
    reviews_score = math.log(1 + reviews) / math.log(1 + max_reviews) if max_reviews > 0 else 0
    location_score = location / 5  # because location rating is out of 5

    final_score = (
        weights['price'] * price_score +
        weights['hotel_class'] * hotel_class_score +
        weights['rating'] * rating_score +
        weights['reviews'] * reviews_score +
        weights['location'] * location_score
    )

    return final_score


def hotels_search(
        search_query: str,
        check_in_date: str,
        check_out_date: str,
        num_passengers: Optional[int] = 2,
        budget: Optional[float] = 10000.0,
        min_rating: Optional[Literal["7", "8", "9"]] = "7",
        hotel_class: Optional[str] = "2, 3, 4, 5",
        currency: Optional[str] = "INR"
    ) -> HotelSearchOutput:
        """
        Search hotels using SerpAPI's Google Hotels API and return structured hotel data (HotelSearchOutput).

        This function:
        - Builds a query using the input search parameters.
        - Calls the SerpAPI Google Hotels API to fetch hotel listings.
        - Extracts and maps the API response into the defined Pydantic models - HotelSearchOutput.
        - Uses multi-criteria sorting to rank hotels.
        - Returns a structured list of hotel search results for further use.

        Args:
            hotel_search_input (HotelSearchInput):
                Input parameters for the hotel search, including:
                - search_query: Destination or hotel search term.
                - check_in_date / check_out_date: Stay period.
                - num_passengers: Number of adults (optional).
                - currency: Currency for pricing (optional).
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
            - Filter results or sort by ratings/prices as needed.
        """

        # --- Ensure API key is set ---
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            raise RuntimeError("SERPAPI_API_KEY environment variable is required")
        
        # --- Convert dict input to Pydantic model safely ---
        try:
            hotel_search_input = HotelSearchInput(
                search_query=search_query,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                num_passengers=num_passengers,
                budget=budget,
                min_rating=min_rating,
                hotel_class=hotel_class,
                currency=currency
            )
        except Exception as e:
            logging.error(f"Input validation failed: {e}")
            return HotelSearchOutput(hotels=[])

        base_url = "https://serpapi.com/search.json"
        params = {
            "engine": "google_hotels",
            "q": hotel_search_input.search_query,
            "check_in_date": hotel_search_input.check_in_date,
            "check_out_date": hotel_search_input.check_out_date,
            "adults": hotel_search_input.num_passengers,
            "currency": hotel_search_input.currency,
            "max_price": int(hotel_search_input.budget),
            "rating": int(hotel_search_input.min_rating),
            "hotel_class": hotel_search_input.hotel_class,
            "api_key": api_key
        }

        try:
            # --- Call API ---
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # --- Extract hotel data safely ---
            hotels_raw = data.get("properties", [])
            if not hotels_raw:
                logging.warning("No hotels found in API response")
                return HotelSearchOutput(hotels=[])
            
            hotels = [extract_hotel_data(h).model_dump() for h in hotels_raw]

            # --- Compute min/max prices and max reviews for normalization ---
            prices = [h.get('rate_per_night', {}).get('extracted_lowest', 0) for h in hotels]
            min_price = min(prices) if prices else 0
            max_price = max(prices) if prices else 1
            max_reviews = max(h.get('reviews', 0) for h in hotels) if hotels else 1
            avg_stars = sum(h.get('hotel_class', 0) for h in hotels) / len(hotels) if hotels else 3
            
            logging.info(f"Price range: {min_price} - {max_price}, Max reviews: {max_reviews}, Avg stars: {avg_stars}")

            # --- Apply weighted scoring ---
            for h in hotels:
                h['final_score'] = compute_hotel_score(h, min_price, max_price, max_reviews, avg_stars)

            # Sort hotels by final_score descending
            hotels_sorted = sorted(hotels, key=lambda x: x['final_score'], reverse=True)

            return HotelSearchOutput(hotels=hotels_sorted)
        
        except requests.RequestException as e:
            logging.error(f"API request failed: {e}")
            return HotelSearchOutput(hotels=[])

        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return HotelSearchOutput(hotels=[])

