# transport_agent.py
"""
Transport Agent: Combines flight search (SerpApi) with airport IATA lookup (Google ADK).
Uses gemini-2.5-flash as the reasoning model.
"""

from google.adk.agents import Agent

# Import your tools
from tripmate.tools.flightSearchTool import flights_search
from tripmate.tools.airportIATATool import airport_iata_code_tool
from tripmate.sub_agents.transport.prompt import TRAVEL_AGENT_PROMPT
from tripmate.tools.stationCodeTool import railway_station_code_tool
from tripmate.tools.trainSearchTool import train_search


# Define the Transport Agent
transport_agent = Agent(
    model="gemini-2.5-flash",
    name="TransportAgent",
    description="An agent that helps users search for flights or Train. Resolve IATA or Railway Station Code. Display the responses in a user-friendly format.",
    instruction=TRAVEL_AGENT_PROMPT,
    tools=[airport_iata_code_tool, flights_search, railway_station_code_tool, train_search]
)
