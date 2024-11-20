import requests
import heapq
import math

API_KEY = 'AIzaSyBzoCUm8NNP68qFTVdWHVlX-MfNIjXUwOE'

url = f'https://maps.googleapis.com/maps/api/directions/json?origin=40.748817,-73.985428&destination=40.785091,-73.968285&key={API_KEY}'

# Constants for the algorithm
RISK_WEIGHT = 5.0  # Adjust the weight of the risk score to balance distance vs. risk
CHECK_THRESHOLD_DISTANCE = 1000  # Minimum distance (in meters) before checking for alc_loc
CHECK_INTERVAL = 500  # Distance interval (in meters) for alc_loc checks
check_radius = int(2*CHECK_INTERVAL/3) #2/3s of check interval, so there's some overlap between points

place_types = ['bar','liquor_store','casino','night_club']
place_types2 = ['convenience_store','drugstore','gas_station','supermarket']
high_risk = False #checks place_types2 if True
if (high_risk): place_types += place_types2


# Priority Queue implementation using heapq
class PriorityQueue:
    def __init__(self):
        self.elements = []

    def is_empty(self):
        return len(self.elements) == 0

    def push(self, item):
        heapq.heappush(self.elements, item)

    def pop(self):
        return heapq.heappop(self.elements)

# Helper functions
def distance_between(point1, point2):
    origin = f"{point1[0]},{point1[1]}"
    destination = f"{point2[0]},{point2[1]}"
    distance_url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origin}&destinations={destination}&key={API_KEY}"
    response = requests.get(distance_url)
    data = response.json()
    
    if data['status'] == 'OK':
        distance = data['rows'][0]['elements'][0]['distance']['value']  # Distance in meters
        return distance
    else:
        raise Exception(f"Error in Distance Matrix API: {data['status']}")

def haversine_distance(coord1, coord2):
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

def query_alc_place_api(waypoint, radius=None):
    # Placeholder function for querying the Google Places API
    lat, lng = waypoint
    if radius == None: radius = check_radius
    locations = []

    for avoid_loc in place_types:
        radius_url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&type={avoid_loc}&opennow&key={API_KEY}'
        response = requests.get(radius_url)
        data = response.json()
        
        if data['status'] == 'OK':
            locations += data['results']
    return locations

    # url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius}&type=bar|liquor_store&key={API_KEY}"

def find_safe_route(start, destination, alc_loc_radius):
    default_route = f'https://maps.googleapis.com/maps/api/directions/json?origin={start}&destination={destination}&units=metric&key={API_KEY}'
    default_route_request = requests.get(default_route)
    default_route_json = default_route_request.json()
    steps = default_route_json['routes'][0]['legs'][0]['steps']
    prev_step = None
    req_waypoints = []

    step_info_dict = {
        'alc_loc_ct': 0,
        'rerouting_necessary':False,
        # 'start_pt': ,

    }
    step_info = [step_info_dict]*len(steps)
    
    #Check for alcohol locations along current route
    for step in steps:
        distance = step['distance']['text']  # Step distance
        duration = step['duration']['text']  # Step duration
        start_pt = step['start_location']['lat'], step['start_location']['lng']
        nearby_avoid_locs = query_alc_place_api(start_pt)

        # if distance > CHECK_INTERVAL:
        # if distance < CHECK_INTERVAL:

    
    # Initialize the priority queue with the start point
    priority_queue = PriorityQueue()
    priority_queue.push((0, start, 0))  # (total_cost, waypoint, risk_score)
    
    visited = set()
    came_from = {}
    cost_so_far = {start: 0}
    
    while not priority_queue.is_empty():
        current_cost, current_point, current_risk = priority_queue.pop()
        
        if current_point == destination:
            return reconstruct_path(came_from, start, destination)
        
        visited.add(current_point)
        
        for neighbor in get_neighbors(current_point):
            if neighbor in visited:
                continue
            
            # Distance cost to the destination
            distance_cost = distance_between(neighbor, destination)
            
            # Check for alc_loc points only if necessary
            if should_check_for_alc_loc(neighbor, start):
                risk_score = calculate_risk_score(neighbor, alc_loc_radius)
            else:
                risk_score = current_risk
            
            total_cost = distance_cost + (risk_score * RISK_WEIGHT)
            
            if neighbor not in cost_so_far or total_cost < cost_so_far[neighbor]:
                cost_so_far[neighbor] = total_cost
                priority_queue.push((total_cost, neighbor, risk_score))
                came_from[neighbor] = current_point
    
    return None  # Return None if no route is found

def should_check_for_alc_loc(waypoint, start):
    distance_from_start = distance_between(waypoint, start)
    return distance_from_start >= CHECK_THRESHOLD_DISTANCE and (distance_from_last_check(waypoint) >= CHECK_INTERVAL)

def distance_from_last_check(waypoint):
    # Placeholder for calculating distance from the last check
    # You can implement logic to track and update the last checked location
    return CHECK_INTERVAL  # Simplified for demonstration

def calculate_risk_score(waypoint, alc_loc_radius):
    alc_locations = query_alc_place_api(waypoint, alc_loc_radius)
    risk_score = 0
    for alc in alc_locations:
        alc_lat = alc['geometry']['location']['lat']
        alc_lng = alc['geometry']['location']['lng']
        proximity_factor = 1 / max(distance_between(waypoint, (alc_lat, alc_lng)), 1)  # Avoid division by zero
        risk_score += proximity_factor
    return risk_score

def reconstruct_path(came_from, start, destination):
    path = []
    current = destination
    while current != start:
        path.append(current)
        current = came_from[current]
    path.append(start)
    path.reverse()
    return path

def get_neighbors(point):
    # Placeholder for generating neighboring waypoints
    # Replace this with a method to get real geographical neighbors
    return [(point[0] + 0.001, point[1]), (point[0], point[1] + 0.001), (point[0] - 0.001, point[1]), (point[0], point[1] - 0.001)]

# Example usage
start_point = (40.748817, -73.985428)  # Example: New York City
destination_point = (40.785091, -73.968285)  # Example: Central Park
safe_route = find_safe_route(start_point, destination_point, alc_loc_radius=check_radius)
print("Safe Route:", safe_route)
