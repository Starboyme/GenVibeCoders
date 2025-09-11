from google.adk.agents.callback_context import CallbackContext
import json
import os

from tripmate.library import constants
from datetime import datetime
from typing import Dict, Any
from google.adk.sessions.state import State

SAMPLE_SCENARIO_PATH = os.getenv("TRIPMATE_SCENARIO","tripmate/profiles/itinerary_empty_default.json")

def _set_initial_states(source: Dict[str, Any], target: State | dict[str, Any]):
    """
    Setting the initial session state given a JSON object of states.

    Args:
        source: A JSON object of states.
        target: The session state object to insert into.
    """
    if constants.SYSTEM_TIME not in target:
        target[constants.SYSTEM_TIME] = str(datetime.now())

    if constants.ITIN_INITIALIZED not in target:
        target[constants.ITIN_INITIALIZED] = True

        target.update(source)

        trip_metadata = source.get(constants.TRMD_KEY, {})
        if trip_metadata:
            target[constants.ITIN_START_DATE] = trip_metadata.get(constants.ITIN_START_DATE, "")
            target[constants.ITIN_END_DATE] = trip_metadata.get(constants.ITIN_END_DATE, "")
            target[constants.ITIN_DATETIME] = trip_metadata.get(constants.ITIN_DATETIME, "")

def _load_precreated_itinerary(callback_context: CallbackContext):
    """
    Sets up the initial state.
    Set this as a callback as before_agent_call of the root_agent.
    This gets called before the system instruction is contructed.

    Args:
        callback_context: The callback context.
    """    
    data = {}
    with open(SAMPLE_SCENARIO_PATH, "r") as file:
        data = json.load(file)
        print(f"\nLoading Initial State: {data}\n")

    _set_initial_states(data["state"], callback_context.state)

def _load_state_from_memory(callback_context: CallbackContext):
    """
    Loads the state from memory.
    Set this as a callback as before_agent_call of the specialized agents.
    This gets called before the system instruction is contructed.

    Args:
        callback_context: The callback context.
    """    
    memory = callback_context.agent.memory
    if memory is not None:
        mem_state = memory.get_state()
        print(f"\nLoading State from Memory: {mem_state}\n")
        _set_initial_states(mem_state, callback_context.state)