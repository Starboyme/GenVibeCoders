from google.adk.agents import Agent
from . import prompt
from tripmate.tools.memory import _load_precreated_itinerary
from dotenv import load_dotenv
load_dotenv()

root_agent = Agent(
    model='gemini-2.5-flash',
    name='tripmate_agent',
    description='A helpful assistant for user questions.',
    instruction=prompt.ROOT_AGENT_INSTRUCTION,
    before_agent_callback=_load_precreated_itinerary,
)