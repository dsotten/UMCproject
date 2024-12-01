import requests
from typing import Final
from queue import PriorityQueue
import math
import json

#Harversine's Formula - Not very precise below 12 meters.
def coord_to_m(lat1, long1, lat2, long2):
    RADIUS_OF_EARTH: Final = 6371000 #in M
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)
    long1 = math.radians(long1)
    long2 = math.radians(long2)
    delt_lat = lat2 - lat1
    delt_long = long2 - long1
    a = (math.sin(delt_lat/2))**2 + math.cos(lat1) * math.cos(lat2) * (math.sin(delt_long/2))**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return c * RADIUS_OF_EARTH #1000 to conver to meters

#Looks through the bar list to see if there is a bar close to the point being looked at
def calc_bar_weight(bar_coords, pot_x, pot_y):
    weight = 0
    for bar in bar_coords:
        if abs(bar[0]-pot_x) < AVERAGE_COORD/7:
            weight += .5
        elif abs(bar[1]-pot_y) < AVERAGE_COORD/7:
            weight += .5
    print('Weight Added:' + str(weight))
    return weight



#Final Variables
API_KEY: Final = 'AIzaSyBzoCUm8NNP68qFTVdWHVlX-MfNIjXUwOE'
AVERAGE_WALK: Final = 85.2 #Per Minute 
WALKING_RADIUS: Final = 300
CORD_TO_METERS: Final = 10.9728 #For 0.0001 degrees
AVERAGE_COORD: Final = 85.2/10.9728*.0001*7
#Weights
BAR_WEIGHT: Final = .5


#Current Example
origin_x = 37.2731
origin_y = -76.7133 #Zable Stadium
destination_x = 37.27732
destination_y = -76.70697 #Jay's Apartment
estimate_min_add = 10

#Don't know if this is needed anymore.
if(destination_x > origin_x):
    bigger_x = destination_x
    smaller_x = origin_x
else:
    bigger_x = origin_x
    smaller_x = destination_x

if(destination_y > origin_y):
    bigger_y = destination_y
    smaller_y = origin_y
else:
    bigger_y= origin_y
    smaller_y = destination_y

#May have to change radius later. Possibly implement it in the if else statements above.
place_type = 'bar'
coord = str(origin_x)+','+str(origin_y)
radius = str(coord_to_m(origin_x,origin_y,destination_x,destination_y))
radius_url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={coord}&radius={radius}&type={place_type}&key={API_KEY}'

#Gets bars in the area surrounding the origin. The radius is how far away the destination is.
bar_coords = []
radius_request = requests.get(radius_url)
if radius_request.status_code == 200:
    places = radius_request.json()
    if places['status'] == 'OK':
        bars = places['results']
        if bars:
            for bar in bars:
                lat = float(bar['geometry']['location']['lat'])
                lng = float(bar['geometry']['location']['lng'])
                bar_coords.append([lat, lng])
    elif places['status'] == 'ZERO_RESULTS':
        print('No Bars') #Probably need to come up with situatiosn for these
    else:
        print("Error in response: ", places['status'])
else:
    print("Request failed: ", radius_request.status_code)


current_node_str = str(origin_x) + ',' + str(origin_y)
current_node = [origin_x, origin_y]

#Keeps track of connections
connection_graph = {current_node_str: ''} #?
#Weight issue
weight_graph = {current_node_str: 0}
#Puts weights into here
pq = PriorityQueue()

check_coords = ''
x_variant = AVERAGE_COORD
y_variant = AVERAGE_COORD

past_current_node = ''

i = 5
while abs(abs(current_node[0]) + abs(current_node[1])) - (abs(destination_x)+ abs(destination_y)) > .0001:
    print(abs(abs(current_node[0]) + abs(current_node[1])) - (abs(destination_x)+ abs(destination_y)) > .0001)
    #Gets the locations and the weights of nodes it wants to look at.
    #Current issue might weight roads multiple times
    weights = []
    check_coords += str(current_node[0]+x_variant) + ',' + str(current_node[1]+y_variant)
    weights.append(calc_bar_weight(bar_coords, current_node[0]+x_variant, current_node[1]+y_variant))
    check_coords += '|'+str(current_node[0]-x_variant)+','+str(current_node[1]+y_variant)
    weights.append(calc_bar_weight(bar_coords, current_node[0]-x_variant, current_node[1]+y_variant))
    check_coords += '|'+str(current_node[0]+x_variant)+','+str(current_node[1]-y_variant)
    weights.append(calc_bar_weight(bar_coords, current_node[0]+x_variant, current_node[1]-y_variant))
    check_coords += '|'+str(current_node[0]-x_variant)+','+str(current_node[1]-y_variant)
    weights.append(calc_bar_weight(bar_coords, current_node[0]-x_variant, current_node[1]-y_variant))
    check_coords += '|'+ str(current_node[0]+x_variant) + ',' + str(current_node[1])
    weights.append(calc_bar_weight(bar_coords, current_node[0]+x_variant, current_node[1]))
    check_coords += '|'+ str(current_node[0]-x_variant) + ',' + str(current_node[1])
    weights.append(calc_bar_weight(bar_coords, current_node[0]-x_variant, current_node[1]))
    check_coords += '|'+ str(current_node[0]) + ',' + str(current_node[1]+y_variant)
    weights.append(calc_bar_weight(bar_coords, current_node[0], current_node[1]+y_variant))
    check_coords += '|'+ str(current_node[0]) + ',' + str(current_node[1]-y_variant)
    weights.append(calc_bar_weight(bar_coords, current_node[0], current_node[1]-y_variant))
    closest_road_url = f'https://roads.googleapis.com/v1/nearestRoads?points={check_coords}&key={API_KEY}'
    
    #Gets the nearest roads from the poaint
    try:
        road_request = requests.get(closest_road_url)
        road_request.raise_for_status()  # Raise an error for HTTP codes 4xx/5xx
        road_request_data = road_request.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

    i = 0
    #Goes through the data
    if "snappedPoints" in road_request_data:
        past = ''
        for snapped_point in road_request_data["snappedPoints"]:
            #Gets string version of the closest road
            latitude = snapped_point["location"]["latitude"]
            longitude = snapped_point["location"]["longitude"]
            lat_long = str(latitude)+ ','+ str(longitude)
            print("Coords:" + lat_long)

            #Checks to see if the road is already in the graph
            if lat_long not in connection_graph:
                #Adds it as a new node to the connection graph and connects it with the node that found it
                connection_graph.update({lat_long: current_node_str})
                #Puts it in the priority queue with its associated weight
                weight = abs(current_node[0] - latitude) + abs(current_node[1] - longitude) + abs(destination_x - latitude) + abs(destination_y - longitude) #Calculates the distance from the road
                print("Weight:" + str(weight))
                pq.put((weight + weights[i], lat_long))
            
            #Might be nice to update the weights here else:
                # weight = abs(current_node[0] - latitude + current_node[1] - longitude) #Calculates the distance from the road
                # pq.update{lat_long: weight_graph.get(lat_long) + weights[i]}
        
            if lat_long != past:
                i += 1
            past = lat_long
        past_current_node = current_node_str
        new_current_node = pq.get()
        current_node_str = new_current_node[1]
        print(current_node_str)
        ll = current_node_str.split(',')
        current_node = [float(ll[0]),float(ll[1])]
        check_coords = ''
        if i == 5:
            break
        else:
            i += 1

#Fix to ensure the number of way points does not exceed
past_current_node = connection_graph.get(past_current_node,'')
waypoints = past_current_node
past_current_node = connection_graph.get(past_current_node,'')
while past_current_node != '':
    waypoints += '|' + past_current_node
    past_current_node = connection_graph.get(past_current_node,'')
    past_current_node = connection_graph.get(past_current_node,'')

routing_url = f'https://maps.googleapis.com/maps/api/directions/json?origin={str(origin_x)},{str(origin_y)}&destination={str(destination_x)},{str(destination_y)}&waypoints={waypoints}&key={API_KEY}'
           
route_request = requests.get(routing_url)
route_json = route_request.json()

if route_json['status'] == 'OK':
    # Get the first route
    route = route_json['routes'][0]
    
    # Print out the total distance and duration
    leg = route['legs'][0]
    print(f"Total Distance: {leg['distance']['text']}")
    print(f"Total Duration: {leg['duration']['text']}")
    print("\nDirections:")
    
    # Print each step of the route
    for step in leg['steps']:
        instruction = step['html_instructions']  # Contains HTML instructions
        distance = step['distance']['text']  # Step distance
        duration = step['duration']['text']  # Step duration

        # Strip HTML tags from the instruction (if needed)
        import re
        clean_instruction = re.sub('<.*?>', '', instruction)  # Remove HTML tags

        # Print step details
        print(f"- {clean_instruction} ({distance}, {duration})")
else:
    print(f"Error: {route_json['status']}")
    
#Perform necessary function to get the way points and give the path.
           
           
           
           
         

         
          
            #Print testing line
            #print(latitude, longitude)

# Need to figure this out - weights - Probably look into that
# liquor_store, casino, night_club
# convenience_store, drugstore, gas_station, supermarket
# for i in road_coordinates_list:
#     cord = str(i[0]) + ',' + str(i[1])
#     radius = AVERAGE_COORD*300000 #Perhaps a distance to look into?
    

  
# for each vertex v in Graph.Vertices:
#     dist[v] ← INFINITY
#     prev[v] ← UNDEFINED
#     add v to Q
#     dist[source] ← 0

#     while Q is not empty:
#     u ← vertex in Q with min dist[u]
#         remove u from Q

#     for each neighbor v of u still in Q:
#         alt ← dist[u] + Graph.Edges(u, v)
#         if alt < dist[v]:
#             dist[v] ← alt
#             prev[v] ← u

#     return dist[], prev[]

# Only call Places API call once, weight from how far away it is from the bar. 
