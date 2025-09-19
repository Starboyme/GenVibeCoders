PROMPT = "You are a helpful travel assistant. \
  You have access to the following tools: \
  - gather_places: To gather popular places in and around a destination. \
  - build_distance_matrix: To build a distance/time matrix between all given places. \
  - solve_tsp_with_fixed_start_end: To solve the Traveling Salesman Problem (TSP) with a fixed start and end point. \
  Use these tools to help users plan their trips effectively. \
  When suggesting places, consider the number of days for the trip to adjust the number of places returned: \
    - <= 2 days → return up to 5 nearby highlights \
    - <= 5 days → return up to 10 places \
    - > 5 days  → return up to 20 places \
  If there are too many places to cover within the given region, pick up a random places that can be covered in the given days. \
  Do not ask extra questions to the user. \
  Ensure that the itinerary is optimized for travel time using the distance matrix and TSP solver. \
  The starting point is usually the accommodation or a major landmark in the destination. \
  Always provide the following details for each place: name, address, latitude, longitude, type, and rating (if available). \
  Provide the final itinerary in a clear and organized manner. Which can be passed on to other systems for further processing."
  
from os import getenv
from dotenv import load_dotenv

from tools.gather_places import gather_places
from tools.routing_tool import solve_tsp_with_fixed_start_end, build_distance_matrix
load_dotenv()

from langchain_google_vertexai import ChatVertexAI

llm = ChatVertexAI(model_name="gemini-2.5-flash")
tools = [gather_places, build_distance_matrix, solve_tsp_with_fixed_start_end]

llm_with_tools = llm.bind_tools(tools)

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
    
async def format_final(state: State):
    # Take the last LLM message
    last_msg = state["messages"][-1]
    # Wrap it in a clean final AI message
    return {"messages": [AIMessage(content=f"Here’s your optimized itinerary:\n\n{last_msg.content}")]}

workflow = StateGraph(State)

workflow.add_node("tool_calling_llm", tool_calling_llm)
workflow.add_node("tools", ToolNode(tools), emit_messages=True)
workflow.add_node("format_final", format_final)

workflow.add_edge(START, "tool_calling_llm")
workflow.add_conditional_edges("tool_calling_llm", tools_condition, ["tools", END])
workflow.add_edge("tools", "tool_calling_llm")
workflow.add_edge("tool_calling_llm", "format_final")
workflow.add_edge("format_final", END)

graph = workflow.compile()


async def run():
  initial_state: State = {
    "messages": [SystemMessage(content=PROMPT)]
  }
  query = "I'm planning a 3-day trip to Coorg. Suggest an itinerary covering popular places to visit."
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
          # Only print the final formatted answer
          print("\n\n--- Final Answer ---\n")
          print("  output:", event["data"]["output"])

        elif kind == "on_chain_end":
            print("\n\n=== Graph Finished ===\n")
  
  print("\nEvents:", events)
  