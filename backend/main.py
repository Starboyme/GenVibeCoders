# from fastapi import FastAPI
# from fastapi.responses import StreamingResponse
import asyncio

from dotenv import load_dotenv
from tools.schedule_tool import create_daily_schedule
load_dotenv()

from langchain_core.messages import AIMessage, ToolMessage
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import StateGraph, START, END
from typing import List, Dict, Any
from state import TravelState

from langchain.prompts import ChatPromptTemplate
from base_llm import llm

# Import nodes
from nodes.orchestrator import orchestrator_agent
from nodes.places import gather_places_agent, execute_gather_places
from nodes.transport import travel_planner_agent
from nodes.routes import distance_matrix_agent, execute_distance_matrix, route_optimizer_agent
from nodes.scheduler import visit_scheduler_agent
from nodes.synthesizer import synthesizer_agent
from nodes.accomodation import accommodation_agent


def route_next_step(state: TravelState):
    """Route to the next appropriate step with new agents"""
    next_step = state.get("next_step", "orchestrator")
    
    # Additional validation for new flow
    if next_step == "plan_travel" and not state.get("origin"):
        next_step = "gather_places"
    elif next_step == "gather_places" and not state.get("places"):
        # Normal flow continues
        pass
    elif next_step == "suggest_stays" and not (state.get("places") or state.get("optimal_route")):
        next_step = "gather_places"  # Need places first
    elif next_step == "generate_distance_matrix" and not state.get("places"):
        next_step = "synthesizer"
    elif next_step == "generate_route" and not state.get("places"):
        next_step = "synthesizer"
    elif next_step == "schedule_visits" and not (state.get("optimal_route") or state.get("places")):
        next_step = "synthesizer"
    
    print(f"🧭 Routing to: {next_step}")
    return next_step

def build_multi_agent_graph():
    """Build the multi-agent travel planning graph with new agents"""
    
    workflow = StateGraph(TravelState)
    
    # Add all agent nodes (existing + new)
    workflow.add_node("orchestrator", orchestrator_agent)
    workflow.add_node("plan_travel", travel_planner_agent)  # NEW
    workflow.add_node("gather_places", gather_places_agent)
    workflow.add_node("execute_gather_places", execute_gather_places)
    workflow.add_node("generate_distance_matrix", distance_matrix_agent)
    workflow.add_node("execute_distance_matrix", execute_distance_matrix)
    workflow.add_node("generate_route", route_optimizer_agent)
    workflow.add_node("schedule_visits", visit_scheduler_agent)
    workflow.add_node("suggest_stays", accommodation_agent)  # NEW
    workflow.add_node("synthesizer", synthesizer_agent)
    
    # Start with orchestrator
    workflow.add_edge(START, "orchestrator")
    
    # Add conditional routing from each node
    workflow.add_conditional_edges(
        "orchestrator",
        route_next_step,
        {
            "plan_travel": "plan_travel",  # NEW
            "gather_places": "gather_places",
            "synthesizer": "synthesizer",
            "generate_distance_matrix": "generate_distance_matrix",
            "generate_route": "generate_route",
            "schedule_visits": "schedule_visits",
            "suggest_stays": "suggest_stays"  # NEW
        }
    )
    
    # NEW: Travel planner routing
    workflow.add_conditional_edges(
        "plan_travel",
        route_next_step,
        {
            "gather_places": "gather_places",
            "synthesizer": "synthesizer"
        }
    )
    
    workflow.add_conditional_edges(
        "gather_places",
        route_next_step,
        {
            "execute_gather_places": "execute_gather_places",
            "synthesizer": "synthesizer"
        }
    )
    
    workflow.add_conditional_edges(
        "execute_gather_places",
        route_next_step,
        {
            "generate_distance_matrix": "generate_distance_matrix",
            "synthesizer": "synthesizer"
        }
    )
    
    workflow.add_conditional_edges(
        "generate_distance_matrix", 
        route_next_step,
        {
            "execute_distance_matrix": "execute_distance_matrix",
            "generate_route": "generate_route",
            "synthesizer": "synthesizer"
        }
    )
    
    workflow.add_conditional_edges(
        "execute_distance_matrix",
        route_next_step,
        {
            "generate_route": "generate_route",
            "synthesizer": "synthesizer"
        }
    )
    
    workflow.add_conditional_edges(
        "generate_route",
        route_next_step,
        {
            "schedule_visits": "schedule_visits",
            "synthesizer": "synthesizer"
        }
    )
    
    workflow.add_conditional_edges(
        "schedule_visits",
        route_next_step,
        {
            "suggest_stays": "suggest_stays",  # NEW: After schedule, suggest accommodations
            "synthesizer": "synthesizer"
        }
    )
    
    # NEW: Accommodation agent routing
    workflow.add_conditional_edges(
        "suggest_stays",
        route_next_step,
        {
            "synthesizer": "synthesizer"
        }
    )
    
    workflow.add_conditional_edges(
        "synthesizer",
        route_next_step,
        {
            "END": END
        }
    )
    
    return workflow.compile()
  
def create_initial_state_with_origin(destination: str, origin: str = None, days: int = 3, theme: str = "general"):
    """Helper to create initial state with origin support"""
    return {
        "days": days,
        "start_date": "September 20 2025",
        "end_date": "September 25 2025",
        "destination": destination,
        "origin": origin,  # NEW
        "theme": theme,
        "user_query": f"Plan a {days}-day {theme} trip to {destination}" + (f" from {origin}" if origin else ""),
        "messages": [],
        "query_type": "",
        "next_step": "orchestrator",
        "places": None,
        "original_places": None,
        "distance_matrix": None,
        "optimal_route": None,
        "daily_schedule": None,
        "travel_info": None,  # NEW
        "accommodations": None,  # NEW
        "effective_days": None  # NEW
    }

graph = build_multi_agent_graph()

async def run():
    """Run the multi-agent travel planning system"""
    print("🚀 Starting Multi-Agent Travel Planning System...\n")
    
    initial_state = create_initial_state_with_origin("goa", "Banglore", 5, "party")
    
    try:
        result = await graph.ainvoke(initial_state)
        
        # Prepare content for file
        content_lines = []
        content_lines.append("# 🎯 FINAL TRAVEL ITINERARY\n")
        content_lines.append("="*70 + "\n\n")
        
        if result and "messages" in result:
            last_message = result["messages"][-1]
            if hasattr(last_message, 'content') and last_message.content:
                content_lines.append(last_message.content)
                print("✅ Itinerary generated successfully")
            else:
                content_lines.append("❌ No content in final message\n\n")
                
                # Debug information
                content_lines.append("## 📊 Pipeline Results:\n\n")
                content_lines.append(f"- Places found: {len(result.get('places', []))}\n")
                content_lines.append(f"- Route optimized: {'Yes' if result.get('optimal_route') else 'No'}\n")
                content_lines.append(f"- Schedule created: {'Yes' if result.get('daily_schedule') else 'No'}\n")
                content_lines.append(f"- Total messages: {len(result.get('messages', []))}\n")
                print("⚠️ Generated with limited content")
        else:
            content_lines.append("❌ No result returned\n")
            print("❌ No result returned")
        
        # Write to output.md file
        with open("output.md", "w", encoding="utf-8") as f:
            f.writelines(content_lines)
        
        print(f"📄 Itinerary saved to output.md")
            
    except Exception as e:
        error_content = f"# ❌ Error During Execution\n\n```\n{str(e)}\n```\n"
        
        with open("output.md", "w", encoding="utf-8") as f:
            f.write(error_content)
            
        print(f"❌ Error during execution: {e}")
        print("📄 Error details saved to output.md")
        import traceback
        traceback.print_exc()

async def run_simple():
    """Simple test run"""
    initial_state = {
        "days": 3,
        "destination": "Coorg",
        "user_query": "Plan a 3-day trip to Coorg",
        "messages": [],
        "next_step": "orchestrator"
    }
    
    try:
        result = await graph.ainvoke(initial_state)
        
        # Prepare content for file
        content_lines = []
        content_lines.append("# TRAVEL ITINERARY\n")
        content_lines.append("="*60 + "\n\n")
        
        if result and "messages" in result and result["messages"]:
            last_message = result["messages"][-1]
            if hasattr(last_message, 'content'):
                content_lines.append(last_message.content)
                print("✅ Simple itinerary generated")
            else:
                content_lines.append("No content available\n")
                print("⚠️ No content available")
        else:
            content_lines.append("No valid response\n")
            print("❌ No valid response")
        
        # Write to output.md file
        with open("output.md", "w", encoding="utf-8") as f:
            f.writelines(content_lines)
        
        print(f"📄 Itinerary saved to output.md")
        
    except Exception as e:
        error_content = f"# ❌ Error\n\n```\n{str(e)}\n```\n"
        
        with open("output.md", "w", encoding="utf-8") as f:
            f.write(error_content)
            
        print(f"❌ Error: {e}")
        print("📄 Error saved to output.md")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run())

# app = FastAPI()

# async def stream_langgraph_response(request: DecisionRequest):
#     graph = get_graph()
#     async for event in graph.stream(request):
#         kind = event["event"]
#         if kind == "on_chat_model_stream":
#             chunk = event["data"]["chunk"]
#             if chunk.content:
#                 yield chunk.content

# @app.post("/")
# async def stream_response(request: DecisionRequest):
#     return StreamingResponse(stream_response())

if __name__ == "__main__":
    asyncio.run(run())