# transport_agent.py
"""
Transport Agent: Combines flight search (SerpApi) with airport IATA lookup (Google ADK).
Uses gemini-2.5-flash as the reasoning model.
"""

from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp

# Import your tools
from tools.flightSearchTool import flights_search
from tools.airportIATATool import airport_iata_code_tool
from nodes.transport.prompt import TRAVEL_AGENT_PROMPT
from tools.stationCodeTool import railway_station_code_tool
from tools.trainSearchTool import train_search


# Define the Transport Agent
_transport_agent = Agent(
    model="gemini-2.5-flash",
    name="TransportAgent",
    description="An agent that helps users search for flights or Train. Resolve IATA or Railway Station Code. Display the responses in a user-friendly format.",
    instruction=TRAVEL_AGENT_PROMPT,
    tools=[airport_iata_code_tool, flights_search, railway_station_code_tool, train_search]
)

transport_agent = AdkApp(agent=_transport_agent)
# transport_agent.async_stream_query(user_id="langgraph", message="")