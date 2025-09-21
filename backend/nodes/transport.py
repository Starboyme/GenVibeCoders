from typing import Any, Dict, List
from state import TravelState
from base_llm import llm
from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.prebuilt import ToolNode


from nodes.transport_agent.agent import transport_agent
from tools.fallbacks.travel_impact import calculate_travel_impact_fallback


async def travel_planner_agent(state: TravelState):
    """
    Plans travel from origin to destination with budget optimization
    Makes 4 separate calls to transport_agent: flights/trains for outbound/return
    """
    print("✈️ TRAVEL PLANNER: Finding comprehensive travel options...")
    
    if not state.get("origin"):
        print("⚠️ No origin specified, skipping travel planning")
        return {
            "messages": [AIMessage(content="No origin specified for travel planning")],
            "effective_days": state["days"],
            "next_step": "gather_places"
        }
    
    # Check required dates
    start_date = state.get("start_date")
    end_date = state.get("end_date")
    
    if not start_date or not end_date:
        print("❌ Start date and end date are required for transport planning")
        return {
            "messages": [AIMessage(content="ERROR: Start date and end date are required for transport planning.")],
            "travel_info": {"error": "Missing required dates", "planned": False},
            "effective_days": state["days"],
            "next_step": "gather_places"
        }
    
    try:
        # Generate user_id for session consistency
        import hashlib
        user_id = hashlib.md5(f"{state['origin']}{state['destination']}{start_date}".encode()).hexdigest()[:8]
        
        budget = state.get("budget", "medium")
        print(f"🔄 Finding travel options for budget: {budget}")
        
        # Prepare all 4 transport queries
        transport_queries = [
            {
                "type": "outbound_flight",
                "mode": "flight",
                "message": f"""
                Find flight options from {state["origin"]} to {state["destination"]} on {start_date}.
                
                SEARCH PARAMETERS:
                - Transport: flight
                - Origin: {state["origin"]}
                - Destination: {state["destination"]}
                - Date: {start_date}
                - Budget preference: {budget}
                
                Requirements:
                - Find multiple flight options (budget, economy, premium if available)
                - Include total travel time (flight + transfers + airport time)
                - Provide cost breakdown
                - Consider connecting flights if direct not available
                - Include airport transfer information to city center
                """
            },
            {
                "type": "outbound_train", 
                "mode": "train",
                "message": f"""
                Find train options from {state["origin"]} to {state["destination"]} on {start_date}.
                
                SEARCH PARAMETERS:
                - Transport: train
                - Origin: {state["origin"]}
                - Destination: {state["destination"]}
                - Date: {start_date}
                - Budget preference: {budget}
                
                Requirements:
                - Find multiple train options (different classes and timings)
                - Include total travel time (train + station transfers)
                - Provide cost breakdown for different classes
                - Include station to city center information
                - Consider overnight trains if applicable
                """
            },
            {
                "type": "return_flight",
                "mode": "flight", 
                "message": f"""
                Find return flight options from {state["destination"]} to {state["origin"]} on {end_date}.
                
                SEARCH PARAMETERS:
                - Transport: flight
                - Origin: {state["destination"]}
                - Destination: {state["origin"]}
                - Date: {end_date}
                - Budget preference: {budget}
                
                Requirements:
                - Find multiple return flight options
                - Include total travel time
                - Provide cost breakdown
                - Consider late evening flights to maximize last day
                - Include airport transfer information
                """
            },
            {
                "type": "return_train",
                "mode": "train",
                "message": f"""
                Find return train options from {state["destination"]} to {state["origin"]} on {end_date}.
                
                SEARCH PARAMETERS:
                - Transport: train
                - Origin: {state["destination"]}
                - Destination: {state["origin"]}
                - Date: {end_date}
                - Budget preference: {budget}
                
                Requirements:
                - Find multiple return train options
                - Include total travel time
                - Provide cost breakdown for different classes
                - Consider late evening departures
                - Include station transfer information
                """
            }
        ]
        
        # Execute all transport queries
        transport_results = {}
        
        for query in transport_queries:
            print(f"🔍 Searching {query['type']}...")
            
            try:
                # Stream response from transport agent
                agent_response_text = ""
                async for event in transport_agent.async_stream_query(
                    user_id=user_id,
                    message=query["message"],
                ):
                    try:
                        chunks = event['content']['parts']
                        for chunk in chunks:
                            agent_response_text += chunk['text']
                    except Exception as e:
                        pass
                
                transport_results[query['type']] = {
                    "mode": query['mode'],
                    "raw_response": agent_response_text,
                    "parsed_options": parse_transport_options(agent_response_text, query['mode'])
                }
                
                print(f"✅ {query['type']} found: {len(transport_results[query['type']]['parsed_options'])} options")
                
            except Exception as e:
                print(f"❌ Error getting {query['type']}: {e}")
                transport_results[query['type']] = {
                    "mode": query['mode'],
                    "raw_response": f"Error: {e}",
                    "parsed_options": []
                }
        
        # Analyze all options and recommend best combinations
        print("🤔 Analyzing travel combinations...")
        best_recommendations = analyze_travel_combinations(
            transport_results, 
            budget, 
            state["days"],
            start_date,
            end_date
        )
        
        # Calculate travel impact and effective days
        travel_time_impact = calculate_travel_impact_from_recommendations(best_recommendations)
        effective_days = max(1, state["days"] - travel_time_impact)
        
        # Create comprehensive travel info
        travel_info = {
            "origin": state["origin"],
            "destination": state["destination"],
            "start_date": start_date,
            "end_date": end_date,
            "budget": budget,
            "all_options": transport_results,
            "recommendations": best_recommendations,
            "travel_time_impact": travel_time_impact,
            "planned": True
        }
        
        # Generate summary response
        summary_response = generate_travel_summary(transport_results, best_recommendations, budget)
        
        print(f"✅ Travel analysis complete - Impact: {travel_time_impact} days, Effective days: {effective_days}")
        
        return {
            "messages": [AIMessage(content=summary_response)],
            "travel_info": travel_info,
            "effective_days": effective_days,
            "next_step": "gather_places"
        }
        
    except Exception as e:
        print(f"❌ Travel planning error: {e}")
        # Fallback calculation
        travel_time_impact = calculate_travel_impact_fallback(state["origin"], state["destination"])
        effective_days = max(1, state["days"] - travel_time_impact)
        
        return {
            "messages": [AIMessage(content=f"Travel planning encountered an error: {e}. Using fallback calculations.")],
            "travel_info": {
                "origin": state["origin"],
                "destination": state["destination"],
                "travel_time_impact": travel_time_impact,
                "planned": False,
                "error": str(e)
            },
            "effective_days": effective_days,
            "next_step": "gather_places"
        }


def parse_transport_options(response_text: str, mode: str) -> List[Dict[str, Any]]:
    """
    Parse transport agent response to extract structured options
    """
    options = []
    
    try:
        import re
        
        # Common patterns for extracting transport info
        if mode == "flight":
            # Look for flight patterns
            flight_patterns = [
                r'(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})',  # Time patterns
                r'₹\s*(\d{1,3}(?:,\d{3})*)',               # Price patterns
                r'(\d+)h\s*(\d+)m',                        # Duration patterns
            ]
            
            # Extract prices
            prices = re.findall(r'₹\s*(\d{1,3}(?:,\d{3})*)', response_text)
            times = re.findall(r'(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})', response_text)
            durations = re.findall(r'(\d+)h\s*(\d+)m', response_text)
            
            # Create structured options (basic parsing)
            for i, price in enumerate(prices[:5]):  # Limit to 5 options
                option = {
                    "mode": "flight",
                    "price": price.replace(',', ''),
                    "departure_time": times[i][0] if i < len(times) else "TBD",
                    "arrival_time": times[i][1] if i < len(times) else "TBD",
                    "duration": f"{durations[i][0]}h {durations[i][1]}m" if i < len(durations) else "TBD",
                    "raw_info": response_text[i*200:(i+1)*200] if len(response_text) > i*200 else ""
                }
                options.append(option)
                
        elif mode == "train":
            # Similar parsing for trains
            prices = re.findall(r'₹\s*(\d{1,3}(?:,\d{3})*)', response_text)
            times = re.findall(r'(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})', response_text)
            
            for i, price in enumerate(prices[:5]):
                option = {
                    "mode": "train",
                    "price": price.replace(',', ''),
                    "departure_time": times[i][0] if i < len(times) else "TBD",
                    "arrival_time": times[i][1] if i < len(times) else "TBD",
                    "raw_info": response_text[i*200:(i+1)*200] if len(response_text) > i*200 else ""
                }
                options.append(option)
        
        # If no structured parsing worked, create a basic option
        if not options and response_text.strip():
            options.append({
                "mode": mode,
                "price": "TBD",
                "raw_info": response_text[:500]
            })
            
    except Exception as e:
        print(f"⚠️ Error parsing {mode} options: {e}")
        # Return basic option with raw text
        if response_text.strip():
            options.append({
                "mode": mode,
                "price": "TBD", 
                "error": str(e),
                "raw_info": response_text[:500]
            })
    
    return options

def analyze_travel_combinations(transport_results: Dict, budget: str, days: int, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Analyze all transport combinations and recommend best options based on budget
    """
    recommendations = []
    
    # Budget preferences
    budget_priorities = {
        "low": {"priority": "price", "max_price_factor": 1.0},
        "medium": {"priority": "balance", "max_price_factor": 1.5}, 
        "high": {"priority": "convenience", "max_price_factor": 2.0}
    }
    
    budget_pref = budget_priorities.get(budget, budget_priorities["medium"])
    
    # Create combinations
    outbound_flights = transport_results.get("outbound_flight", {}).get("parsed_options", [])
    outbound_trains = transport_results.get("outbound_train", {}).get("parsed_options", [])
    return_flights = transport_results.get("return_flight", {}).get("parsed_options", [])
    return_trains = transport_results.get("return_train", {}).get("parsed_options", [])
    
    combinations = []
    
    # Flight + Flight
    for out_flight in outbound_flights[:3]:  # Limit combinations
        for ret_flight in return_flights[:3]:
            if out_flight.get("price", "0").isdigit() and ret_flight.get("price", "0").isdigit():
                total_price = int(out_flight["price"]) + int(ret_flight["price"])
                combinations.append({
                    "type": "flight_flight",
                    "outbound": out_flight,
                    "return": ret_flight,
                    "total_price": total_price,
                    "total_time_impact": 0,  # Flights usually don't consume full days
                    "convenience_score": 9
                })
    
    # Train + Train
    for out_train in outbound_trains[:3]:
        for ret_train in return_trains[:3]:
            if out_train.get("price", "0").isdigit() and ret_train.get("price", "0").isdigit():
                total_price = int(out_train["price"]) + int(ret_train["price"])
                combinations.append({
                    "type": "train_train", 
                    "outbound": out_train,
                    "return": ret_train,
                    "total_price": total_price,
                    "total_time_impact": 1,  # Trains might consume parts of days
                    "convenience_score": 6
                })
    
    # Mixed combinations
    for out_flight in outbound_flights[:2]:
        for ret_train in return_trains[:2]:
            if out_flight.get("price", "0").isdigit() and ret_train.get("price", "0").isdigit():
                total_price = int(out_flight["price"]) + int(ret_train["price"])
                combinations.append({
                    "type": "flight_train",
                    "outbound": out_flight,
                    "return": ret_train,
                    "total_price": total_price,
                    "total_time_impact": 0,
                    "convenience_score": 7
                })
    
    # Sort combinations based on budget preference
    if budget_pref["priority"] == "price":
        combinations.sort(key=lambda x: x["total_price"])
    elif budget_pref["priority"] == "convenience":
        combinations.sort(key=lambda x: -x["convenience_score"])
    else:  # balance
        combinations.sort(key=lambda x: x["total_price"] - (x["convenience_score"] * 100))
    
    # Return top recommendations
    recommendations = combinations[:3]  # Top 3 combinations
    
    return recommendations

def calculate_travel_impact_from_recommendations(recommendations: List[Dict[str, Any]]) -> int:
    """
    Calculate travel time impact from best recommendation
    """
    if not recommendations:
        return 1  # Default
    
    best_option = recommendations[0]
    return best_option.get("total_time_impact", 0)

def generate_travel_summary(transport_results: Dict, recommendations: List[Dict[str, Any]], budget: str) -> str:
    """
    Generate a comprehensive travel summary
    """
    summary = f"# 🚀 COMPREHENSIVE TRAVEL ANALYSIS\n\n"
    summary += f"**Budget Preference**: {budget.title()}\n\n"
    
    summary += f"## 🔍 Search Results Summary\n\n"
    for result_type, result_data in transport_results.items():
        options_count = len(result_data.get("parsed_options", []))
        summary += f"- **{result_type.replace('_', ' ').title()}**: {options_count} options found\n"
    
    summary += f"\n## 🏆 TOP RECOMMENDATIONS\n\n"
    
    for i, rec in enumerate(recommendations[:3], 1):
        summary += f"### Option {i}: {rec['type'].replace('_', ' + ').title()}\n"
        summary += f"- **Total Cost**: ₹{rec['total_price']:,}\n"
        summary += f"- **Convenience Score**: {rec['convenience_score']}/10\n"
        summary += f"- **Travel Impact**: {rec['total_time_impact']} days\n"
        
        # Outbound details
        outbound = rec["outbound"]
        summary += f"- **Outbound**: {outbound['mode'].title()} "
        if outbound.get("departure_time"):
            summary += f"({outbound['departure_time']} - {outbound.get('arrival_time', 'TBD')}) "
        summary += f"₹{outbound.get('price', 'TBD')}\n"
        
        # Return details
        return_opt = rec["return"]
        summary += f"- **Return**: {return_opt['mode'].title()} "
        if return_opt.get("departure_time"):
            summary += f"({return_opt['departure_time']} - {return_opt.get('arrival_time', 'TBD')}) "
        summary += f"₹{return_opt.get('price', 'TBD')}\n\n"
    
    summary += f"## 📊 Raw Search Results\n\n"
    summary += f"*Detailed search results from transport agent available in travel_info*\n"
    
    return summary