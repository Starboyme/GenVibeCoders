from state import TravelState
from base_llm import llm
from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage
from datetime import datetime, timedelta


ENHANCED_PROMPT = """Create a comprehensive travel itinerary for {destination} using the structured data provided.

AVAILABLE DATA:
{structured_data}

TASK: Create a detailed, chronologically organized travel itinerary with SPECIFIC BOOKING RECOMMENDATIONS and actionable steps.

# Complete Travel Itinerary: {destination}

## Trip Overview
- **Origin**: {origin}
- **Destination**: {destination}
- **Travel Dates**: {start_date} to {end_date}
- **Total Duration**: {total_days} days
- **Effective Sightseeing Days**: {effective_days} days
- **Theme**: {theme}
- **Budget**: {budget}

## Confirmed Bookings & Recommendations
{travel_summary}

## Accommodation Bookings
{accommodation_summary}

## Detailed Day-by-Day Itinerary
{daily_itinerary_structure}

## Budget Breakdown
### Transportation Costs
- **Recommended Option**: [Extract from travel_summary]
- **Total Transport Cost**: [Total from recommendations]
- **Alternative Options**: [Show 1-2 cheaper alternatives]

### Daily Expenses (Estimated per day)
- **Accommodation**: Rs 1,500 - Rs 3,000 per night
- **Meals**: Rs 800 - Rs 1,500 per day
- **Local Transport**: Rs 300 - Rs 800 per day
- **Attractions/Activities**: Rs 500 - Rs 1,200 per day
- **Shopping/Miscellaneous**: Rs 500 - Rs 1,000 per day

**Total Estimated Trip Cost**: Rs [Calculate based on days and transport]

## Pre-Travel Checklist
### Immediate Action Items (Book Now)
- [ ] Confirm flight/train bookings from recommendations above
- [ ] Book accommodation for {effective_days} nights
- [ ] Purchase travel insurance
- [ ] Check visa/ID requirements (if applicable)

### 1-2 Weeks Before Travel
- [ ] Check weather forecast and pack accordingly
- [ ] Download offline maps and translation apps
- [ ] Inform bank about travel plans
- [ ] Arrange airport/station transfers
- [ ] Research local emergency contacts

### Day Before Departure
- [ ] Confirm flight/train timings and platform/gate info
- [ ] Pack essential documents and medicines
- [ ] Charge all electronic devices
- [ ] Check in online (for flights)
- [ ] Set multiple alarms for departure day

## Essential Packing List
### Documents
- Valid ID/Passport copies (digital + physical)
- Confirmed ticket printouts/screenshots
- Hotel booking confirmations
- Travel insurance documents
- Emergency contact list

### Based on Activities in {destination}
- [Customize based on theme and planned activities]
- Comfortable walking shoes for sightseeing
- Weather-appropriate clothing
- Portable charger and adapters
- Basic first-aid kit and personal medications

## Important Reminders
- **Booking Windows**: Train tickets open 120 days ahead, flights are cheapest 3-4 weeks ahead
- **Cancellation Policies**: Check and understand cancellation terms for all bookings
- **Local Customs**: Research cultural norms and dress codes for attractions
- **Emergency Preparedness**: Save local emergency numbers and embassy contacts
- **Health Precautions**: Check if any vaccinations or health certificates are required

Generate a COMPLETE, ACTIONABLE itinerary with specific booking details and clear next steps."""

async def synthesizer_agent(state: TravelState):
    """
    Creates final formatted itinerary from all collected data in chronological order
    """
    print("✨ SYNTHESIZER: Creating chronologically organized itinerary...")
    
    # Extract all available data
    places = state.get("places", [])
    optimal_route = state.get("optimal_route", places) or []
    daily_schedule = state.get("daily_schedule", {})
    travel_info = state.get("travel_info", {})
    accommodations = state.get("accommodations", []) or []
    effective_days = state.get("effective_days", state["days"])
    
    print(f"📊 Processing data - Places: {len(places)}, Route: {len(optimal_route)}, Schedule: {bool(daily_schedule)}, Travel: {bool(travel_info)}, Accommodations: {len(accommodations)}")
    
    # Create structured data for the LLM
    structured_data = build_structured_data(state, places, optimal_route, daily_schedule, travel_info, accommodations, effective_days)
    
    # Build travel summary
    travel_summary = build_travel_summary(travel_info, state)
    
    # Build accommodation summary
    accommodation_summary = build_accommodation_summary(accommodations, optimal_route, effective_days)
    
    # Build detailed daily itinerary structure
    daily_itinerary_structure = build_daily_itinerary_structure(
        state, optimal_route, daily_schedule, travel_info, accommodations, effective_days
    )
    
    synthesizer_prompt = ChatPromptTemplate.from_messages([
        ("human", ENHANCED_PROMPT)
    ])
    
    synthesizer_chain = synthesizer_prompt | llm
    
    try:
        response = await synthesizer_chain.ainvoke({
            "destination": state["destination"],
            "origin": state.get("origin", "Not specified"),
            "start_date": state.get("start_date", "TBD"),
            "end_date": state.get("end_date", "TBD"),
            "total_days": state["days"],
            "effective_days": effective_days,
            "theme": state.get("theme", "general tourism"),
            "budget": state.get("budget", "medium"),
            "structured_data": structured_data,
            "travel_summary": travel_summary,
            "accommodation_summary": accommodation_summary,
            "daily_itinerary_structure": daily_itinerary_structure
        })
        
        if hasattr(response, 'content') and response.content:
            content_length = len(response.content)
            print(f"✅ Generated chronologically organized itinerary: {content_length} characters")
        else:
            print("❌ No content generated, creating enhanced fallback")
            response = AIMessage(content=create_enhanced_fallback_itinerary(state))
        
        return {
            "messages": [response],
            "next_step": "END"
        }
        
    except Exception as e:
        print(f"❌ Synthesizer error: {e}")
        fallback_content = create_enhanced_fallback_itinerary(state)
        return {
            "messages": [AIMessage(content=fallback_content)],
            "next_step": "END"
        }


def build_structured_data(state, places, optimal_route, daily_schedule, travel_info, accommodations, effective_days):
    """Build comprehensive structured data summary"""
    data_sections = []
    
    # Travel Information Section
    if travel_info and travel_info.get("planned"):
        data_sections.append("TRAVEL DETAILS:")
        data_sections.append(f"- Origin: {travel_info.get('origin', 'Not specified')}")
        data_sections.append(f"- Destination: {state['destination']}")
        data_sections.append(f"- Departure Date: {state.get('start_date', 'TBD')}")
        data_sections.append(f"- Return Date: {state.get('end_date', 'TBD')}")
        data_sections.append(f"- Travel Impact: {travel_info.get('travel_time_impact', 0)} day(s)")
        
        if travel_info.get("recommendations"):
            data_sections.append("- Best Travel Options:")
            for i, rec in enumerate(travel_info["recommendations"][:2], 1):
                data_sections.append(f"  {i}. {rec.get('type', 'Option')}: ₹{rec.get('total_price', 'TBD')}")
        data_sections.append("")
    
    # Places and Route Section
    if optimal_route:
        data_sections.append(f"OPTIMIZED ROUTE ({len(optimal_route)} places):")
        for i, place in enumerate(optimal_route, 1):
            name = place.get('name', f'Place {i}')
            place_type = place.get('type', 'attraction')
            rating = f" ({place['rating']}★)" if place.get('rating') else ""
            data_sections.append(f"{i}. {name} - {place_type}{rating}")
        data_sections.append("")
    
    # Daily Schedule Section
    if daily_schedule and daily_schedule.get('success'):
        data_sections.append("DAILY SCHEDULE STRUCTURE:")
        schedules = daily_schedule.get('daily_schedules', {})
        for day_key in sorted(schedules.keys()):
            day_data = schedules[day_key]
            activities = day_data.get('activities', [])
            data_sections.append(f"- {day_key}: {len(activities)} activities planned")
            for activity in activities[:3]:  # Show first 3 activities
                time = activity.get('time', 'TBD')
                name = activity.get('name', 'Activity')
                data_sections.append(f"  • {time}: {name}")
        data_sections.append("")
    
    # Accommodation Section
    if accommodations:
        data_sections.append(f"ACCOMMODATION OPTIONS ({len(accommodations)} available):")
        for i, acc in enumerate(accommodations[:3], 1):
            name = acc.get('name', f'Accommodation {i}')
            location = acc.get('location', 'Location TBD')
            acc_type = acc.get('type', 'accommodation')
            price_range = acc.get('price_range', 'Price TBD')
            data_sections.append(f"{i}. {name} ({acc_type}) - {location} - {price_range}")
        data_sections.append("")
    
    return "\n".join(data_sections) if data_sections else "Limited structured data available"


def build_travel_summary(travel_info, state):
    """Build comprehensive travel summary with actionable booking recommendations"""
    if not travel_info or not travel_info.get("planned"):
        return "No travel information available - assuming local planning only."
    
    summary_parts = []
    
    # Basic travel info
    origin = travel_info.get('origin', 'Not specified')
    destination = state.get('destination', 'Not specified')
    start_date = travel_info.get('start_date', 'TBD')
    end_date = travel_info.get('end_date', 'TBD')
    impact = travel_info.get('travel_time_impact', 0)
    budget = travel_info.get('budget', 'medium')
    
    summary_parts.append(f"**Route**: {origin} → {destination}")
    summary_parts.append(f"**Travel Dates**: {start_date} to {end_date}")
    summary_parts.append(f"**Budget Preference**: {budget.title()}")
    if impact > 0:
        summary_parts.append(f"**Travel Impact**: {impact} day(s) will be partially used for travel")
    
    # Extract best recommendation for booking
    recommendations = travel_info.get('recommendations', [])
    if recommendations:
        best_option = recommendations[0]  # Top recommendation
        summary_parts.append("")
        summary_parts.append("**🎯 RECOMMENDED BOOKING:**")
        
        outbound = best_option.get('outbound', {})
        return_leg = best_option.get('return', {})
        total_price = best_option.get('total_price', 'TBD')
        
        # Outbound booking details
        summary_parts.append(f"**Outbound Journey ({start_date})**:")
        summary_parts.append(f"- Mode: {outbound.get('mode', 'Transport').title()}")
        if outbound.get('departure_time'):
            summary_parts.append(f"- Timing: {outbound['departure_time']} - {outbound.get('arrival_time', 'TBD')}")
        summary_parts.append(f"- Cost: ₹{outbound.get('price', 'TBD')}")
        if outbound.get('duration'):
            summary_parts.append(f"- Duration: {outbound['duration']}")
        
        # Return booking details
        summary_parts.append(f"**Return Journey ({end_date})**:")
        summary_parts.append(f"- Mode: {return_leg.get('mode', 'Transport').title()}")
        if return_leg.get('departure_time'):
            summary_parts.append(f"- Timing: {return_leg['departure_time']} - {return_leg.get('arrival_time', 'TBD')}")
        summary_parts.append(f"- Cost: ₹{return_leg.get('price', 'TBD')}")
        if return_leg.get('duration'):
            summary_parts.append(f"- Duration: {return_leg['duration']}")
        
        summary_parts.append(f"**Total Travel Cost: ₹{total_price:,}**")
        
        # Alternative options
        if len(recommendations) > 1:
            summary_parts.append("")
            summary_parts.append("**Alternative Options:**")
            for i, alt_rec in enumerate(recommendations[1:3], 2):
                alt_outbound = alt_rec.get('outbound', {})
                alt_return = alt_rec.get('return', {})
                alt_price = alt_rec.get('total_price', 'TBD')
                
                summary_parts.append(f"{i}. {alt_outbound.get('mode', '').title()} + {alt_return.get('mode', '').title()}: ₹{alt_price:,}")
                summary_parts.append(f"   Convenience Score: {alt_rec.get('convenience_score', 'N/A')}/10")
        
        # Booking recommendations and tips
        summary_parts.append("")
        summary_parts.append("**📋 Booking Action Items:**")
        
        if outbound.get('mode') == 'flight':
            summary_parts.append("- Book flights 3-4 weeks in advance for best prices")
            summary_parts.append("- Check baggage allowance and add-on costs")
            summary_parts.append("- Arrive at airport 2 hours before domestic flights")
            summary_parts.append("- Consider seat selection and meal preferences during booking")
            if 'connecting' in outbound.get('raw_info', '').lower():
                summary_parts.append("- Account for layover time and terminal changes")
        elif outbound.get('mode') == 'train':
            summary_parts.append("- Book train tickets as early as possible (booking opens 120 days ahead)")
            summary_parts.append("- Consider Tatkal booking if normal quota is full")
            summary_parts.append("- Reach station 30 minutes before departure")
            summary_parts.append("- Check platform number before travel date")
            if 'overnight' in outbound.get('raw_info', '').lower():
                summary_parts.append("- Pack essentials for overnight journey")
        
        # Transportation to/from stations/airports
        summary_parts.append("- Arrange airport/station transfers in advance")
        summary_parts.append("- Keep digital copies of tickets on phone")
        summary_parts.append("- Check cancellation and rescheduling policies")
        
    else:
        summary_parts.append("")
        summary_parts.append("**Travel by Road Recommended:**")
        summary_parts.append("- Consider renting a car or hiring a taxi")
        summary_parts.append("- Plan for rest stops during long drives")
        summary_parts.append("- Check road conditions and weather before departure")
        summary_parts.append("- Keep emergency contacts and roadside assistance numbers")
    
    return "\n".join(summary_parts)


def build_accommodation_summary(accommodations, optimal_route, effective_days):
    """Build accommodation strategy summary"""
    if not accommodations:
        return "Accommodation suggestions not available - please research local options based on your route."
    
    summary_parts = []
    summary_parts.append(f"**Strategy**: Optimize stays for {effective_days}-day itinerary")
    
    if len(optimal_route) > 0:
        summary_parts.append(f"**Location Considerations**: Based on {len(optimal_route)} planned attractions")
    
    summary_parts.append("**Recommended Options**:")
    for i, acc in enumerate(accommodations[:3], 1):
        name = acc.get('name', f'Option {i}')
        location = acc.get('location', 'Central area')
        acc_type = acc.get('type', 'accommodation')
        reason = acc.get('strategic_reason', 'Good location for planned activities')
        price_range = acc.get('price_range', 'Mid-range')
        
        summary_parts.append(f"{i}. **{name}** ({acc_type})")
        summary_parts.append(f"   - Location: {location}")
        summary_parts.append(f"   - Price: {price_range}")
        summary_parts.append(f"   - Why: {reason}")
    
    return "\n".join(summary_parts)


def build_daily_itinerary_structure(state, optimal_route, daily_schedule, travel_info, accommodations, effective_days):
    """Build detailed day-by-day structure with specific travel booking information"""
    structure_parts = []
    
    # Extract travel booking details
    travel_impact = travel_info.get('travel_time_impact', 0) if travel_info else 0
    is_travel_day = travel_impact > 0 and state.get('origin')
    recommendations = travel_info.get('recommendations', []) if travel_info else []
    best_travel = recommendations[0] if recommendations else None
    
    structure_parts.append("**Chronological Day-by-Day Plan:**")
    structure_parts.append("")
    
    # Day 1: Handle travel day with specific booking info
    if is_travel_day and best_travel:
        outbound = best_travel.get('outbound', {})
        structure_parts.append("### Day 1: Departure & Travel")
        
        if outbound.get('mode') == 'flight':
            departure_time = outbound.get('departure_time', 'TBD')
            arrival_time = outbound.get('arrival_time', 'TBD')
            duration = outbound.get('duration', 'TBD')
            
            structure_parts.append("**FLIGHT BOOKING CONFIRMED:**")
            structure_parts.append(f"- Flight: {state.get('origin', 'Origin')} → {state['destination']}")
            structure_parts.append(f"- Departure: {departure_time}")
            structure_parts.append(f"- Arrival: {arrival_time}")
            structure_parts.append(f"- Duration: {duration}")
            structure_parts.append(f"- Cost: ₹{outbound.get('price', 'TBD')}")
            structure_parts.append("")
            
            structure_parts.append("**Travel Day Schedule:**")
            # Calculate recommended airport arrival time
            if departure_time != 'TBD':
                try:
                    from datetime import datetime, timedelta
                    dept_time = datetime.strptime(departure_time, "%H:%M")
                    airport_time = (dept_time - timedelta(hours=2)).strftime("%H:%M")
                    structure_parts.append(f"- {airport_time}: Leave for airport (2 hours before flight)")
                    structure_parts.append(f"- {departure_time}: Flight departure")
                    structure_parts.append(f"- {arrival_time}: Arrival at {state['destination']}")
                except:
                    structure_parts.append(f"- Early morning: Leave for airport")
                    structure_parts.append(f"- {departure_time}: Flight departure")
                    structure_parts.append(f"- {arrival_time}: Arrival at {state['destination']}")
            
            if arrival_time != 'TBD':
                try:
                    arrival_dt = datetime.strptime(arrival_time, "%H:%M")
                    checkin_time = (arrival_dt + timedelta(hours=1)).strftime("%H:%M")
                    structure_parts.append(f"- {checkin_time}: Airport transfer and hotel check-in")
                except:
                    structure_parts.append("- After arrival: Transfer to hotel and check-in")
            
            structure_parts.append("- Evening: Rest and local orientation")
            
        elif outbound.get('mode') == 'train':
            departure_time = outbound.get('departure_time', 'TBD')
            arrival_time = outbound.get('arrival_time', 'TBD')
            
            structure_parts.append("**TRAIN BOOKING CONFIRMED:**")
            structure_parts.append(f"- Train: {state.get('origin', 'Origin')} → {state['destination']}")
            structure_parts.append(f"- Departure: {departure_time}")
            structure_parts.append(f"- Arrival: {arrival_time}")
            structure_parts.append(f"- Cost: ₹{outbound.get('price', 'TBD')}")
            structure_parts.append("")
            
            structure_parts.append("**Travel Day Schedule:**")
            if departure_time != 'TBD':
                try:
                    dept_time = datetime.strptime(departure_time, "%H:%M")
                    station_time = (dept_time - timedelta(minutes=30)).strftime("%H:%M")
                    structure_parts.append(f"- {station_time}: Reach railway station")
                    structure_parts.append(f"- {departure_time}: Train departure")
                    structure_parts.append(f"- {arrival_time}: Arrival at {state['destination']}")
                except:
                    structure_parts.append(f"- Early: Reach railway station")
                    structure_parts.append(f"- {departure_time}: Train departure")
                    structure_parts.append(f"- {arrival_time}: Arrival at {state['destination']}")
            
            structure_parts.append("- After arrival: Transfer to hotel and check-in")
            structure_parts.append("- Evening: Rest and explore local area")
        
        structure_parts.append("")
    
    # Handle sightseeing days using daily_schedule or optimal_route
    sightseeing_start_day = 2 if is_travel_day else 1
    
    if daily_schedule and daily_schedule.get('success'):
        structure_parts.append("**Using Optimized Activity Schedule:**")
        schedules = daily_schedule.get('daily_schedules', {})
        
        for day_num in range(sightseeing_start_day, sightseeing_start_day + effective_days):
            schedule_day = f"Day {day_num - (1 if is_travel_day else 0)}"
            
            if schedule_day in schedules:
                day_data = schedules[schedule_day]
                activities = day_data.get('activities', [])
                
                structure_parts.append(f"### Day {day_num}: Sightseeing")
                if activities:
                    current_period = None
                    for activity in activities:
                        time = activity.get('time', 'TBD')
                        name = activity.get('name', 'Activity')
                        duration = activity.get('duration', '')
                        location = activity.get('location', '')
                        
                        # Determine time period
                        period = get_time_period(time)
                        if period != current_period:
                            structure_parts.append(f"**{period}**")
                            current_period = period
                        
                        duration_text = f" ({duration})" if duration else ""
                        location_text = f" at {location}" if location else ""
                        structure_parts.append(f"- {time}: {name}{duration_text}{location_text}")
                
                # Add accommodation info for this day
                if accommodations:
                    recommended_stay = accommodations[0] if accommodations else None
                    if recommended_stay:
                        structure_parts.append("")
                        structure_parts.append(f"**Accommodation: {recommended_stay.get('name', 'Hotel')}**")
                        structure_parts.append(f"- Location: {recommended_stay.get('location', 'Central area')}")
                        structure_parts.append(f"- Type: {recommended_stay.get('type', 'Hotel')}")
                        structure_parts.append(f"- Booking tip: {recommended_stay.get('strategic_reason', 'Good location')}")
                
                structure_parts.append("")
    else:
        # Fallback: Create structure from optimal_route
        structure_parts.append("**Using Route-Based Schedule:**")
        
        if optimal_route:
            places_per_day = max(1, len(optimal_route) // effective_days)
            route_index = 0
            
            for day_num in range(sightseeing_start_day, sightseeing_start_day + effective_days):
                structure_parts.append(f"### Day {day_num}: Exploration")
                
                # Morning activities
                structure_parts.append("**Morning (8:00 AM - 12:00 PM)**")
                structure_parts.append("- 8:00 AM: Breakfast at hotel")
                
                if route_index < len(optimal_route):
                    place = optimal_route[route_index]
                    structure_parts.append(f"- 9:30 AM: Visit {place.get('name', 'Attraction')}")
                    if place.get('address'):
                        structure_parts.append(f"  Address: {place['address']}")
                    if place.get('type'):
                        structure_parts.append(f"  Type: {place['type']}")
                    route_index += 1
                
                # Afternoon activities
                structure_parts.append("**Afternoon (12:00 PM - 6:00 PM)**")
                structure_parts.append("- 12:30 PM: Lunch at local restaurant")
                
                if route_index < len(optimal_route) and places_per_day > 1:
                    place = optimal_route[route_index]
                    structure_parts.append(f"- 2:30 PM: Visit {place.get('name', 'Attraction')}")
                    if place.get('address'):
                        structure_parts.append(f"  Address: {place['address']}")
                    route_index += 1
                
                # Evening
                structure_parts.append("**Evening (6:00 PM onwards)**")
                structure_parts.append("- 7:30 PM: Dinner")
                structure_parts.append("- Evening: Leisure and local exploration")
                structure_parts.append("")
    
    # Final day: Return journey with specific booking info
    final_day = state['days']
    if best_travel and final_day > 1:
        return_leg = best_travel.get('return', {})
        structure_parts.append(f"### Day {final_day}: Departure")
        
        if return_leg.get('mode') == 'flight':
            departure_time = return_leg.get('departure_time', 'TBD')
            arrival_time = return_leg.get('arrival_time', 'TBD')
            
            structure_parts.append("**RETURN FLIGHT BOOKING CONFIRMED:**")
            structure_parts.append(f"- Flight: {state['destination']} → {state.get('origin', 'Origin')}")
            structure_parts.append(f"- Departure: {departure_time}")
            structure_parts.append(f"- Arrival: {arrival_time}")
            structure_parts.append(f"- Cost: ₹{return_leg.get('price', 'TBD')}")
            structure_parts.append("")
            
            structure_parts.append("**Departure Day Schedule:**")
            structure_parts.append("- 8:00 AM: Breakfast and check-out")
            if departure_time != 'TBD':
                try:
                    dept_time = datetime.strptime(departure_time, "%H:%M")
                    leave_time = (dept_time - timedelta(hours=3)).strftime("%H:%M")
                    structure_parts.append(f"- {leave_time}: Last-minute shopping/sightseeing")
                    airport_time = (dept_time - timedelta(hours=2)).strftime("%H:%M")
                    structure_parts.append(f"- {airport_time}: Leave for airport")
                    structure_parts.append(f"- {departure_time}: Flight departure")
                    structure_parts.append(f"- {arrival_time}: Arrival at {state.get('origin', 'home')}")
                except:
                    structure_parts.append("- Morning: Final activities and airport departure")
            
        elif return_leg.get('mode') == 'train':
            departure_time = return_leg.get('departure_time', 'TBD')
            arrival_time = return_leg.get('arrival_time', 'TBD')
            
            structure_parts.append("**RETURN TRAIN BOOKING CONFIRMED:**")
            structure_parts.append(f"- Train: {state['destination']} → {state.get('origin', 'Origin')}")
            structure_parts.append(f"- Departure: {departure_time}")
            structure_parts.append(f"- Arrival: {arrival_time}")
            structure_parts.append(f"- Cost: ₹{return_leg.get('price', 'TBD')}")
            structure_parts.append("")
            
            structure_parts.append("**Departure Day Schedule:**")
            structure_parts.append("- 8:00 AM: Breakfast and check-out")
            if departure_time != 'TBD':
                try:
                    dept_time = datetime.strptime(departure_time, "%H:%M")
                    leave_time = (dept_time - timedelta(hours=2)).strftime("%H:%M")
                    structure_parts.append(f"- {leave_time}: Final sightseeing or shopping")
                    station_time = (dept_time - timedelta(minutes=30)).strftime("%H:%M")
                    structure_parts.append(f"- {station_time}: Reach railway station")
                    structure_parts.append(f"- {departure_time}: Train departure")
                    structure_parts.append(f"- {arrival_time}: Arrival at {state.get('origin', 'home')}")
                except:
                    structure_parts.append("- Check-out and railway station departure")
    
    return "\n".join(structure_parts)


def get_time_period(time_str):
    """Determine time period from time string"""
    if not time_str or time_str == 'TBD':
        return "Time TBD"
    
    try:
        # Parse time (assuming format like "09:00" or "9:00 AM")
        time_clean = time_str.replace(' AM', '').replace(' PM', '').replace(' am', '').replace(' pm', '')
        
        if ':' in time_clean:
            hour = int(time_clean.split(':')[0])
        else:
            hour = int(time_clean)
        
        # Handle 12-hour format
        if 'PM' in time_str.upper() or 'pm' in time_str:
            if hour != 12:
                hour += 12
        elif 'AM' in time_str.upper() or 'am' in time_str:
            if hour == 12:
                hour = 0
        
        if 5 <= hour < 12:
            return "Morning"
        elif 12 <= hour < 17:
            return "Afternoon"
        elif 17 <= hour < 21:
            return "Evening"
        else:
            return "Night"
            
    except (ValueError, IndexError):
        return "Time TBD"


def create_enhanced_fallback_itinerary(state: TravelState):
    """Create enhanced fallback itinerary with specific booking recommendations"""
    places = state.get("places", [])
    route = state.get("optimal_route", places) or []
    travel_info = state.get("travel_info", {})
    accommodations = state.get("accommodations", [])
    effective_days = state.get("effective_days", state["days"])
    
    fallback = f"""# Complete Travel Itinerary: {state['destination']}

## Trip Overview
- **Destination**: {state['destination']}
- **Origin**: {state.get('origin', 'Not specified')}
- **Duration**: {state['days']} days
- **Effective Days**: {effective_days} days
- **Travel Dates**: {state.get('start_date', 'TBD')} to {state.get('end_date', 'TBD')}
- **Theme**: {state.get('theme', 'General')}
- **Budget**: {state.get('budget', 'Medium')}

"""

    # Extract specific booking recommendations from transport data
    recommendations = travel_info.get('recommendations', []) if travel_info else []
    if recommendations:
        best_option = recommendations[0]
        outbound = best_option.get('outbound', {})
        return_leg = best_option.get('return', {})
        
        fallback += f"""## RECOMMENDED BOOKINGS

### Transportation (Book Immediately)
**Total Cost: Rs {best_option.get('total_price', 'TBD'):,}**

**Outbound Journey ({state.get('start_date', 'TBD')})**
- **Mode**: {outbound.get('mode', 'Transport').title()}
- **Route**: {state.get('origin', 'Origin')} → {state['destination']}
- **Time**: {outbound.get('departure_time', 'TBD')} - {outbound.get('arrival_time', 'TBD')}
- **Cost**: Rs {outbound.get('price', 'TBD')}
- **Duration**: {outbound.get('duration', 'TBD')}

**Return Journey ({state.get('end_date', 'TBD')})**
- **Mode**: {return_leg.get('mode', 'Transport').title()}  
- **Route**: {state['destination']} → {state.get('origin', 'Origin')}
- **Time**: {return_leg.get('departure_time', 'TBD')} - {return_leg.get('arrival_time', 'TBD')}
- **Cost**: Rs {return_leg.get('price', 'TBD')}
- **Duration**: {return_leg.get('duration', 'TBD')}

### Alternative Options Available
"""
        # Add alternative recommendations
        for i, alt_rec in enumerate(recommendations[1:3], 2):
            alt_total = alt_rec.get('total_price', 'TBD')
            alt_outbound = alt_rec.get('outbound', {})
            alt_return = alt_rec.get('return', {})
            fallback += f"""**Option {i}**: {alt_outbound.get('mode', '').title()} + {alt_return.get('mode', '').title()} = Rs {alt_total:,} (Convenience: {alt_rec.get('convenience_score', 'N/A')}/10)
"""
        fallback += "\n"

    # Travel Information
    elif travel_info and travel_info.get('planned'):
        fallback += f"""## Travel Information
- **Route**: {travel_info.get('origin', 'Origin')} → {state['destination']}
- **Travel Impact**: {travel_info.get('travel_time_impact', 0)} day(s)
- **Recommendation**: Book travel by road or check local transport options
"""
        fallback += "\n"
    
    # Accommodation Bookings with specific recommendations
    if accommodations:
        fallback += f"""## ACCOMMODATION BOOKINGS ({len(accommodations)} Options)

### Primary Recommendation
**{accommodations[0].get('name', 'Hotel Option 1')}**
- **Type**: {accommodations[0].get('type', 'Hotel')}
- **Location**: {accommodations[0].get('location', 'Central')}
- **Price Range**: {accommodations[0].get('price_range', 'Mid-range')} per night
- **Why Choose**: {accommodations[0].get('strategic_reason', 'Good location for planned activities')}
- **Booking Action**: Call directly or use booking platforms like MakeMyTrip, Booking.com

### Alternative Options
"""
        for i, acc in enumerate(accommodations[1:3], 2):
            fallback += f"""**Option {i}: {acc.get('name', f'Hotel Option {i}')}**
- Location: {acc.get('location', 'Central')} | Type: {acc.get('type', 'Hotel')} | Price: {acc.get('price_range', 'Mid-range')}

"""
    
    # Places to Visit with booking requirements
    if route:
        fallback += f"""## ATTRACTIONS & ACTIVITIES ({len(route)} locations)

### Pre-booking Required
"""
        booking_required = []
        walk_in_ok = []
        
        for place in route:
            place_type = place.get('type', '').lower()
            # Categorize based on type
            if any(keyword in place_type for keyword in ['museum', 'fort', 'palace', 'park', 'sanctuary', 'reserve']):
                booking_required.append(place)
            else:
                walk_in_ok.append(place)
        
        if booking_required:
            for i, place in enumerate(booking_required, 1):
                fallback += f"""**{i}. {place.get('name', 'Attraction')}**
- **Type**: {place.get('type', 'attraction').title()}
- **Location**: {place.get('address', 'Address not available')}
- **Rating**: {place.get('rating', 'N/A')} stars
- **Booking**: Advance booking recommended
"""
        
        if walk_in_ok:
            fallback += f"""
### Walk-in Visits
"""
            for i, place in enumerate(walk_in_ok, 1):
                fallback += f"""**{i}. {place.get('name', 'Place')}**
- **Type**: {place.get('type', 'attraction').title()}
- **Location**: {place.get('address', 'Address not available')}
- **Rating**: {place.get('rating', 'N/A')} stars
"""
        fallback += "\n"
    
    # Detailed Daily Schedule with specific timings
    travel_impact = travel_info.get('travel_time_impact', 0) if travel_info else 0
    is_travel_day = travel_impact > 0 and state.get('origin')
    
    fallback += """## DETAILED DAILY SCHEDULE

"""
    
    if route:
        places_per_day = max(1, len(route) // effective_days)
        route_index = 0
        
        for day in range(1, state['days'] + 1):
            if day == 1 and is_travel_day:
                # Travel day with specific transport details
                if recommendations:
                    outbound = recommendations[0].get('outbound', {})
                    fallback += f"""### Day 1: Departure & Travel
**CONFIRMED TRANSPORT**: {outbound.get('mode', 'Transport').title()}
- **6:00 AM**: Final packing and breakfast
- **{outbound.get('departure_time', '8:00 AM')}**: Departure from {state.get('origin', 'origin')}
- **{outbound.get('arrival_time', '12:00 PM')}**: Arrival at {state['destination']}
- **2:00 PM**: Check-in at {accommodations[0].get('name', 'hotel') if accommodations else 'hotel'}
- **4:00 PM**: Local orientation and rest
- **7:30 PM**: Dinner and early rest

**Transport Cost**: Rs {outbound.get('price', 'TBD')} | Duration: {outbound.get('duration', 'TBD')}

"""
                else:
                    fallback += f"""### Day 1: Departure & Travel
- **8:00 AM**: Departure from {state.get('origin', 'origin')}
- **Afternoon**: Travel and arrival at {state['destination']}
- **Evening**: Check-in and local orientation

"""
                continue
            
            fallback += f"""### Day {day}: Exploration
**Accommodation**: {accommodations[0].get('name', 'Your hotel') if accommodations else 'Hotel'}

**Morning (8:00 AM - 12:00 PM)**
- **8:00 AM**: Breakfast at hotel
"""
            
            # Add specific places with timing
            if route_index < len(route):
                place = route[route_index]
                fallback += f"""- **9:30 AM**: Visit {place.get('name', 'Attraction')}
  - Type: {place.get('type', 'attraction').title()}
  - Address: {place.get('address', 'Check location')}
  - Duration: 2-3 hours (recommended)
"""
                route_index += 1
            
            fallback += f"""
**Afternoon (12:00 PM - 6:00 PM)**
- **12:30 PM**: Lunch at local restaurant
"""
            
            if route_index < len(route) and places_per_day > 1:
                place = route[route_index]
                fallback += f"""- **2:30 PM**: Visit {place.get('name', 'Attraction')}
  - Type: {place.get('type', 'attraction').title()}
  - Address: {place.get('address', 'Check location')}
  - Duration: 2-3 hours (recommended)
"""
                route_index += 1
            
            fallback += f"""- **5:00 PM**: Local shopping or cafe time

**Evening (6:00 PM onwards)**
- **7:30 PM**: Dinner at recommended restaurant
- **9:00 PM**: Leisure time and plan next day

"""
    
    # Final day with return journey details
    if recommendations and state['days'] > 1:
        return_leg = recommendations[0].get('return', {})
        fallback += f"""### Day {state['days']}: Departure
**CONFIRMED RETURN**: {return_leg.get('mode', 'Transport').title()}
- **8:00 AM**: Breakfast and check-out from {accommodations[0].get('name', 'hotel') if accommodations else 'hotel'}
- **10:00 AM**: Final shopping or quick local visit
- **{return_leg.get('departure_time', '2:00 PM')}**: Departure from {state['destination']}
- **{return_leg.get('arrival_time', '6:00 PM')}**: Arrival at {state.get('origin', 'home')}

**Return Transport Cost**: Rs {return_leg.get('price', 'TBD')} | Duration: {return_leg.get('duration', 'TBD')}
"""
    
    # Action items and budget
    total_transport = recommendations[0].get('total_price', 0) if recommendations else 0
    estimated_accommodation = effective_days * 2000  # Rs 2000 per night average
    estimated_daily = effective_days * 2500  # Rs 2500 per day for meals, local transport, activities
    total_estimated = total_transport + estimated_accommodation + estimated_daily
    
    fallback += f"""
## IMMEDIATE ACTION ITEMS

### Book Now (Priority 1)
- [ ] **Transport**: {recommendations[0].get('type', 'Flight/Train').replace('_', ' + ').title() if recommendations else 'Travel arrangement'} - Rs {total_transport:,}
- [ ] **Accommodation**: {accommodations[0].get('name', 'Hotel booking') if accommodations else 'Hotel booking'} for {effective_days} nights
- [ ] **Travel Insurance**: Purchase comprehensive cover

### This Week (Priority 2)  
- [ ] Download offline maps for {state['destination']}
- [ ] Research local emergency contacts and hospital locations
- [ ] Check weather forecast and pack accordingly
- [ ] Inform bank about travel dates and destination

### Day Before Departure
- [ ] Confirm all transport timings and terminal/platform details
- [ ] Pack all essential documents and medicines
- [ ] Charge devices and download entertainment for journey
- [ ] Check-in online (if flying) and save boarding passes

## ESTIMATED BUDGET BREAKDOWN
- **Transportation**: Rs {total_transport:,}
- **Accommodation** ({effective_days} nights): Rs {estimated_accommodation:,}  
- **Daily Expenses** ({effective_days} days): Rs {estimated_daily:,}
- ****TOTAL ESTIMATED COST**: Rs {total_estimated:,}**

## EMERGENCY INFORMATION
### Important Numbers (Save in Phone)
- Local Emergency: 112
- Police: 100
- Fire: 101
- Medical Emergency: 108
- Tourist Helpline: 1363

### Essential Apps to Download
- Google Maps (download offline maps)
- Google Translate
- Weather app
- Banking apps
- Booking confirmations (screenshot/save offline)

## FINAL REMINDERS
- Keep physical and digital copies of all bookings
- Carry some cash for local vendors and tips
- Respect local customs and dress codes
- Stay hydrated and carry basic medications
- Have a backup plan for weather-dependent activities

**Have a safe and memorable trip to {state['destination']}!**
"""
    
    return fallback