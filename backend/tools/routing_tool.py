import requests
import os
from dotenv import load_dotenv
from langchain.tools import tool
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

load_dotenv()

API_KEY = os.getenv("GPLACES_API_KEY")

PLACES_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"

@tool()
def get_places_lat_lng(query: str, api_key: str = API_KEY, limit: int = 10):
    """
    Get a list of places (name + lat,lng + Google Maps link) from Places API v1 using a query.
    
    Args:
        query (str): Search query like "temples in Bangalore".
        api_key (str): Google Cloud API Key.
        limit (int): Number of places to return (default 10).
    
    Returns:
        list of dict with name, lat, lng, location_link, and place_id
    """
    url = PLACES_SEARCH_URL
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.id"
    }
    
    body = {
        "textQuery": query,
        "pageSize": limit
    }
    
    resp = requests.post(url, headers=headers, json=body)
    resp.raise_for_status()
    
    data = resp.json()
    results = []
    
    for place in data.get("places", []):
        results.append({
            "name": place["displayName"]["text"],
            "address": place.get("formattedAddress"),
            "lat": place["location"]["latitude"],
            "lng": place["location"]["longitude"],
            "place_id": place["id"],
            "location_link": f"https://www.google.com/maps/search/?api=1&query={place['location']['latitude']},{place['location']['longitude']}"
        })
    
    return results

ROUTES_ENDPOINT = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"

@tool()
def build_distance_matrix(places: list, api_key: str = API_KEY, travel_mode: str = "DRIVE"):
    """
    Build a distance/time matrix between all given places using Google Routes API v2.
    
    Args:
        places (list): List of dicts with at least {"lat", "lng"} (from get_places_lat_lng).
        api_key (str): Google Cloud API Key.
        travel_mode (str): "DRIVE", "WALK", "BICYCLE", "TRANSIT" (default DRIVE).
    
    Returns:
        dict with distance_matrix[origin_index][destination_index] = {distance_meters, duration_seconds}
    """
    
    url = ROUTES_ENDPOINT
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "originIndex,destinationIndex,duration,distanceMeters"
    }
    
    origins = [{"waypoint": {"location": {"latLng": {"latitude": p["lat"], "longitude": p["lng"]}}}} for p in places]
    destinations = [{"waypoint": {"location": {"latLng": {"latitude": p["lat"], "longitude": p["lng"]}}}} for p in places]
    
    body = {
        "origins": origins,
        "destinations": destinations
    }
    # print(json.dumps(body))
    
    resp = requests.post(url, headers=headers,  json=body)
    resp.raise_for_status()
    
    data = resp.json()
    
    # Initialize matrix
    n = len(places)
    matrix = [[None] * n for _ in range(n)]
    
    for row in data:
        o = row["originIndex"]
        d = row["destinationIndex"]

        # duration may come as "123s" (string)
        duration_str = row.get("duration", "0s")
        duration_seconds = int(duration_str.replace("s", "")) if isinstance(duration_str, str) else 0

        matrix[o][d] = {
            "distance_meters": row.get("distanceMeters", 0),
            "duration_seconds": duration_seconds
        }
    
    return matrix

@tool()
def solve_tsp_with_fixed_start_end(distance_matrix, start_index, end_index=None):
    """
    Solve TSP with OR-Tools given a distance matrix.
    Fix start, optionally fix end.

    Args:
        distance_matrix (list[list[dict]]): NxN matrix where matrix[i][j]["duration_seconds"] or ["distance_meters"].
        start_index (int): index of start node (e.g., airport).
        end_index (int or None): index of end node. If None, same as start.

    Returns:
        (route, route_distance): route is a list of indices.
    """

    size = len(distance_matrix)

    # Convert to plain int cost matrix
    cost_matrix = [
        [distance_matrix[i][j]["duration_seconds"] if distance_matrix[i][j] else 999999
         for j in range(size)]
        for i in range(size)
    ]

    # --- FIX: use starts/ends as lists ---
    if end_index is None:
        end_index = start_index
    manager = pywrapcp.RoutingIndexManager(size, 1, [start_index], [end_index])

    routing = pywrapcp.RoutingModel(manager)

    # Callback to return travel time
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return cost_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Search parameters
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.FromSeconds(5)

    # Solve
    solution = routing.SolveWithParameters(search_parameters)
    if not solution:
        return None, None

    # Extract route
    route = []
    index = routing.Start(0)
    route_distance = 0

    while not routing.IsEnd(index):
        node = manager.IndexToNode(index)
        route.append(node)
        previous_index = index
        index = solution.Value(routing.NextVar(index))
        route_distance += routing.GetArcCostForVehicle(previous_index, index, 0)

    route.append(manager.IndexToNode(index))  # add end

    return route, route_distance
