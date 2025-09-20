# stationCodeTool.py
"""Tool to get Railway Station Codes using a custom agent with Google Search"""
from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

from google.adk.tools.google_search_tool import google_search

_station_code_agent = Agent(
    model="gemini-2.5-flash",
    name="TrainStationCodeAgent",
    description="An agent that provides STATION CODE for railway stations in India Only.",
    instruction="""
    You are expert in Railway Station Codes. You can provide the Railway station code for any railway station in India based on its name or location.
    If you are given a Railway station name, return the corresponding Railway Station Code.
    If you are given a city or location, return the primary Railway Station Code serving that area.
    If you cannot find the Railway Station Code, respond with "Railway Station Code not found".
    Always respond in the format: "<Railway Station Code or not found message>".
    """,
    tools=[google_search],
)

railway_station_code_tool = AgentTool(agent=_station_code_agent)