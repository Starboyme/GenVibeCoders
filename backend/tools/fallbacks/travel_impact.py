def calculate_travel_impact_fallback(origin: str, destination: str) -> int:
    """
    Enhanced fallback calculation with better location-specific logic
    Returns number of days that will be impacted by travel
    """
    if not origin or not destination:
        return 0
    
    origin_lower = origin.lower()
    destination_lower = destination.lower()
    
    # Specific mappings for common Indian destinations
    hill_stations_remote = {
        'coorg': {'nearest_airport': 'mangalore', 'road_time_hours': 3, 'impact_days': 1},
        'kodagu': {'nearest_airport': 'mangalore', 'road_time_hours': 3, 'impact_days': 1},
        'ooty': {'nearest_airport': 'coimbatore', 'road_time_hours': 3, 'impact_days': 1},
        'ootacamund': {'nearest_airport': 'coimbatore', 'road_time_hours': 3, 'impact_days': 1},
        'munnar': {'nearest_airport': 'cochin', 'road_time_hours': 4, 'impact_days': 1},
        'manali': {'nearest_airport': 'chandigarh', 'road_time_hours': 8, 'impact_days': 2},
        'shimla': {'nearest_airport': 'chandigarh', 'road_time_hours': 4, 'impact_days': 1},
        'darjeeling': {'nearest_airport': 'bagdogra', 'road_time_hours': 3, 'impact_days': 1},
        'gangtok': {'nearest_airport': 'bagdogra', 'road_time_hours': 4, 'impact_days': 1},
        'mussoorie': {'nearest_airport': 'dehradun', 'road_time_hours': 1, 'impact_days': 1},
        'nainital': {'nearest_airport': 'pantnagar', 'road_time_hours': 2, 'impact_days': 1},
        'mcleodganj': {'nearest_airport': 'dharamshala', 'road_time_hours': 1, 'impact_days': 1},
        'kasol': {'nearest_airport': 'chandigarh', 'road_time_hours': 6, 'impact_days': 2},
        'rishikesh': {'nearest_airport': 'dehradun', 'road_time_hours': 1, 'impact_days': 0},
        'haridwar': {'nearest_airport': 'dehradun', 'road_time_hours': 1, 'impact_days': 0},
        'almora': {'nearest_airport': 'pantnagar', 'road_time_hours': 4, 'impact_days': 1},
        'lansdowne': {'nearest_airport': 'dehradun', 'road_time_hours': 3, 'impact_days': 1},
        'kasauli': {'nearest_airport': 'chandigarh', 'road_time_hours': 2, 'impact_days': 1},
        'dalhousie': {'nearest_airport': 'pathankot', 'road_time_hours': 2, 'impact_days': 1},
        'khajjiar': {'nearest_airport': 'pathankot', 'road_time_hours': 3, 'impact_days': 1},
        'kullu': {'nearest_airport': 'bhuntar', 'road_time_hours': 1, 'impact_days': 1},
        'spiti': {'nearest_airport': 'chandigarh', 'road_time_hours': 12, 'impact_days': 2},
        'ladakh': {'nearest_airport': 'leh', 'road_time_hours': 1, 'impact_days': 1},
        'leh': {'nearest_airport': 'leh', 'road_time_hours': 0, 'impact_days': 1},
        'srinagar': {'nearest_airport': 'srinagar', 'road_time_hours': 0, 'impact_days': 1},
        'gulmarg': {'nearest_airport': 'srinagar', 'road_time_hours': 2, 'impact_days': 1},
        'pahalgam': {'nearest_airport': 'srinagar', 'road_time_hours': 3, 'impact_days': 1},
        'sonamarg': {'nearest_airport': 'srinagar', 'road_time_hours': 3, 'impact_days': 1},
        
        # South India hill stations
        'kodaikanal': {'nearest_airport': 'madurai', 'road_time_hours': 3, 'impact_days': 1},
        'yercaud': {'nearest_airport': 'salem', 'road_time_hours': 1, 'impact_days': 0},
        'coonoor': {'nearest_airport': 'coimbatore', 'road_time_hours': 2, 'impact_days': 1},
        'kotagiri': {'nearest_airport': 'coimbatore', 'road_time_hours': 2, 'impact_days': 1},
        'wayanad': {'nearest_airport': 'calicut', 'road_time_hours': 2, 'impact_days': 1},
        'thekkady': {'nearest_airport': 'madurai', 'road_time_hours': 3, 'impact_days': 1},
        'ponmudi': {'nearest_airport': 'trivandrum', 'road_time_hours': 2, 'impact_days': 1},
        'vagamon': {'nearest_airport': 'cochin', 'road_time_hours': 3, 'impact_days': 1},
        
        # Western Ghats
        'sakleshpur': {'nearest_airport': 'bangalore', 'road_time_hours': 4, 'impact_days': 1},
        'chikmagalur': {'nearest_airport': 'bangalore', 'road_time_hours': 4, 'impact_days': 1},
        'kemmanagundi': {'nearest_airport': 'bangalore', 'road_time_hours': 5, 'impact_days': 1},
        'kudremukh': {'nearest_airport': 'mangalore', 'road_time_hours': 3, 'impact_days': 1},
        
        # Northeast
        'shillong': {'nearest_airport': 'guwahati', 'road_time_hours': 3, 'impact_days': 1},
        'cherrapunji': {'nearest_airport': 'guwahati', 'road_time_hours': 4, 'impact_days': 1},
        'kaziranga': {'nearest_airport': 'guwahati', 'road_time_hours': 4, 'impact_days': 1},
        'tawang': {'nearest_airport': 'guwahati', 'road_time_hours': 8, 'impact_days': 2},
        'ziro': {'nearest_airport': 'guwahati', 'road_time_hours': 6, 'impact_days': 2},
        'kohima': {'nearest_airport': 'dimapur', 'road_time_hours': 2, 'impact_days': 1},
        'imphal': {'nearest_airport': 'imphal', 'road_time_hours': 0, 'impact_days': 1},
        'aizawl': {'nearest_airport': 'lengpui', 'road_time_hours': 1, 'impact_days': 1},
        
        # Rajasthan remote areas
        'pushkar': {'nearest_airport': 'jaipur', 'road_time_hours': 3, 'impact_days': 1},
        'mount_abu': {'nearest_airport': 'udaipur', 'road_time_hours': 3, 'impact_days': 1},
        'bundi': {'nearest_airport': 'jaipur', 'road_time_hours': 4, 'impact_days': 1},
        'chittorgarh': {'nearest_airport': 'udaipur', 'road_time_hours': 2, 'impact_days': 1},
        'bikaner': {'nearest_airport': 'jodhpur', 'road_time_hours': 3, 'impact_days': 1},
        'jaisalmer': {'nearest_airport': 'jodhpur', 'road_time_hours': 5, 'impact_days': 2},
    }
    
    # Major cities with direct flight/train connectivity (minimal impact)
    major_cities = {
        'mumbai': 0, 'bangalore': 0, 'delhi': 0, 'chennai': 0, 'kolkata': 0,
        'hyderabad': 0, 'pune': 0, 'ahmedabad': 0, 'surat': 0, 'jaipur': 0,
        'lucknow': 0, 'kanpur': 0, 'nagpur': 0, 'indore': 0, 'thane': 0,
        'bhopal': 0, 'visakhapatnam': 0, 'pimpri': 0, 'patna': 0, 'vadodara': 0,
        'ludhiana': 0, 'agra': 0, 'nashik': 0, 'faridabad': 0, 'meerut': 0,
        'rajkot': 0, 'kalyan': 0, 'vasai': 0, 'varanasi': 0, 'srinagar': 1,
        'aurangabad': 0, 'dhanbad': 0, 'amritsar': 0, 'allahabad': 0, 'ranchi': 0,
        'howrah': 0, 'coimbatore': 0, 'jabalpur': 0, 'gwalior': 0, 'vijayawada': 0,
        'jodhpur': 0, 'madurai': 0, 'raipur': 0, 'kota': 0, 'chandigarh': 0,
        'guwahati': 1, 'solapur': 0, 'tiruchirappalli': 0, 'hubli': 0, 'mysore': 0,
        'tiruppur': 0, 'moradabad': 0, 'salem': 0, 'guntur': 0, 'bhiwandi': 0,
        'saharanpur': 0, 'gorakhpur': 0, 'bikaner': 1, 'amravati': 0, 'noida': 0,
        'jamshedpur': 0, 'bhilai': 0, 'warangal': 0, 'cuttack': 0, 'firozabad': 0,
        'kochi': 0, 'cochin': 0, 'ernakulam': 0, 'trivandrum': 0, 'calicut': 0,
        'kozhikode': 0, 'thrissur': 0, 'kollam': 0, 'alappuzha': 0, 'kottayam': 0,
        'goa': 0, 'panaji': 0, 'margao': 0, 'vasco': 0
    }
    
    # Beach destinations (usually good connectivity)
    beach_destinations = {
        'goa': 0, 'pondicherry': 0, 'puducherry': 0, 'varkala': 0, 'kovalam': 0,
        'mamallapuram': 0, 'mahabalipuram': 0, 'dhanushkodi': 1, 'rameswaram': 1,
        'digha': 1, 'puri': 1, 'konark': 1, 'chandipur': 1, 'gopalpur': 1,
        'vishakhapatnam': 0, 'vizag': 0, 'araku': 1, 'hampi': 1, 'badami': 1,
        'aihole': 1, 'pattadakal': 1, 'bijapur': 1, 'gokarna': 1, 'karwar': 1,
        'udupi': 1, 'mangalore': 0, 'kannur': 1, 'bekal': 1, 'kasaragod': 1
    }
    
    # International destinations
    international_indicators = [
        'usa', 'america', 'united states', 'new york', 'california', 'washington',
        'uk', 'england', 'london', 'scotland', 'wales', 'britain', 'great britain',
        'europe', 'france', 'paris', 'germany', 'berlin', 'italy', 'rome', 'spain',
        'netherlands', 'amsterdam', 'switzerland', 'sweden', 'norway', 'denmark',
        'canada', 'toronto', 'vancouver', 'montreal', 'ottawa',
        'australia', 'sydney', 'melbourne', 'perth', 'brisbane', 'adelaide',
        'singapore', 'malaysia', 'kuala lumpur', 'thailand', 'bangkok', 'phuket',
        'indonesia', 'bali', 'jakarta', 'philippines', 'manila', 'cebu',
        'japan', 'tokyo', 'kyoto', 'osaka', 'china', 'beijing', 'shanghai',
        'south korea', 'seoul', 'hong kong', 'macau', 'taiwan', 'taipei',
        'dubai', 'uae', 'abu dhabi', 'qatar', 'doha', 'kuwait', 'bahrain',
        'saudi arabia', 'riyadh', 'jeddah', 'oman', 'muscat',
        'sri lanka', 'colombo', 'maldives', 'male', 'nepal', 'kathmandu',
        'bhutan', 'thimphu', 'bangladesh', 'dhaka', 'myanmar', 'yangon',
        'vietnam', 'ho chi minh', 'hanoi', 'cambodia', 'phnom penh',
        'south africa', 'cape town', 'johannesburg', 'egypt', 'cairo',
        'turkey', 'istanbul', 'russia', 'moscow', 'brazil', 'rio de janeiro'
    ]
    
    # Check for specific hill station or remote destination
    for place, info in hill_stations_remote.items():
        if place in destination_lower or any(part in destination_lower for part in place.split('_')):
            print(f"🗺️ Destination '{destination}' identified as remote location")
            print(f"   Nearest airport: {info['nearest_airport']}")
            print(f"   Road travel: {info['road_time_hours']} hours")
            
            # Check if origin is also remote
            origin_is_major = any(city in origin_lower for city in major_cities.keys())
            if not origin_is_major:
                # Both origin and destination are remote
                return info['impact_days'] + 1
            else:
                return info['impact_days']
    
    # Check if destination is a major city
    for city, impact in major_cities.items():
        if city in destination_lower:
            print(f"🏙️ Destination '{destination}' identified as major city")
            return impact
    
    # Check if destination is a beach location
    for beach, impact in beach_destinations.items():
        if beach in destination_lower:
            print(f"🏖️ Destination '{destination}' identified as beach destination")
            return impact
    
    # Check for international travel
    origin_is_international = any(country in origin_lower for country in international_indicators)
    destination_is_international = any(country in destination_lower for country in international_indicators)
    
    if origin_is_international or destination_is_international:
        print(f"🌍 International travel detected")
        return 2  # 2 days lost for international travel (jet lag, long flights, etc.)
    
    # Check for inter-state vs intra-state travel (rough heuristic)
    indian_states = {
        'maharashtra': ['mumbai', 'pune', 'nagpur', 'nashik', 'aurangabad'],
        'karnataka': ['bangalore', 'mysore', 'hubli', 'mangalore', 'belgaum', 'coorg'],
        'tamil_nadu': ['chennai', 'coimbatore', 'madurai', 'salem', 'tiruchirapalli', 'ooty'],
        'kerala': ['kochi', 'trivandrum', 'calicut', 'thrissur', 'munnar'],
        'gujarat': ['ahmedabad', 'surat', 'vadodara', 'rajkot'],
        'rajasthan': ['jaipur', 'jodhpur', 'udaipur', 'bikaner', 'pushkar'],
        'uttar_pradesh': ['lucknow', 'kanpur', 'agra', 'varanasi', 'allahabad'],
        'west_bengal': ['kolkata', 'howrah', 'darjeeling'],
        'delhi': ['delhi', 'new delhi'],
        'punjab': ['ludhiana', 'amritsar', 'chandigarh'],
        'haryana': ['faridabad', 'gurgaon', 'chandigarh'],
        'himachal_pradesh': ['shimla', 'manali', 'dharamshala'],
        'uttarakhand': ['dehradun', 'haridwar', 'rishikesh', 'nainital'],
        'goa': ['panaji', 'margao', 'vasco'],
        'assam': ['guwahati', 'kaziranga'],
        'odisha': ['bhubaneswar', 'cuttack', 'puri'],
        'andhra_pradesh': ['hyderabad', 'visakhapatnam', 'vijayawada'],
        'telangana': ['hyderabad'],
        'jharkhand': ['ranchi', 'jamshedpur'],
        'bihar': ['patna'],
        'madhya_pradesh': ['bhopal', 'indore', 'jabalpur']
    }
    
    origin_state = None
    destination_state = None
    
    for state, cities in indian_states.items():
        if any(city in origin_lower for city in cities):
            origin_state = state
        if any(city in destination_lower for city in cities):
            destination_state = state
    
    if origin_state and destination_state:
        if origin_state == destination_state:
            print(f"🗺️ Intra-state travel within {origin_state.replace('_', ' ').title()}")
            return 0  # Same state, good connectivity
        else:
            print(f"🗺️ Inter-state travel: {origin_state.replace('_', ' ').title()} to {destination_state.replace('_', ' ').title()}")
            return 1  # Different states, might need a day
    
    # Default fallback based on distance heuristics
    print(f"🗺️ Using distance heuristic for {origin} to {destination}")
    
    # Very rough distance estimation based on common knowledge
    if any(keyword in destination_lower for keyword in ['north', 'kashmir', 'ladakh', 'himachal', 'uttarakhand']) and \
       any(keyword in origin_lower for keyword in ['south', 'kerala', 'tamil', 'karnataka', 'andhra']):
        return 2  # North-South travel
    elif any(keyword in destination_lower for keyword in ['east', 'assam', 'meghalaya', 'manipur', 'nagaland']) and \
         any(keyword in origin_lower for keyword in ['west', 'maharashtra', 'gujarat', 'rajasthan']):
        return 2  # East-West travel
    
    # Final default
    return 1  # Conservative estimate - 1 day impact

# Test function to validate the fallback logic
def test_travel_impact():
    """Test the travel impact calculation with common examples"""
    test_cases = [
        ("Bangalore", "Coorg", 1),
        ("Mumbai", "Goa", 0),
        ("Delhi", "Manali", 2),
        ("Chennai", "Ooty", 1),
        ("Bangalore", "Mumbai", 0),
        ("Delhi", "Bangkok", 2),
        ("Kolkata", "Darjeeling", 1),
        ("Hyderabad", "Araku", 1),
        ("", "Coorg", 0),
        ("Bangalore", "", 0)
    ]
    
    print("🧪 Testing travel impact calculations:")
    for origin, destination, expected in test_cases:
        result = calculate_travel_impact_fallback(origin, destination)
        status = "✅" if result == expected else "❌"
        print(f"{status} {origin} → {destination}: {result} days (expected: {expected})")

if __name__ == "__main__":
    test_travel_impact()