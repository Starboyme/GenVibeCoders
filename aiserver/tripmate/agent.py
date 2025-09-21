from google.adk.agents import Agent
from . import prompt
from tripmate.tools.memory import _load_precreated_itinerary
from tripmate.sub_agents.hotel.agent import hotel_agent
from dotenv import load_dotenv

#subAgents
from tripmate.sub_agents.transport.agent import transport_agent
load_dotenv()

root_agent = Agent(
    model='gemini-2.5-flash',
    name='tripmate_agent',
    description='A helpful assistant for user questions.',
    instruction=prompt.ROOT_AGENT_INSTRUCTION,
    sub_agents=[
        transport_agent,
        hotel_agent
    ],
    # before_agent_callback=_load_precreated_itinerary,
)