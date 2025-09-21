# trainSearchTool.py
"""Tool to search for trains using RailRadar's APIs"""
import os
import requests
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()

# --------------------------
# Pydantic Models
# --------------------------

class TrainSearchInput(BaseModel):
    origin: str = Field(description="The Origin Railway Station Code")
    destination: str = Field(description="The Destination Railway Station Code")
    departure_date: str = Field(description="The Departure date in YYYY-MM-DD format")
    num_passengers: int = Field(default=1, description="Number of passengers (adults)")
    budget: float = Field(default=3000.0, description="Budget for train search")
    currency: str = Field(default="INR", description="Currency (ISO code)")

class TrainResult(BaseModel):
    trainNumber: str
    trainName: str
    sourceStationCode: str
    destinationStationCode: str
    departureTime: Optional[str] = None
    departureDate: Optional[str] = None
    arrivalTime: Optional[str] = None
    arrivalDate: Optional[str] = None

class TrainSearchOutput(BaseModel):
    trains: List[TrainResult]

# --------------------------
# API Client
# --------------------------

API_BASE = "https://railradar.in/api/v1"
API_KEY = os.getenv("RAILRADAR_API_KEY")

HEADERS = {
    "accept": "application/json",
    "x-api-key": API_KEY
}

def subtract_days(date_str: str, days: int) -> str:
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    new_date = date_obj - timedelta(days=days)
    return new_date.strftime("%Y-%m-%d")

def add_days(date_str: str, days: int) -> str:
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    new_date = date_obj + timedelta(days=days)
    return new_date.strftime("%Y-%m-%d")

def format_date_dd_mmm_yyyy(date_str: str) -> str:
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return date_obj.strftime("%d-%b-%Y")

def train_search(
    origin: str,
    destination: str,
    departure_date: str,
    num_passengers: int = 1,
    budget: float = 3000.0,
    currency: str = "INR"
) -> TrainSearchOutput:
    if not API_KEY:
        raise ValueError("Missing API key: Set environment variable RAILRADAR_API_KEY")

    # 1. Get trains between stations
    url = f"{API_BASE}/trains/between"
    params = {"from": origin, "to": destination}
    resp = requests.get(url, headers=HEADERS, params=params)
    resp.raise_for_status()
    trains_between = resp.json().get("data", [])

    results: List[TrainResult] = []

    # 2. For each train, fetch schedule with journey date
    for train in trains_between:
        train_number = train.get("trainNumber")
        train_name = train.get("trainName")

        schedule_url = f"{API_BASE}/trains/{train_number}/schedule"
        schedule_params = {"journeyDate": departure_date}
        sched_resp = requests.get(schedule_url, headers=HEADERS, params=schedule_params)

        if sched_resp.status_code != 200:
            print("Schedule API returned", sched_resp)
            continue  # skip train if schedule API fails

        sched_data = sched_resp.json().get("data")
        sched_data_availableStartDate = sched_data["availableStartDates"]
        if not sched_data_availableStartDate or len(sched_data_availableStartDate) == 0:
            continue  # Train info not found!
        
        for route in sched_data["route"]:
            if(route["station"]["code"] == origin):
                journey_day = int(route.get("journeyDay", 1))
                toStartDate = subtract_days(departure_date,journey_day - 1)
                break
        
        if not toStartDate or format_date_dd_mmm_yyyy(toStartDate) not in sched_data_availableStartDate:
            continue #Train not arriving in the origin station at the departure_date

        route = sched_data["route"]
        departure_time, arrival_time, arrival_date = None, None, None

        for stop in route:
            if stop["station"]["code"] == origin:
                departure_time = stop["schedule"]["departure"]
            if stop["station"]["code"] == destination:
                journey_day = int(stop.get("journeyDay", 1))  # default 1 if missing
                arrival_date = add_days(departure_date, journey_day - 1)
                arrival_time = stop["schedule"]["arrival"]
                break

        # Only include trains with valid times for both origin and destination
        if departure_time and arrival_time:
            results.append(TrainResult(
                trainNumber=train_number,
                trainName=train_name,
                sourceStationCode=origin,
                destinationStationCode=destination,
                departureTime=departure_time,
                departureDate=departure_date,
                arrivalTime=arrival_time,
                arrivalDate=arrival_date
            ))

    return TrainSearchOutput(trains=results)
