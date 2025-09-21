from state import TravelState
from base_llm import llm
from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.prebuilt import ToolNode


# tools
from tools.routing_tool import solve_tsp_with_fixed_start_end, build_distance_matrix


matrix_prompt = ChatPromptTemplate.from_messages([
        ("human", """You are a distance matrix generator. Calculate travel distances/times between all places.

Places to process: {num_places} places
Destination: {destination}

Use the build_distance_matrix tool with the places from the previous step.""")
    ])


async def distance_matrix_agent(state: TravelState):
    """
    Generates distance matrix between places
    """
    print("DISTANCE MATRIX: Calculating distances...")
    
    if not state.get("places"):
        return {
            "messages": [AIMessage(content="No places available for distance calculation")],
            "next_step": "synthesizer"
        }
    
    
    tools = [build_distance_matrix]
    matrix_chain = matrix_prompt | llm.bind_tools(tools)
    
    try:
        response = await matrix_chain.ainvoke({
            "num_places": len(state["places"]),
            "destination": state["destination"]
        })
        
        return {
            "messages": [response],
            "next_step": "execute_distance_matrix"
        }
        
    except Exception as e:
        print(f"Distance matrix error: {e}")
        return {
            "messages": [AIMessage(content=f"Error calculating distances: {e}")],
            "next_step": "generate_route"
        }
        
async def execute_distance_matrix(state: TravelState):
    """Execute distance matrix calculation"""
    print("Executing distance matrix calculation...")
    
    # Create tool node with the places from state
    tool_node = ToolNode([build_distance_matrix])
    
    # Manually invoke the tool with places
    try:
        result = await build_distance_matrix.ainvoke({"places": state["places"]})
        
        distance_matrix = result
        
        print(f"Distance matrix calculated: {len(distance_matrix)}x{len(distance_matrix) if distance_matrix else 0}")
        
        return {
            "messages": [ToolMessage(content=str(result), tool_call_id="distance_matrix")],
            "distance_matrix": distance_matrix,
            "next_step": "generate_route"
        }
        
    except Exception as e:
        print(f"Distance matrix execution error: {e}")
        return {
            "messages": [AIMessage(content=f"Distance calculation failed: {e}")],
            "next_step": "generate_route"
        }
        
async def route_optimizer_agent(state: TravelState):
    """
    Optimizes the route using TSP solver
    """
    print("🗺️ ROUTE OPTIMIZER: Finding optimal route...")
    
    if not state.get("places") or not state.get("distance_matrix"):
        return {
            "messages": [AIMessage(content="Missing places or distance matrix for route optimization")],
            "next_step": "synthesizer"
        }
    
    try:
        route, total_time = await solve_tsp_with_fixed_start_end.ainvoke({
            "distance_matrix": state["distance_matrix"],
            "start_index": 0,
            "end_index": 1
        })
        
        optimal_route = []
        places = state["places"]
        for idx in route:
          optimal_route.append(places[idx])
        
        print(f"✅ Route optimized: {len(optimal_route)} places in order")
        
        return {
            "messages": [ToolMessage(content=str(optimal_route), tool_call_id="route_optimizer")],
            "optimal_route": optimal_route,
            "next_step": "schedule_visits"
        }
        
    except Exception as e:
        print(f"❌ Route optimization error: {e}")
        return {
            "messages": [AIMessage(content=f"Route optimization failed: {e}")],
            "next_step": "schedule_visits"
        }