from state import TravelState
from langchain_core.messages import AIMessage, ToolMessage

# tools
from tools.schedule_tool import create_daily_schedule

async def visit_scheduler_agent(state: TravelState):
    """
    Creates detailed daily schedule with times
    """
    print("⏰ VISIT SCHEDULER: Creating timed schedule...")
    
    route = state.get("optimal_route") or state.get("places", [])
    if not route:
        return {
            "messages": [AIMessage(content="No route available for scheduling")],
            "next_step": "synthesizer"
        }
    
    try:
        distance_matrix = [[col["duration_seconds"] for col in row] for row in state.get("distance_matrix")]
        result = await create_daily_schedule.ainvoke({
            "optimized_route": route,
            "total_days": state["days"],
            "travel_times_matrix": distance_matrix,
            "start_time": "08:00"
        })
        
        print(f"✅ Schedule created for {state['days']} days")
        
        return {
            "messages": [ToolMessage(content=str(result), tool_call_id="visit_scheduler")],
            "daily_schedule": result,
            "next_step": "synthesizer"
        }
        
    except Exception as e:
        print(f"❌ Scheduling error: {e}")
        return {
            "messages": [AIMessage(content=f"Scheduling failed: {e}")],
            "next_step": "synthesizer"
        }