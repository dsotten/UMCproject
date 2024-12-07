import requests
from typing import Final
from queue import PriorityQueue
import math
import json

#This file holds our last implementation and most expensive implementation. We use dynamic grid size and routing.

#Harversine's Formula - This formula is used to convert coordinates into meters. - Not as precise below 12 meters, but still relatively accurate.
def coord_to_m(long1, lat1, long2, lat2):
    RADIUS_OF_EARTH: Final = 6371000 #in M
    long1 = math.radians(long1)
    long2 = math.radians(long2)
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)
    delt_lat = lat2 - lat1
    delt_long = long2 - long1
    a = (math.sin(delt_lat/2))**2 + math.cos(lat1) * math.cos(lat2) * (math.sin(delt_long/2))**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return c * RADIUS_OF_EARTH #1000 to conver to meters

#Looks through the list to see if there is an avoided establishment close to the point being looked at and adds a weighted constant. - Uses this to only have to make one API call.
def calc_weight(coords, long, lat, grid_size):
    WEIGHT_CONSTANT: Final = 10 #Constant currently but plan to update for future updates.
    weight_addition = 0 #initially
    for place in coords:
        distance_x = abs(place[0]-long) #Should return a negative or positive value.
        distance_y = abs(place[1]-lat)
        if distance_x < grid_size*2 or  distance_y < grid_size:
            weight_addition += coord_to_m(lat, long, place[0], place[1]) * WEIGHT_CONSTANT
    return weight_addition

#The main program that gets the alcohol avoidance route.
#Input(s):
#avoid_place - The list of the type of establishments your route is to avoid.
def get_route(origin_long, origin_lat, dest_long, dest_lat, avoid_place, API_KEY, max_api_calls=50, opennow=True):
    # API_KEY: Final = 'AIzaSyDUWGT6bmVDHC3vST7oSW9eK2vhzvWlI8M' 

    #Defines the distance away it will look from a point.
    grid_size = .0001 #Dynamic grid size por favor


    radius_int = coord_to_m(origin_long,origin_lat,dest_long, dest_lat) #Have to have the meters away to give to the api
    #A 2D array that in the first dimension will hold the type of places to avoid and in the second dimension holds the lists of coordinates where they establishment is in the radius.
    avoid_place_lst = []
    
    #Gets coordinates of establishments for each place type.
    for place_type in avoid_place:
        #Everything needs to be in String format to implement in the URL
        coord = str(origin_long)+','+str(origin_lat)
        radius = str(radius_int)
        
        #Only includes establishments that are open based on the time, else includes all establishments in the area.
        if opennow:
            radius_url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={coord}&radius={radius}&type={place_type}&opennow&key={API_KEY}'
        else:
            radius_url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={coord}&radius={radius}&type={place_type}&key={API_KEY}'

        #Makes the radius request. Gets bars in the area surrounding the origin and puts them into the bar_coords list.
        #If an error occurs when making the bar request, it is printed in the console.
        coords = []
        radius_request = requests.get(radius_url)
        if radius_request.status_code == 200:
            places = radius_request.json()
            if places['status'] == 'OK':
                bars = places['results']
                if bars:
                    for bar in bars:
                        lng = float(bar['geometry']['location']['lng'])
                        lat = float(bar['geometry']['location']['lat'])
                        coords.append((lng, lat))
            elif places['status'] == 'ZERO_RESULTS':
                print('No '+str(place_type)+'s') # I think your implementation has some extra stuff.
            else:
                print("Error in response: ", places['status'])
        else:
            print("Request failed: ", radius_request.status_code)
        if len(coords) > 0:
            avoid_place_lst.append(coords)

    #Current node - Starts at the origin
    current_node_str = str(origin_long) + ',' + str(origin_lat)
    current_node = (origin_long, origin_lat)

    #Keeps track of connections - main purpose is to not rereview places and to back track once the algorithm is over. Holds the current_lat_and_long and the coordinates prior to get there.
    connection_graph = {current_node_str: ''} 
    #Keep tracks of weight - main purpose is to add on the weight of previous nodes. - Weight is in meters
    weight_graph = {current_node_str: 0}
    #Puts (weights, node_name) into here to make decisions on what node to traverse to next.
    pq = PriorityQueue()

    check_coords = ''
    #Will use these when creating the route
    waypoints = ''

    api_check = 0

    if len(avoid_place_lst) > 0:
        #Makes sure the longitude and latitude are not within a gride size and checks to make sure the api is not called more than 50 times.
        while abs(current_node[0] -  dest_long) > grid_size and abs(current_node[1] - dest_lat) > grid_size and api_check <= max_api_calls:
            #Gets the locations and the weights of nodes it wants to look at surrounding the current node. Format:
            # ***
            # *X*
            # ***
            # * - The places checked.
            # X - The current cordinate.
            check_coords += str(current_node[0]+grid_size) + ',' + str(current_node[1]+grid_size)
            check_coords += '|'+str(current_node[0]-grid_size)+','+str(current_node[1]+grid_size)
            check_coords += '|'+str(current_node[0]+grid_size)+','+str(current_node[1]-grid_size)
            check_coords += '|'+str(current_node[0]-grid_size)+','+str(current_node[1]-grid_size)
            check_coords += '|'+ str(current_node[0]+grid_size) + ',' + str(current_node[1])
            check_coords += '|'+ str(current_node[0]-grid_size) + ',' + str(current_node[1])
            check_coords += '|'+ str(current_node[0]) + ',' + str(current_node[1]+grid_size)
            check_coords += '|'+ str(current_node[0]) + ',' + str(current_node[1]-grid_size)

            #Put into the proper URL and trys to get the roads. If an error occurs, it is printed in the console.
            closest_road_url = f'https://roads.googleapis.com/v1/nearestRoads?points={check_coords}&key={API_KEY}'
            try:
                road_request = requests.get(closest_road_url)
                road_request.raise_for_status()  # Raise an error for HTTP codes 4xx/5xx
                road_request_data = road_request.json()
            except requests.exceptions.RequestException as e:
                print(f"Error: {e}")
            
            #Adds the new data to the connection_graph, weight_graph, and pq.
            if "snappedPoints" in road_request_data:
                for snapped_point in road_request_data["snappedPoints"]:
                    longitude = snapped_point["location"]["longitude"] 
                    latitude = snapped_point["location"]["latitude"]
                    long_lat = str(latitude)+ ','+ str(longitude) #I don't know why the json is flipping them

                    #Checks to see if the road is already in the graph
                    if long_lat not in connection_graph:
                        #Adds it as a new node to the connection graph and connects it with the node that found it.
                        connection_graph.update({long_lat: current_node_str})
                        #Gets the weight to the road destination
                        
                        routing_url = f'https://maps.googleapis.com/maps/api/directions/json?origin={long_lat}&destination={str(dest_long)},{str(dest_lat)}&units=metric&key={API_KEY}'

                        route_request = requests.get(routing_url)
                        route_json = route_request.json()

                        if route_json['status'] == 'OK':
                            # Get the first route
                            route = route_json['routes'][0]
                            leg = route['legs'][0]
                            dest_weight = float(leg['distance']['value'])
                        else:
                            dest_weight = 100

                        #Necessary to look for the wide variety of places.
                        place_weight = 0
                        for place in avoid_place_lst:
                            place_weight += calc_weight(place, latitude, longitude, grid_size)
                        weight_graph.update({long_lat: (place_weight + (weight_graph.get(current_node_str)))})
                        pq.put((weight_graph.get(long_lat), long_lat))
                
            #Prints if this error occurs
            if pq.empty():
                print("Priority queue is empty; terminating.")
                break
            new_current_node = pq.get()
            current_node_str = new_current_node[1]
            ll = current_node_str.split(',')
            current_node = (float(ll[0]),float(ll[1]))
            check_coords = ''
            api_check += 1

        past_current_node = min(weight_graph) #Gets the min in case the API calls terminated the search, leaving it incomplete.
        waypoints = past_current_node
        #Adds the way points to a string so the URL can use it.
        while past_current_node != '':
            waypoints += '|' + past_current_node
            past_current_node = connection_graph.get(past_current_node,'')
            past_current_node = connection_graph.get(past_current_node,'')

    #Gets the route based off of the way points (if available)
    if waypoints != '':
        routing_url = f'https://maps.googleapis.com/maps/api/directions/json?origin={str(origin_long)},{str(origin_lat)}&destination={str(dest_long)},{str(dest_lat)}&waypoints={waypoints}&units=metric&key={API_KEY}'
    else:
        routing_url = f'https://maps.googleapis.com/maps/api/directions/json?origin={str(origin_long)},{str(origin_lat)}&destination={str(dest_long)},{str(dest_lat)}&units=metric&key={API_KEY}'

    route_request = requests.get(routing_url)
    route_json = route_request.json()

    #Returns route and API calls made for searching
    if route_json['status'] == 'OK':
        # Get the first route
        route = route_json['routes'][0]

        return {
            'route_json': route,
            'num_api_calls': api_check*8
        }
    else:
        print(f"Error: {route_json['status']}")
        return {
            'route_json': None,
            'num_api_calls': api_check
        }

def handler(origin, destination, key, max_api_calls = 50, high_risk=False, opennow=False):
    ox, oy = origin
    dx, dy = destination

    danger_locations = ['bar','liquor_store','casino','night_club']
    place_types2 = ['convenience_store','drugstore','gas_station','supermarket']
    if (high_risk): danger_locations += place_types2

    route_call = get_route(ox, oy, dx, dy, danger_locations, max_api_calls=max_api_calls, API_KEY=key, opennow=opennow)

    return route_call



#Some example test code
if __name__ == '__main__':
    origin_long = 37.2686
    origin_lat = -76.7133333 #Not Zable Stadium
    dest_long = 37.27732
    dest_lat = -76.70697 #Apartment Complex
    avoid_place = ['bar']

    get_route(origin_long, origin_lat, dest_long, dest_lat, avoid_place)