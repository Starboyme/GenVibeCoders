import requests
from os import getenv
from dotenv import load_dotenv
from langchain.tools import tool

load_dotenv()

PLACES_ENDPOINT = "https://maps.googleapis.com/maps/api/place/textsearch/json"
GPLACES_API_KEY = getenv("GPLACES_API_KEY")

@tool()
def get_airports(destination: str, days: int = 3):
  """
  Gather airports in and around a destination using the Google Places API.

  Args:
    destination (str): The name of the destination city or region (e.g., "Manali", "Coorg").
    days (int) [Optional]: Number of trip days. Used to adjust the number of places returned:
      - <= 2 days → return up to 5 nearby highlights
      - <= 5 days → return up to 10 places
      - > 5 days  → return up to 20 places

  Returns a compact list of dicts with only:
    - name (str)
    - address (str)
    - latitude (float)
    - longitude (float)
    - type (list of str)
  """
  results = []

  # 1. Google Places API
  params = {
      "query": f"operational airports in {destination}",
      "key": GPLACES_API_KEY
  }
  try:
    resp = requests.get(PLACES_ENDPOINT, params=params).json()
  except Exception as e:
    print("Error calling Google Places API:", e)
  
  for place in resp.get("results", []):
    if (place.get("business_status") != "OPERATIONAL" or
        "airport" not in place.get("types", [])):
      continue
    results.append({
      "name": place.get("name"),
      "address": place.get("formatted_address"),
      "lat": place.get("geometry", {}).get("location", {}).get("lat"),
      "lng": place.get("geometry", {}).get("location", {}).get("lng"),
      "type": place.get("types", [])
    })

  return results