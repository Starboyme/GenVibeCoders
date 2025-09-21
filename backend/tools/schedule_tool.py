"""
Schedule Tool for creating time-based daily itineraries
"""

from langchain.tools import tool
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
from pydantic import BaseModel, Field

class PlaceDetails(BaseModel):
    """Schema for place details"""
    name: str = Field(description="Name of the place")
    address: Optional[str] = Field(default="", description="Address of the place")
    latitude: Optional[float] = Field(default=None, description="Latitude coordinate")
    longitude: Optional[float] = Field(default=None, description="Longitude coordinate")
    rating: Optional[float] = Field(default=None, description="Rating of the place")
    type: Optional[str] = Field(default="attraction", description="Type of place")

class ScheduleInput(BaseModel):
    """Input schema for create_daily_schedule"""
    optimized_route: List[Dict[str, Any]] = Field(
        description="List of places in optimal visiting order from TSP solver. Each place should have: name, type, latitude, longitude, address, rating"
    )
    total_days: int = Field(description="Total number of days for the trip")
    travel_times_matrix: Optional[List[List[float]]] = Field(
        default=None, 
        description="Optional matrix of travel times between places (in minutes)"
    )
    start_time: str = Field(
        default="08:00", 
        description="Start time for each day in HH:MM format"
    )

@tool(args_schema=ScheduleInput)
def create_daily_schedule(
    optimized_route: List[Dict[str, Any]], 
    total_days: int,
    travel_times_matrix: Optional[List[List[float]]] = None,
    start_time: str = "08:00"
) -> Dict[str, Any]:
    """
    Create a detailed daily schedule with specific times for visiting each place in the optimized route.
    
    Args:
        optimized_route: List of places in optimal visiting order from TSP solver
                        Each place should have: name, type, latitude, longitude, address, rating
        total_days: Total number of days for the trip
        travel_times_matrix: Optional matrix of travel times between places (in minutes)
        start_time: Start time for each day in HH:MM format (default: 08:00)
    
    Returns:
        Dictionary with daily schedules including times, places, and activities
    """
    
    if not optimized_route:
        return {"error": "No optimized route provided"}
    
    try:
        # Parse start time
        start_hour, start_minute = map(int, start_time.split(':'))
        
        # Define typical visit durations by place type (in minutes)
        visit_durations = {
            'temple': 45,
            'church': 30,
            'mosque': 30,
            'religious_site': 45,
            'museum': 120,
            'historical_site': 90,
            'monument': 60,
            'palace': 120,
            'fort': 90,
            'viewpoint': 45,
            'scenic_spot': 60,
            'waterfall': 90,
            'lake': 60,
            'park': 75,
            'garden': 60,
            'hill_station': 120,
            'wildlife_sanctuary': 180,
            'national_park': 240,
            'beach': 120,
            'market': 60,
            'shopping': 90,
            'restaurant': 90,
            'cafe': 45,
            'resort': 60,
            'hotel': 30,
            'default': 75
        }
        
        # Define meal times and durations
        meal_times = {
            'breakfast': {'start': '08:00', 'duration': 45},
            'lunch': {'start': '12:30', 'duration': 60},
            'snack': {'start': '16:00', 'duration': 30},
            'dinner': {'start': '19:30', 'duration': 75}
        }
        
        # Calculate places per day
        total_places = len(optimized_route)
        places_per_day = max(1, total_places // total_days)
        remaining_places = total_places % total_days
        
        daily_schedules = {}
        place_index = 0
        
        for day in range(1, total_days + 1):
            daily_schedules[f"day_{day}"] = {
                "date": f"Day {day}",
                "activities": [],
                "summary": {
                    "total_places": 0,
                    "total_travel_time": 0,
                    "start_time": start_time,
                    "estimated_end_time": ""
                }
            }
            
            # Determine number of places for this day
            places_today = places_per_day
            if day <= remaining_places:
                places_today += 1
            
            current_time = datetime.strptime(start_time, '%H:%M')
            
            # Add breakfast
            daily_schedules[f"day_{day}"]["activities"].append({
                "time": current_time.strftime('%H:%M'),
                "activity": "Breakfast",
                "type": "meal",
                "duration_minutes": meal_times['breakfast']['duration'],
                "notes": "Start your day with a good meal"
            })
            current_time += timedelta(minutes=meal_times['breakfast']['duration'])
            
            # Add places for the day
            for i in range(places_today):
                if place_index >= len(optimized_route):
                    break
                    
                place = optimized_route[place_index]
                
                # Determine visit duration
                place_type = place.get('type', 'default').lower()
                duration = visit_durations.get(place_type, visit_durations['default'])
                
                # Add travel time (simplified - could use actual matrix)
                if i > 0:  # Not the first place of the day
                    travel_time = 30  # Default 30 minutes travel time
                    if travel_times_matrix and place_index > 0:
                        prev_idx = place_index - 1
                        if prev_idx < len(travel_times_matrix) and place_index < len(travel_times_matrix[prev_idx]):
                            travel_time = int(travel_times_matrix[prev_idx][place_index])
                    
                    # Add travel activity
                    daily_schedules[f"day_{day}"]["activities"].append({
                        "time": current_time.strftime('%H:%M'),
                        "activity": f"Travel to {place['name']}",
                        "type": "travel",
                        "duration_minutes": travel_time,
                        "notes": f"Travel time from previous location"
                    })
                    current_time += timedelta(minutes=travel_time)
                    daily_schedules[f"day_{day}"]["summary"]["total_travel_time"] += travel_time
                
                # Check if it's lunch time
                if current_time.hour >= 12 and current_time.hour < 14:
                    # Add lunch if we haven't had it yet
                    lunch_added = any(act['activity'] == 'Lunch' for act in daily_schedules[f"day_{day}"]["activities"])
                    if not lunch_added:
                        daily_schedules[f"day_{day}"]["activities"].append({
                            "time": current_time.strftime('%H:%M'),
                            "activity": "Lunch",
                            "type": "meal",
                            "duration_minutes": meal_times['lunch']['duration'],
                            "notes": "Midday meal break"
                        })
                        current_time += timedelta(minutes=meal_times['lunch']['duration'])
                
                # Add the main place visit
                daily_schedules[f"day_{day}"]["activities"].append({
                    "time": current_time.strftime('%H:%M'),
                    "activity": f"Visit {place['name']}",
                    "type": "sightseeing",
                    "duration_minutes": duration,
                    "place_details": {
                        "name": place['name'],
                        "address": place.get('address', 'Address not available'),
                        "latitude": place.get('latitude'),
                        "longitude": place.get('longitude'),
                        "rating": place.get('rating'),
                        "place_type": place.get('type')
                    },
                    "notes": f"Explore and enjoy this {place_type.replace('_', ' ')}"
                })
                current_time += timedelta(minutes=duration)
                daily_schedules[f"day_{day}"]["summary"]["total_places"] += 1
                
                place_index += 1
            
            # Add evening snack if appropriate
            if current_time.hour >= 16:
                snack_added = any(act['activity'] == 'Evening Snack' for act in daily_schedules[f"day_{day}"]["activities"])
                if not snack_added:
                    daily_schedules[f"day_{day}"]["activities"].append({
                        "time": current_time.strftime('%H:%M'),
                        "activity": "Evening Snack",
                        "type": "meal",
                        "duration_minutes": meal_times['snack']['duration'],
                        "notes": "Light refreshments"
                    })
                    current_time += timedelta(minutes=meal_times['snack']['duration'])
            
            # Add dinner
            if current_time.hour < 19:
                current_time = current_time.replace(hour=19, minute=30)
            
            daily_schedules[f"day_{day}"]["activities"].append({
                "time": current_time.strftime('%H:%M'),
                "activity": "Dinner",
                "type": "meal",
                "duration_minutes": meal_times['dinner']['duration'],
                "notes": "End the day with a delicious meal"
            })
            current_time += timedelta(minutes=meal_times['dinner']['duration'])
            
            # Set estimated end time
            daily_schedules[f"day_{day}"]["summary"]["estimated_end_time"] = current_time.strftime('%H:%M')
        
        return {
            "success": True,
            "total_days": total_days,
            "total_places_scheduled": place_index,
            "daily_schedules": daily_schedules,
            "scheduling_notes": [
                "Times are approximate and can be adjusted based on your preferences",
                "Consider local traffic conditions and weather",
                "Some attractions may have specific opening hours - verify before visiting",
                "Buffer time is included for unexpected delays"
            ]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create daily schedule: {str(e)}"
        }