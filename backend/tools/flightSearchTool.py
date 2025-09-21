# transportTool.py
"""Tool to search for flights using SerpApi's Google Flights engine."""
import os
from typing import Optional, List, Dict, Any
import requests
from pydantic import BaseModel, Field
from dotenv import load_dotenv
load_dotenv()


class FlightsSearchInput(BaseModel):
    #Input for flight search queries"""
    origin: str = Field(description="The origin airport code (IATA) or location kgmid")
    destination: str = Field(description="The destination airport code (IATA) or location kgmid")
    departure_date: str = Field(description="The departure date in YYYY-MM-DD format")
    return_date: Optional[str] = Field(default=None, description="The return date in YYYY-MM-DD format, if applicable")
    num_passengers: int = Field(default=1, description="The number of passengers (adults)")
    budget: float = Field(default=10000.0, description="The budget for the flight search")
    currency: str = Field(default="INR", description="The currency for the budget (ISO code, e.g. INR, USD)")
    type: int = Field(default=2, description="Type of flight: 1 for round-trip, 2 for one-way, 3 for round-trip")


class FlightSearchOutput(BaseModel):
    class FlightSearchResult(BaseModel):
        # pick the fields you need — this is a general structure that you can extend
        price: Optional[float] = None
        currency: Optional[str] = None
        airlines: Optional[List[str]] = None
        total_duration: Optional[str] = None
        stops: Optional[int] = None
        segments: Optional[List[Dict[str, Any]]] = None
        booking_token: Optional[str] = None
        raw: Optional[Dict[str, Any]] = None  # keep raw JSON for debugging / advanced use

    # Output for flight search results
    flights: List[FlightSearchResult] = Field(description="A list of flight options matching the search criteria")

def format_duration(minutes: int | None) -> str | None:
    """Convert minutes into H:MM format (e.g., 70 → '1h 10m')."""
    if minutes is None:
        return None
    try:
        minutes = int(minutes)
        hours, mins = divmod(minutes, 60)
        if hours > 0:
            return f"{hours}h {mins}m"
        return f"{mins}m"
    except Exception:
        return None


def flights_search(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    num_passengers: int = 1,
    budget: float = 10000.0,
    currency: str = "INR",
    type: int = 2,
) -> FlightSearchOutput:
    """
    Query SerpApi's Google Flights engine and return parsed flight options.
    Requires SERPAPI_API_KEY environment variable to be set.

    Notes:
      - Uses 'departure_id' and 'arrival_id' as documented by SerpApi.
      - For a round-trip search include return_date; for one-way omit it.
    """
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        raise RuntimeError("SERPAPI_API_KEY environment variable is required")

    endpoint = "https://serpapi.com/search"
    params = {
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": destination,
        "outbound_date": departure_date,
        "adults": num_passengers,
        "currency": currency,
        "api_key": api_key,
        "type": type
        # optionally: "deep_search": "true"  # uncomment if you need exact browser-like results (slower)
    }
    if return_date:
        params["return_date"] = return_date

    # Optional optimization: avoid cache if fresh results required:
    # params["no_cache"] = "true"

    resp = requests.get(endpoint, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    print(f"\nRaw SerpApi Response: {data}\n")

    # choose which arrays to parse: best_flights first (if present), then other_flights
    candidates = []
    if isinstance(data.get("best_flights"), list):
        candidates.extend(data.get("best_flights", []))
    if isinstance(data.get("other_flights"), list):
        candidates.extend(data.get("other_flights", []))
    # some responses may include 'flights' or differently structured entries; be defensive
    if not candidates and isinstance(data.get("flights"), list):
        candidates.extend(data.get("flights", []))

    results = []
    for entry in candidates:
        # Common safe-extraction helpers
        def _safe(d, *keys, default=None):
            cur = d
            for k in keys:
                if not isinstance(cur, dict) or k not in cur:
                    return default
                cur = cur[k]
            return cur

        # price extraction - can be int, str, or dict
        price = None
        currency_code = None

        price_field = entry.get("price")
        if isinstance(price_field, (int, float, str)):
            try:
                price = float(price_field)
            except Exception:
                price = None
        elif isinstance(price_field, dict):
            price = price_field.get("total") or price_field.get("price") or price_field.get("value")
            currency_code = price_field.get("currency") or currency_code

        # fallback
        if price is None:
            price = entry.get("total_price") or _safe(entry, "price", "total")

        # airlines: try to collect flight-level airline names/codes
        airlines = []
        segments = []
        raw_segments = entry.get("flights") or entry.get("segments") or []
        if isinstance(raw_segments, list):
            for seg in raw_segments:
                seg_info = {
                    "departure_airport": _safe(seg, "departure_airport", "id") or _safe(seg, "departure_airport", "name"),
                    "arrival_airport": _safe(seg, "arrival_airport", "id") or _safe(seg, "arrival_airport", "name"),
                    "departure_time": _safe(seg, "departure_airport", "time") or seg.get("departure_time"),
                    "arrival_time": _safe(seg, "arrival_airport", "time") or seg.get("arrival_time"),
                    "airline": _safe(seg, "airline", "name") or seg.get("airline"),
                    "duration": seg.get("duration")
                }
                if seg_info.get("airline"):
                    airlines.append(seg_info["airline"])
                segments.append(seg_info)

        # total duration and stops
        total_duration = entry.get("total_duration") or entry.get("duration") or entry.get("total_trip_duration")
        stops = None
        if isinstance(entry.get("stops"), (int, str)):
            try:
                stops = int(entry.get("stops"))
            except Exception:
                stops = None
        else:
            # infer from segments
            if isinstance(segments, list):
                stops = max(0, len(segments) - 1) if segments else None

        booking_token = entry.get("booking_token") or _safe(entry, "booking_options", 0, "booking_token")

        result_obj = FlightSearchOutput.FlightSearchResult(
            price=float(price) if price is not None else None,
            currency=currency_code or currency,
            airlines=list(dict.fromkeys([a for a in airlines if a])),  # unique preserving order
            total_duration=format_duration(total_duration),
            stops=stops,
            segments=segments if segments else None,
            booking_token=booking_token,
            raw=entry
        )
        results.append(result_obj)

    # Optionally filter by budget (provided by user)
    filtered_results = []
    for r in results:
        if r.price is None:
            # keep unknown-price results (optional), or skip them
            filtered_results.append(r)
            continue
        if r.price <= budget:
            filtered_results.append(r)

    return FlightSearchOutput(flights=filtered_results)
