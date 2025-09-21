from typing import List, Dict, Any, Optional
from langchain_core.messages import AnyMessage
from typing_extensions import Annotated, TypedDict
from langgraph.graph.message import add_messages

class TravelState(TypedDict):
    """Enhanced state to track the entire travel planning pipeline"""
    messages: Annotated[list[AnyMessage], add_messages]
    days: int
    destination: str
    origin: Optional[str]
    start_date: Optional[str]  # YYYY-MM-DD format
    end_date: Optional[str]    # YYYY-MM-DD format
    budget: Optional[str]      # NEW: "low", "medium", "high", or specific amount
    theme: Optional[str]
    user_query: str
    query_type: str
    
    # Data from each step
    places: Optional[List[Dict[str, Any]]]
    original_places: Optional[List[Dict[str, Any]]]
    distance_matrix: Optional[Any]
    optimal_route: Optional[List[Dict[str, Any]]]
    daily_schedule: Optional[Dict[str, Any]]
    
    # Travel and accommodation data
    travel_info: Optional[Dict[str, Any]]
    accommodations: Optional[List[Dict[str, Any]]]
    effective_days: Optional[int]
    
    # Control flow
    next_step: str