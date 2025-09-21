from langgraph.graph import StateGraph, END
from nodes.transport.agent import transport_agent
from langchain_core.messages import BaseMessage, HumanMessage
from typing import TypedDict, Annotated, List
import operator
import asyncio # For running the async code

# Define the state of the graph
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    user_query: str

async def call_transport_agent_node(state: AgentState):
    """
    LangGraph node function that interacts with the Google ADK agent via AdkApp.
    """
    print("---CALLING ADK AGENT VIA ADKAPP---")

    # Get the latest user message from the state
    user_message = state['messages'][-1].content

    # The user ID is required for a session. It could be from a user session ID in your application.
    user_id = "langgraph-user-123"

    # Use the async_stream_query method to interact with the agent.
    # This is a better practice as it allows for handling streaming responses.
    # You'll collect all parts of the response from the stream.
    agent_response_text = ""
    async for event in transport_agent.async_stream_query(
        user_id=user_id,
        message=user_message,
    ):
        # Extract the text from the event. The structure might vary.
        # This is a common way to get the final text from a streamed response.
        # print(event)
        # if event.get('text'):
        #     agent_response_text += event.get('text')
        try:
          chunks = event['content']['parts']
          for chunk in chunks:
            agent_response_text += chunk['text']
        except Exception as e:
          pass

    # Return the updated state with the agent's final response
    return {"messages": [HumanMessage(content=agent_response_text)]}

# Initialize the StateGraph with the AgentState
workflow = StateGraph(AgentState)

# Add the new node to the graph
workflow.add_node("transport_agent_node", call_transport_agent_node)

# Set the entry and end points for the graph
workflow.set_entry_point("transport_agent_node")
workflow.add_edge("transport_agent_node", END)

# Compile the graph
app = workflow.compile()

# The initial state for the graph
initial_state = {
    "messages": [HumanMessage(content="Find me flights from Chennai to Mumbai on 25th September 2025.")],
}

# Run the graph
async def run():
    result = await app.ainvoke(initial_state)
    print(result)
