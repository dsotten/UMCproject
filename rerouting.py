import requests
import heapq
import math

API_KEY = 'AIzaSyBzoCUm8NNP68qFTVdWHVlX-MfNIjXUwOE'

url = f'https://maps.googleapis.com/maps/api/directions/json?origin=40.748817,-73.985428&destination=40.785091,-73.968285&key={API_KEY}'

# Constants for the algorithm
CHECK_THRESHOLD_DISTANCE = 1000  # Minimum distance (in meters) before checking for alc_loc
CHECK_INTERVAL = 500  # Distance interval (in meters) for alc_loc checks
check_radius = int(2*CHECK_INTERVAL/3) #2/3s of check interval, so there's some overlap between points
min_safe_dist = 50
MAX_ALTERNATIVE_SEARCH_RADIUS = 2000  # Max radius to search for alternative waypoints

place_types = ['bar','liquor_store','casino','night_club']
place_types2 = ['convenience_store','drugstore','gas_station','supermarket']
high_risk = False #checks place_types2 if True
if (high_risk): place_types += place_types2

def haversine_distance(coord1, coord2):
    """Calculate the distance between two points on Earth."""
    
    # Radius of the Earth in meters
    R = 6371000
    lat1, lon1 = coord1
    lat2, lon2 = coord2    

    # Convert latitude and longitude from degrees to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    # Haversine formula
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Distance in meters
    distance = R * c
    return distance

def is_point_near_route_segment(point, start_point, end_point, max_distance=min_safe_dist):
    """
    Determine if a point is within a certain distance of a line segment.
    
    Args:
        point (tuple): Coordinate to check (lat, lon)
        start_point (tuple): Starting point of the line segment (lat, lon)
        end_point (tuple): Ending point of the line segment (lat, lon)
        max_distance (float): Maximum allowed distance from the line (default: MIN_SAFE_DISTANCE)
    
    Returns:
        bool: True if point is near the line segment, False otherwise
    """
    # Extract coordinates
    px, py = point
    x1, y1 = start_point
    x2, y2 = end_point
    
    # Calculate line segment length
    line_length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    # If line segment is essentially a point
    if line_length == 0:
        return haversine_distance(point, start_point) <= max_distance
    
    # Calculate projection of point onto the line
    # Parametric representation of line
    t = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / (line_length**2)
    
    # Clamp t to [0,1] to ensure point is within line segment
    t = max(0, min(1, t))
    
    # Calculate closest point on the line segment
    closest_x = x1 + t * (x2 - x1)
    closest_y = y1 + t * (y2 - y1)
    
    # Calculate distance between point and closest point
    distance = haversine_distance(point, (closest_x, closest_y))
    
    # Check if distance is within max_distance
    return distance <= max_distance

def generate_nearby_safe_points(dangerous_point, alc_locations, travel_direction, search_radius=CHECK_INTERVAL):
    """
    Find alternative safe points around a dangerous location.
    
    Args:
        dangerous_point (tuple): Coordinates of the dangerous location (lat, lon)
        dangerous_direction (coordinate): Average direction of alcohol locations
        search_radius (int): Radius to search for alternative points
    
    Returns:
        list: List of safe alternative point coordinates
    """
    lat, lon = dangerous_point
    alt_points = []

    location_info = analyze_alcohol_locations(dangerous_point,alc_locations)
    dangerous_direction = location_info['average_direction']

    # Generate alternative points in different directions
    directions = [
        (0, 1),    # North
        (0, -1),   # South
        (1, 0),    # East
        (-1, 0),   # West
        (1, 1),    # Northeast
        (-1, -1),  # Southwest
        (1, -1),   # Southeast
        (-1, 1)    # Northwest
    ]

    if dangerous_direction:
        if dangerous_direction >= 315 or dangerous_direction <= 45:
            directions = [
                (0, -1),   # South
                (1, 0),    # East
                (-1, 0),   # West
                (-1, -1),  # Southwest
                (1, -1),   # Southeast
            ]
        elif dangerous_direction >= 45 and dangerous_direction <= 135:
            directions = [
                (0, 1),    # North
                (0, -1),   # South
                (-1, 0),   # West
                (-1, -1),  # Southwest
                (-1, 1)    # Northwest
            ]
        elif dangerous_direction >= 135 and dangerous_direction <= 225:
            directions = [
                (0, 1),    # North
                (1, 0),    # East
                (-1, 0),   # West
                (1, 1),    # Northeast
                (-1, 1)    # Northwest
            ]
        elif dangerous_direction >= 225 and dangerous_direction <= 315:
            directions = [
        (0, 1),    # North
        (0, -1),   # South
        (1, 0),    # East
        (1, 1),    # Northeast
        (1, -1),   # Southeast
    ]

    for dx, dy in directions:
        # Calculate new point slightly offset from dangerous location
        new_lat = lat + (dx * (search_radius / 111000))  # ~111km per degree of latitude
        new_lon = lon + (dy * (search_radius / (111000 * math.cos(math.radians(lat)))))
        
        alternative_point = (new_lat, new_lon)
        alt_points.append(alternative_point)
    
    return alt_points

def calculate_direction(pt1, pt2):
    """
    Calculate the initial bearing/direction from point 1 to point 2.
    
    Args:
        pt1 (tuple): Starting point coordinates (lat1, lon1)
        pt2 (tuple): Ending point coordinates (lat2, lon2)
    
    Returns:
        float: Bearing in degrees (0-360, where 0 is North, 90 is East, etc.)
    """
    lat1, lon1 = math.radians(pt1[0]), math.radians(pt1[1])
    lat2, lon2 = math.radians(pt2[0]), math.radians(pt2[1])
    
    # Calculate differences
    delta_lon = lon2 - lon1
    
    # Calculate initial bearing using spherical trigonometry
    y = math.sin(delta_lon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(delta_lon)
    
    # Convert to degrees and normalize to 0-360 range
    initial_bearing = math.degrees(math.atan2(y, x))
    bearing = (initial_bearing + 360) % 360
    
    return bearing

def analyze_alcohol_locations(waypoint, alcohol_locations):
    """
    Analyze alcohol locations around a given waypoint.
    
    Args:
        waypoint (tuple): Central point coordinates (lat, lon)
        alcohol_locations (list): List of alcohol location coordinates
    
    Returns:
        dict: Analysis of alcohol locations including:
            - average_distance: Mean distance from waypoint
            - average_direction: Mean direction from waypoint
            - location_count: Number of alcohol locations
    """
    if not alcohol_locations:
        return {
            'average_distance': float('inf'),
            'average_direction': None,
            'location_count': 0
        }
    
    # Calculate distances and directions
    distances = []
    directions = []
    
    for loc in alcohol_locations:
        # Calculate distance
        dist = haversine_distance(waypoint, loc)
        distances.append(dist)
        
        # Calculate direction
        direction = calculate_direction(waypoint, loc)
        directions.append(direction)
    
    # Compute statistics
    avg_distance = sum(distances) / len(distances)
    
    # Calculate average direction (more complex due to circular nature)
    # Use vector-based approach for more accurate average
    avg_x = sum(math.cos(math.radians(d)) for d in directions) / len(directions)
    avg_y = sum(math.sin(math.radians(d)) for d in directions) / len(directions)
    avg_direction = math.degrees(math.atan2(avg_y, avg_x)) % 360
    
    return {
        'average_distance': avg_distance,
        'average_direction': avg_direction,
        'location_count': len(alcohol_locations)
    }

def query_alc_place_api(waypoint, radius=check_radius):
    # Placeholder function for querying the Google Places API
    lat, lng = waypoint
    locations = []

    for avoid_loc in place_types:
        radius_url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&type={avoid_loc}&opennow&key={API_KEY}'
        response = requests.get(radius_url)
        data = response.json()
        
        if response.status_code == 200 and data['status'] == 'OK':
                for result in data['results']:
                    lat = result['geometry']['location']['lat']
                    lon = result['geometry']['location']['lng']
                    locations += [(lat, lon)]
    return locations

    # url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&type=bar|liquor_store&key={API_KEY}"

def find_avoid_locs(start, end, distance=None):
    lat_s, lon_s = start
    lat_e, lon_e = end
    midpoint = (lat_s+lat_e)/2, (lon_s+lon_e)/2

    if distance is None:
        distance = haversine_distance(start, end)
    radius = max(min_safe_dist*2,distance/2)
    nearby_avoid_locs = query_alc_place_api(midpoint,radius=radius)

    return nearby_avoid_locs

def find_danger_locs(start, end, avoid_locs):
    danger_locs = []
    for location in avoid_locs:
        if is_point_near_route_segment(location, start, end):
            danger_locs += [location]
    return danger_locs

#Finds specific waypoints to route through (doesn't work)
def find_safe_route_wp(start, destination):
    default_route = f'https://maps.googleapis.com/maps/api/directions/json?origin={start}&destination={destination}&units=metric&key={API_KEY}'
    default_route_request = requests.get(default_route)
    default_route_json = default_route_request.json()
    # print(default_route_json)
    steps = default_route_json['routes'][0]['legs'][0]['steps']
    prev_step = None
    thru_waypoints = []

    #Check for alcohol locations along current route
    for i in range(len(steps)-1):
        duration = steps[i]['duration']['text']  # Step duration
        start = steps[i]['start_location']['lat'], steps[i]['start_location']['lng']
        end = steps[i]['end_location']['lat'], steps[i]['end_location']['lng']
        distance = haversine_distance(start, end)
        direction = calculate_direction(start, end)
        print_instruction(steps[i])

        avoid_locs = find_avoid_locs(start,end,distance)
        danger_locs = find_danger_locs(start,end,avoid_locs)
        print("Dangerous locations on step "+str(i)+": "+str(danger_locs))
        min_danger_locs = len(danger_locs)

        #Find optimal alternative
        if danger_locs != []:
            possible_alternatives = generate_nearby_safe_points(end, avoid_locs, direction)
            best_alt_waypoint = None
            for waypoint in possible_alternatives:
                tmp_avoid_locs = find_avoid_locs(start,waypoint)
                tmp_danger_locs = find_danger_locs(start,waypoint,tmp_avoid_locs)
                if len(tmp_danger_locs) < min_danger_locs:
                    min_danger_locs = len(tmp_danger_locs)
                    best_alt_waypoint = waypoint

            if best_alt_waypoint is not None:
                thru_waypoints += [best_alt_waypoint]
                print ("New waypoint")

    #pass in best waypoint as start to next loop iteration, and remove it if there isn't another 
    if thru_waypoints != []:
        waypoints_str = "|".join(f"{lat},{lng}" for lat, lng in thru_waypoints)
        print(waypoints_str)
        alt_route_url = (
            f'https://maps.googleapis.com/maps/api/directions/json?'
            f'origin={start}&destination={destination}'
            f'&waypoints={waypoints_str}&units=metric&key={API_KEY}')
        alt_route_request = requests.get(alt_route_url)
        alt_route_json = alt_route_request.json()
        print(alt_route_json)

    return None  # Return None if no route is found

#Tests all the routes Google returns and finds the one least affected by alcohol establishments
def find_safe_route_ar(start, destination):
    possible_routes = f'https://maps.googleapis.com/maps/api/directions/json?origin={start}&destination={destination}&units=metric&alternatives=true&key={API_KEY}'
    possible_routes_json = requests.get(possible_routes).json()
    routes = possible_routes_json['routes']
    alc_locs_per_route = []
    for route in routes:
        steps = route['legs'][0]['steps']
        num_danger_locs = 0
        for i in range(len(steps)-1):
            start = steps[i]['start_location']['lat'], steps[i]['start_location']['lng']
            end = steps[i]['end_location']['lat'], steps[i]['end_location']['lng']
            distance = haversine_distance(start, end)
            # print_instruction(steps[i])

            avoid_locs = find_avoid_locs(start,end,distance)
            danger_locs = find_danger_locs(start,end,avoid_locs)
            # print("Dangerous locations on step "+str(i)+": "+str(danger_locs))
            num_danger_locs += len(danger_locs)
        alc_locs_per_route += [num_danger_locs]

    best_route = -1
    min_locs = float('inf')
    for i in range(len(alc_locs_per_route)):
        num_locs = alc_locs_per_route[i]
        print("Route "+str(i+1)+" passes "+str(num_locs)+" dangerous locations.")
        if num_locs < min_locs: 
            best_route = i
            min_locs = num_locs

    print("Route "+str(best_route+1)+" is safest:")

    final_route_steps = routes[i]['legs'][0]['steps']
    for step in final_route_steps:
        print_instruction(step)

    # print("Route: "+str(route))

def print_instruction(step):
    instruction = step['html_instructions']  # Contains HTML instructions
    distance = step['distance']['text']  # Step distance
    duration = step['duration']['text']  # Step duration

    # Strip HTML tags from the instruction (if needed)
    import re
    clean_instruction = re.sub('<.*?>', '', instruction)  # Remove HTML tags

    # Print step details
    print(f"- {clean_instruction} ({distance}, {duration})")

# Example usage
start_point = '40.748817,-73.985428'  # Example: New York City
destination_point = '40.785091,-73.968285'  # Example: Central Park
# start_point = '37.2731,-76.7133'
# destination_point = '37.27732,-76.70697'
safe_route = find_safe_route_ar(start_point, destination_point)
# print("Safe Route:", safe_route)