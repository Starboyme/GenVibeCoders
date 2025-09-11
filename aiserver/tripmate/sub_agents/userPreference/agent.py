from google.adk.agents import Agent
from . import prompt

from tripmate.tools.memory import _load_state_from_memory

userPreferenceAgent = Agent(
    model='gemini-2.5-flash',
    name='user_preference_agent',
    description='An agent to handle user preferences for trip planning.',
    instruction=prompt.USER_INSTR,
    before_agent_callback=_load_state_from_memory
)