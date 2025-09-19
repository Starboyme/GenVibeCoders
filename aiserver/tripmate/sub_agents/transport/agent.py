# transport_agent.py
"""
Transport Agent: Combines flight search (SerpApi) with airport IATA lookup (Google ADK).
Uses gemini-2.5-flash as the reasoning model.
"""

from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

# Import your tools
from tripmate.tools.transportTool import flights_search
from tripmate.tools.airportTool import airport_iata_code_tool
from tripmate.sub_agents.transport.prompt import TRAVEL_AGENT_PROMPT



# # Wrap flights_search in an AgentTool so ADK agents can call it
# flights_search_tool = AgentTool(
#     flights_search,

# )


# Define the Transport Agent
transport_agent = Agent(
    model="gemini-2.5-flash",
    name="TransportAgent",
    description="An agent that helps users search for flights and resolve IATA airport codes. Display the responses in a user-friendly format.",
    instruction=TRAVEL_AGENT_PROMPT,
    tools=[airport_iata_code_tool, flights_search],
)
