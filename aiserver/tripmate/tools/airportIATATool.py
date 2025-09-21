#airportTool.py
"""Tool to get IATA codes for airports using a custom agent with Google Search."""
from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

from google.adk.tools.google_search_tool import google_search

_search_agent = Agent(
    model="gemini-2.5-flash",
    name="AirportIATACodeAgent",
    description="An agent that provides IATA codes for airports worldwide.",
    instruction="""
    You are an expert in IATA Airport Codes. You can provide the IATA code for any airport worldwide based on its name or location.
    If you are given a airport name, return the corresponding IATA code.
    If you are given a city or location, return the IATA code of the primary airport serving that area.
    If you cannot find the IATA code, respond with "IATA code not found".
    Always respond in the format: "<IATA code or not found message>".
    """,
    tools=[google_search],
)

airport_iata_code_tool = AgentTool(agent=_search_agent)