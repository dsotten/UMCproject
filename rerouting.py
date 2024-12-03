import requests
import heapq
import math

API_KEY = 'AIzaSyBzoCUm8NNP68qFTVdWHVlX-MfNIjXUwOE'
min_safe_dist = 50
danger_locations = ['bar','liquor_store','casino','night_club']

# place_types = ['bar','liquor_store','casino','night_club']
# place_types2 = ['convenience_store','drugstore','gas_station','supermarket']
# high_risk = False #checks place_types2 if True
# if (high_risk): place_types += place_types2


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

def query_alc_place_api(waypoint, radius, place_types=danger_locations, opennow=True):
    # Placeholder function for querying the Google Places API
    lat, lng = waypoint
    locations = []

    for avoid_loc in place_types:
        if opennow:
            radius_url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&type={avoid_loc}&opennow&key={API_KEY}'
        else:
            radius_url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&type={avoid_loc}&key={API_KEY}'
        response = requests.get(radius_url)
        data = response.json()
        
        if response.status_code == 200 and data['status'] == 'OK':
                for result in data['results']:
                    lat = result['geometry']['location']['lat']
                    lon = result['geometry']['location']['lng']
                    locations += [(lat, lon)]
    return locations

    # url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&type=bar|liquor_store&key={API_KEY}"

def find_avoid_locs(start, end, distance=None, opennow=False):
    lat_s, lon_s = start
    lat_e, lon_e = end
    midpoint = (lat_s+lat_e)/2, (lon_s+lon_e)/2

    if distance is None:
        distance = haversine_distance(start, end)
    radius = max(min_safe_dist*2,distance/2)
    nearby_avoid_locs = query_alc_place_api(midpoint,radius=radius,opennow=opennow)

    return nearby_avoid_locs

def find_danger_locs(start, end, avoid_locs):
    danger_locs = []
    for location in avoid_locs:
        if is_point_near_route_segment(location, start, end):
            danger_locs += [location]
    return danger_locs

#Tests all the routes Google returns and finds the one least affected by alcohol establishments
def find_best_alt_route(start, destination):
    possible_routes = f'https://maps.googleapis.com/maps/api/directions/json?origin={start}&destination={destination}&units=metric&alternatives=true&key={API_KEY}'
    api_ct = 1
    
    routes_request = requests.get(possible_routes)
    possible_routes_json = routes_request.json()
    # print(str(possible_routes_json))
    routes = possible_routes_json['routes']
    alc_locs_per_route = []

    if routes_request.status_code == 200 and possible_routes_json['status'] == 'OK':
        for route in routes:
            steps = route['legs'][0]['steps']
            num_danger_locs = 0
            for i in range(len(steps)-1):
                start = steps[i]['start_location']['lat'], steps[i]['start_location']['lng']
                end = steps[i]['end_location']['lat'], steps[i]['end_location']['lng']
                distance = haversine_distance(start, end)
                # print_instruction(steps[i])
                avoid_locs = find_avoid_locs(start,end,distance)
                api_ct += len(danger_locations)
                danger_locs = find_danger_locs(start,end,avoid_locs)
                # print("Dangerous locations on step "+str(i)+": "+str(danger_locs))
                num_danger_locs += len(danger_locs)
            alc_locs_per_route += [num_danger_locs]

        best_route = 0
        min_locs = 0
        max_locs = -1
        if alc_locs_per_route is not []:
            min_locs = float('inf')
            for i in range(len(alc_locs_per_route)):
                num_locs = alc_locs_per_route[i]
                print("Route "+str(i+1)+" passes "+str(num_locs)+" dangerous locations.")
                if num_locs < min_locs: 
                    best_route = i
                    min_locs = num_locs
                if num_locs > max_locs:
                    max_locs = num_locs

        print("Route "+str(best_route+1)+" is safest:")

        ret_dict = {
            'route_json': routes[best_route],
            'danger_locs': min_locs,
            'max_danger_locs': max_locs,
            'num_api_calls': api_ct
        }
        return ret_dict
    else:
        ret_dict = {
            'route_json': 'ERROR',
            'danger_locs': 'ERROR',
            'num_api_calls': api_ct
        }
        return ret_dict
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

def str_instruction(step):
    instruction = step['html_instructions']  # Contains HTML instructions
    distance = step['distance']['text']  # Step distance
    duration = step['duration']['text']  # Step duration

    # Strip HTML tags from the instruction (if needed)
    import re
    clean_instruction = re.sub('<.*?>', '', instruction)  # Remove HTML tags

    # Print step details
    return f"- {clean_instruction} ({distance}, {duration})"

def handler(origin, destination, key, high_risk=False):
    global API_KEY
    global danger_locations
    API_KEY = key
    place_types2 = ['convenience_store','drugstore','gas_station','supermarket']
    if (high_risk): danger_locations += place_types2

    alt_route_dict = find_best_alt_route(origin,destination)
    return alt_route_dict