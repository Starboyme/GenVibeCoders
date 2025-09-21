from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.prebuilt import ToolNode


from state import TravelState
from base_llm import llm

# tools
from tools.gather_places import gather_places


PROMPT = """You are a places gathering agent. Your job is to find popular places for travel planning.

Task: Find places for a {effective_days}-day trip to {destination}
Original trip duration: {total_days} days
Effective days after travel: {effective_days} days
Theme: {theme}
User Query: {user_query}

Travel context: {travel_context}

Use the gather_places tool to find relevant places. Consider the effective number of days to determine how many places to return:
- <= 2 days → up to 5 places
- <= 5 days → up to 10 places  
- > 5 days → up to 15 places

Focus on must-visit attractions that can be covered in the available time.

Call the gather_places tool now."""

async def gather_places_agent(state: TravelState):
    """
    Gathers places based on destination, effective days, and theme
    """
    print("PLACES GATHERER: Finding places...")
    
    # Use effective days instead of original days
    effective_days = state.get("effective_days", state["days"])
    
    gatherer_prompt = ChatPromptTemplate.from_messages([
        ("human", PROMPT)
    ])
    
    tools = [gather_places]
    gatherer_chain = gatherer_prompt | llm.bind_tools(tools)
    
    try:
        # Prepare travel context
        travel_info = state.get("travel_info", {})
        travel_context = "No travel information available"
        if travel_info and travel_info.get("planned"):
            impact = travel_info.get("travel_time_impact", 0)
            travel_context = f"Travel from {travel_info.get('origin', 'origin')} requires {impact} day(s)"
        
        response = await gatherer_chain.ainvoke({
            "effective_days": effective_days,
            "total_days": state["days"],
            "destination": state["destination"],
            "theme": state.get("theme", "general"),
            "user_query": state["user_query"],
            "travel_context": travel_context
        })
        
        
        return {
            "messages": [response],
            "next_step": "execute_gather_places"
        }
        
    except Exception as e:
        print(f"Places gatherer error: {e}")
        return {
            "messages": [AIMessage(content=f"Error gathering places: {e}")],
            "next_step": "synthesizer"
        }

async def execute_gather_places(state: TravelState):
    """Execute the gather_places tool and store results"""
    print("Executing gather_places tool...")
    
    tool_node = ToolNode([gather_places])
    result = await tool_node.ainvoke(state)
    
    # Extract places from tool result
    places = []
    if result["messages"]:
        for msg in result["messages"]:
            if isinstance(msg, ToolMessage) and msg.content:
                try:
                    import json
                    tool_result = json.loads(msg.content)
                    places = tool_result
                except:
                    # Handle string format or other formats
                    if "places" in str(msg.content):
                        places = [] 
    
    print(f"Found {len(places)} places")
    
    return {
        "messages": result["messages"],
        "places": places,
        "original_places": places.copy() if places else [],
        "next_step": "generate_distance_matrix"
    }