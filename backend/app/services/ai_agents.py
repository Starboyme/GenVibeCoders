import os
import json
import re
import asyncio
from typing import Dict, Any, List, Optional, Union
from vertexai.generative_models import GenerativeModel, ChatSession
from urllib.parse import quote_plus


# ------------------------------
# Helpers
# ------------------------------
def safe_json_parse(response: Union[str, Dict, List], expect_list: bool = False) -> Union[List, Dict]:
    """Parse and normalize JSON responses from the LLM."""
    if isinstance(response, (dict, list)):
        parsed = response
    else:
        try:
            cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", str(response), flags=re.DOTALL).strip()
            parsed = json.loads(cleaned)
        except Exception as e:
            print(f"safe_json_parse error: {e}, response={response}")
            return [] if expect_list else {}

    # Normalize
    if expect_list:
        if isinstance(parsed, dict):
            return [parsed]
        if isinstance(parsed, list):
            return parsed
        return []
    else:
        if isinstance(parsed, list) and parsed:
            return parsed[0]  # take first element if list given instead of dict
        if isinstance(parsed, dict):
            return parsed
        return {}


def generate_maps_link(name: str) -> str:
    """Generate a Google Maps search link for a given place name."""
    if not name:
        return ""
    return f"https://www.google.com/maps/search/{quote_plus(name)}"


# ------------------------------
# TravelLLMAgent
# ------------------------------
class TravelLLMAgent:
    """Wrapper around Vertex AI Gemini for structured trip planning responses."""

    def __init__(self, model_name: str = None) -> None:
        self.model_name = model_name or os.getenv("GOOGLE_GEMINI_MODEL", "gemini-2.5-flash-lite")
        self.model = GenerativeModel(self.model_name)
        self.chat: Optional[ChatSession] = None

    async def generate(self, prompt: str) -> Union[Dict[str, Any], List[Any]]:
        if os.getenv("MOCK_AI", "false").lower() == "true":
            return self._mock_llm_response(prompt)

        if not self.chat:
            self.chat = self.model.start_chat()

        response = await self.chat.send_message_async(prompt)
        response_text = ""
        try:
            response_text = response.candidates[0].content.parts[0].text.strip()
            print("Raw LLM response >>>", repr(response_text))  # Debug log

            cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", response_text, flags=re.DOTALL).strip()
            return json.loads(cleaned)
        except Exception as e:
            print("LLM Response Parse Error:", e)
            return {
                "error": "Failed to parse AI response",
                "raw": response_text or str(response),
            }

    def _mock_llm_response(self, prompt: str) -> Dict[str, Any]:
        """Return a mock response that matches the expected JSON schema."""
        return {
            "itinerary": [
                {
                    "day": "1",
                    "cost": "7000",
                    "stay": {
                        "name": "Mock Resort",
                        "cost": "5000",
                        "contact": "+91-1234567890",
                        "location_link": generate_maps_link("Mock Resort")
                    },
                    "itineraryText": "Day 1: Stay at Mock Resort, visit Baga Beach and enjoy seafood.",
                    "activities": [
                        {
                            "name": "Baga Beach",
                            "description": "Relax at the most famous beach in Goa.",
                            "cost": "0",
                            "location_link": generate_maps_link("Baga Beach")
                        }
                    ],
                    "food": [
                        {
                            "name": "Fisherman's Wharf",
                            "description": "Enjoy authentic Goan seafood.",
                            "cost": "2000",
                            "location_link": generate_maps_link("Fisherman's Wharf")
                        }
                    ]
                }
            ]
        }


# ------------------------------
# Base Agent
# ------------------------------
class BaseAgent:
    def __init__(self, llm: TravelLLMAgent):
        self.llm = llm

    async def generate(self, prompt: str) -> Dict[str, Any]:
        return await self.llm.generate(prompt)


# ------------------------------
# Specialized Agents
# ------------------------------
class ItineraryAgent(BaseAgent):
    async def generate(self, trip: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
You are a travel planner AI.
Generate an initial day-wise trip outline for the following trip:

{json.dumps(trip, indent=2)}

Return ONLY valid JSON in this schema (no markdown, no comments):

{{
  "itinerary": [
    {{
      "day": "1",
      "cost": "0",
      "stay": {{
        "name": "",
        "cost": "0",
        "contact": "",
        "location_link": ""
      }},
      "itineraryText": "",
      "activities": [],
      "food": []
    }}
  ]
}}
"""
        return await self.llm.generate(prompt)


class StayAgent(BaseAgent):
    async def recommend(self, trip: Dict[str, Any], day: int) -> Dict[str, Any]:
        prompt = f"""
Recommend one hotel/resort for Day {day} of this trip:

{json.dumps(trip, indent=2)}

Return ONLY valid JSON (no markdown):
{{
  "name": "Stay Name",
  "cost": "5000",
  "contact": "+91-1234567890",
  "location_link": "https://maps.example.com/stay"
}}
"""
        raw = await self.llm.generate(prompt)
        stay = safe_json_parse(raw, expect_list=False)
        stay["location_link"] = generate_maps_link(stay.get("name", ""))
        return stay


class ActivityAgent(BaseAgent):
    async def recommend(self, trip: Dict[str, Any], day: int) -> List[Dict[str, Any]]:
        prompt = f"""
Recommend 2-3 activities for Day {day} of this trip:

{json.dumps(trip, indent=2)}

Return ONLY a valid JSON array (no markdown):
[
  {{
    "name": "Activity Name",
    "description": "Why this activity is great",
    "cost": "1000",
    "location_link": "https://maps.example.com/activity"
  }}
]
"""
        raw = await self.llm.generate(prompt)
        activities = safe_json_parse(raw, expect_list=True)
        for a in activities:
            a["location_link"] = generate_maps_link(a.get("name", ""))
        return activities


class FoodAgent(BaseAgent):
    async def recommend(self, trip: Dict[str, Any], day: int) -> List[Dict[str, Any]]:
        prompt = f"""
Recommend 2-3 restaurants/food experiences for Day {day} of this trip:

{json.dumps(trip, indent=2)}

Return ONLY a valid JSON array (no markdown):
[
  {{
    "name": "Restaurant Name",
    "description": "Why this food experience is great",
    "cost": "1500",
    "location_link": "https://maps.example.com/food"
  }}
]
"""
        raw = await self.llm.generate(prompt)
        food = safe_json_parse(raw, expect_list=True)
        for f in food:
            f["location_link"] = generate_maps_link(f.get("name", ""))
        return food


# ------------------------------
# Orchestrator
# ------------------------------
class AiAgentService:
    """High-level service orchestrating multiple specialized agents."""

    def __init__(self, llm: Optional[TravelLLMAgent] = None) -> None:
        self.llm = llm or TravelLLMAgent()
        self.itinerary_agent = ItineraryAgent(self.llm)
        self.stay_agent = StayAgent(self.llm)
        self.activity_agent = ActivityAgent(self.llm)
        self.food_agent = FoodAgent(self.llm)

    async def plan_trip_agents(self, trip: Dict[str, Any]) -> Dict[str, Any]:
        base_itinerary = await self.itinerary_agent.generate(trip)
        days = [int(d.get("day", idx + 1)) for idx, d in enumerate(base_itinerary.get("itinerary", []))]

        final_days: List[Dict[str, Any]] = []

        async def process_day(day: int):
            stay = await self.stay_agent.recommend(trip, day)
            activities = await self.activity_agent.recommend(trip, day)
            food = await self.food_agent.recommend(trip, day)

            # Normalize costs
            stay_cost = int(stay.get("cost", "0"))
            activities_cost = sum(int(a.get("cost", "0")) for a in activities)
            food_cost = sum(int(f.get("cost", "0")) for f in food)
            total_cost = stay_cost + activities_cost + food_cost

            final_days.append({
                "day": str(day),
                "cost": str(total_cost),
                "stay": stay,
                "itineraryText": (
                    f"Day {day}: Stay at {stay.get('name', 'TBD')} and enjoy "
                    f"{', '.join(a.get('name','') for a in activities)}. "
                    f"Meals at {', '.join(f.get('name','') for f in food)}."
                ),
                "activities": activities,
                "food": food
            })

        await asyncio.gather(*(process_day(d) for d in days))

        return {"itinerary": sorted(final_days, key=lambda x: int(x["day"]))}
