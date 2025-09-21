# transport_agent.py
"""
Hotel Agent: Uses Google Hotels API (SerpApi).
Uses gemini-2.5-flash as the reasoning model.
"""

from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

# Import your tools
from tripmate.tools.hotelSearchTool import hotels_search
from tripmate.sub_agents.hotel.prompt import HOTEL_AGENT_PROMPT


# Define the Hotel Agent
hotel_agent = Agent(
    model="gemini-2.5-flash",
    name="HotelAgent",
    description="An agent that helps users search for hotels if given a location. Display the responses in a user-friendly format.",
    instruction=HOTEL_AGENT_PROMPT,
    tools=[hotels_search],
)
