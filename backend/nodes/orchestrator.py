from state import TravelState
from base_llm import llm
from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage


PROMPT = """You are an orchestrator for a travel planning system. Analyze the user query and determine what type of request this is.

User Query: "{user_query}"
Destination: {destination}
Origin: {origin}
Days: {days}

Classify the query into ONE of these categories and respond with ONLY the category name:

1. "generate_itinerary" - User wants to plan a new trip/itinerary from scratch
2. "modify_time" - User wants to change the time of visit for existing places
3. "add_place" - User wants to add a new place to existing itinerary  
4. "remove_place" - User wants to remove a place from existing itinerary
5. "regenerate_route" - User wants to optimize/change the route order
6. "modify_schedule" - User wants to change the daily schedule
7. "find_travel" - User wants to find flights/trains from origin to destination
8. "find_accommodation" - User wants accommodation suggestions

Current state: {current_state}
Origin status: {origin_status}

Respond with ONLY the category name."""

async def orchestrator_agent(state: TravelState):
    """
    Analyzes user query and routes to appropriate next step
    """
    print("🎭 ORCHESTRATOR: Analyzing user query...")
    
    # Check if places exist in state
    has_places_text = "Has places" if state.get("places") else "No places yet"
    has_origin_text = "Has origin" if state.get("origin") else "No origin specified"
    
    orchestrator_prompt = ChatPromptTemplate.from_messages([
        ("human", PROMPT)
    ])
    
    try:
        orchestrator_chain = orchestrator_prompt | llm
        response = await orchestrator_chain.ainvoke({
            "user_query": state["user_query"],
            "destination": state["destination"],
            "origin": state.get("origin", "Not specified"),
            "days": state["days"],
            "current_state": has_places_text,
            "origin_status": has_origin_text
        })
        
        query_type = response.content.strip().lower()
        print(f"🎯 Query classified as: {query_type}")
        
        # Determine next step based on query type and state
        if query_type == "generate_itinerary" or not state.get("places"):
            # If origin is specified, start with travel planning
            if state.get("origin") and not state.get("travel_info"):
                next_step = "plan_travel"
            else:
                next_step = "gather_places"
        elif query_type == "find_travel":
            next_step = "plan_travel"
        elif query_type == "find_accommodation":
            next_step = "suggest_stays"
        elif query_type == "modify_time":
            next_step = "synthesizer"
        elif query_type in ["add_place", "remove_place"]:
            next_step = "modify_places"
        elif query_type == "regenerate_route":
            next_step = "generate_route"
        elif query_type == "modify_schedule":
            next_step = "schedule_visits"
        else:
            # Default flow - check if we need travel planning first
            if state.get("origin") and not state.get("travel_info"):
                next_step = "plan_travel"
            else:
                next_step = "gather_places"
        
        return {
            "query_type": query_type,
            "next_step": next_step,
            "messages": [AIMessage(content=f"Routing to: {next_step}")]
        }
        
    except Exception as e:
        print(f"❌ Orchestrator error: {e}")
        # Default routing with origin check
        if state.get("origin") and not state.get("travel_info"):
            next_step = "plan_travel"
        else:
            next_step = "gather_places"
            
        return {
            "query_type": "generate_itinerary",
            "next_step": next_step,
            "messages": [AIMessage(content="Defaulting to itinerary generation")]
        }