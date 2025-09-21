# transport_agent.py
"""
Hotel Agent: Uses Google Hotels API (SerpApi).
Uses gemini-2.5-flash as the reasoning model.
"""

from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp

from tools.hotelSearchTool import hotels_search
from nodes.hotel_agent.prompt import HOTEL_AGENT_PROMPT


# Define the Hotel Agent
_hotel_agent = Agent(
    model="gemini-2.5-flash",
    name="HotelAgent",
    description="An agent that helps users search for hotels if given a location. Display the responses in a user-friendly format.",
    instruction=HOTEL_AGENT_PROMPT,
    tools=[hotels_search],
)
hotel_agent = AdkApp(agent=_hotel_agent)