PROMPT = "You are a helpful assistant that helps people find airports in the given list of cities. \
  You have access to get_airports tool to get information about airports. \
  Determine whether the airport is domestic/international using the 'type' field from API response \
  There may be multiple entries for the same airport in the response from the tool, \
  look at the address, latitude and longitude to figure out duplicates and include only unique in the response \
  The response should be in a format with the following keys: \
  - name: The name of the airport. \
  - city: The city where the airport is located. \
  - country: The country where the airport is located. \
  - coordinates: The latitude and longitude of the airport. \
  - domestic_flights: A boolean indicating if the airport has domestic flights. \
  - international_flights: A boolean indicating if the airport has international flights."
  
from os import getenv
from dotenv import load_dotenv

from tools.airports_tool import get_airports
load_dotenv()

from langchain_google_vertexai import ChatVertexAI

llm = ChatVertexAI(model_name="gemini-2.5-flash")

llm_with_tools = llm.bind_tools([get_airports])

from typing_extensions import Annotated, TypedDict
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage, AIMessage
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
  messages: Annotated[list[AnyMessage], add_messages]

async def tool_calling_llm(state: State):
  async for chunk in llm_with_tools.astream(state["messages"]):
    yield {"messages": [chunk]}

workflow = StateGraph(State)

workflow.add_node("tool_calling_llm", tool_calling_llm)
workflow.add_node("tools", ToolNode([get_airports]))

workflow.add_edge(START, "tool_calling_llm")
workflow.add_conditional_edges("tool_calling_llm", tools_condition, ["tools", END])
workflow.add_edge("tools", "tool_calling_llm")

graph = workflow.compile()


async def run():
  initial_state: State = {
    "messages": [SystemMessage(content=PROMPT)]
  }
  query = "airports in bangalore"
  state = initial_state.copy()
  state["messages"].append(HumanMessage(content=query))
  events = set()
  async for event in graph.astream_events(state, version="v1"):
        kind = event["event"]
        events.add(kind)
        
        # print(event)

        if kind == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            if hasattr(chunk, "content") and chunk.content:
                print(chunk.content, end="", flush=True)

        elif kind == "on_tool_start":
            print("\n\n[Tool started]", event["name"])
            print("  input:", event["data"]["input"])

        elif kind == "on_tool_end":
            print("\n[Tool result]")
            print("  output:", event["data"]["output"])

        elif kind == "on_chat_model_end":
            print("\n\n--- Model Finished ---\n")

        elif kind == "on_chain_end":
            print("\n\n=== Graph Finished ===\n")
  
  print("\nEvents:", events)
  