from typing import Any, Dict, List
from state import TravelState
from base_llm import llm
from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage

PROMPT = """You are an accommodation specialist for travel planning.

Task: Suggest accommodations for a {effective_days}-day trip to {destination}
Theme: {theme}
Budget consideration: Mid-range to budget-friendly options
User Query: {user_query}

Available context:
- Places to visit: {num_places} locations planned
- Daily schedule: {"Available" if daily_schedule else "Not available"}
- Origin: {origin}

Your responsibilities:
1. Analyze the planned itinerary and route
2. Suggest strategic accommodation locations to minimize travel time
3. Recommend different types of stays (hotels, guesthouses, homestays)
4. Consider proximity to planned attractions
5. Provide options for different budgets
6. Suggest area-based accommodation strategy

For each accommodation suggestion, provide:
- Location name and area
- Type of accommodation (hotel/guesthouse/homestay/resort)
- Why this location is strategic for the itinerary
- Approximate price range
- Key amenities
- Proximity to planned attractions
- Transportation connectivity

Consider:
- Clustering accommodations near multiple attractions
- Local neighborhood character and safety
- Transportation hubs and connectivity
- Budget-friendly vs luxury options
- Local cultural experiences through stays

Provide a day-wise accommodation strategy:
- Which areas to stay in for maximum efficiency
- How to split nights between different locations if beneficial
- Backup options in case primary choices are unavailable"""

async def accommodation_agent(state: TravelState):
    """
    Suggests accommodations for each day of the trip
    """
    print("🏨 ACCOMMODATION AGENT: Finding stay options...")
    
    effective_days = state.get("effective_days", state["days"])
    optimal_route = state.get("optimal_route", [])
    places = state.get("places", [])
    daily_schedule = state.get("daily_schedule", {})
    
    accommodation_prompt = ChatPromptTemplate.from_messages([
        ("human", PROMPT)
    ])
    
    # You'll bind your accommodation tools here
    # accommodation_tools = [search_hotels, search_guesthouses, search_homestays, get_area_info]
    # accommodation_chain = accommodation_prompt | llm.bind_tools(accommodation_tools)
    
    accommodation_chain = accommodation_prompt | llm  # For now, without tools
    
    try:
        response = await accommodation_chain.ainvoke({
            "destination": state["destination"],
            "effective_days": effective_days,
            "theme": state.get("theme", "general"),
            "user_query": state["user_query"],
            "num_places": len(optimal_route or places),
            "daily_schedule": bool(daily_schedule),
            "origin": state.get("origin", "Not specified")
        })
        
        # Store accommodation suggestions
        accommodations = extract_accommodations_from_response(response.content)
        
        print(f"✅ Found {len(accommodations)} accommodation suggestions")
        
        return {
            "messages": [response],
            "accommodations": accommodations,
            "next_step": "synthesizer"
        }
        
    except Exception as e:
        print(f"❌ Accommodation planning error: {e}")
        return {
            "messages": [AIMessage(content=f"Accommodation planning failed: {e}")],
            "accommodations": [],
            "next_step": "synthesizer"
        }

def extract_accommodations_from_response(content: str) -> List[Dict[str, Any]]:
    """Extract accommodation data from LLM response - implement your parsing logic"""
    # Simple placeholder - you should implement proper parsing
    return [
        {
            "name": "Sample Hotel",
            "type": "hotel",
            "location": "City Center",
            "price_range": "Mid-range",
            "amenities": ["WiFi", "Breakfast"],
            "strategic_reason": "Close to main attractions"
        }
    ]