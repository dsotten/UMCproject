import requests
from typing import Final
from queue import PriorityQueue
import math
import json
import heapq

#Harversine's Formula - This formula is used to convert coordinates into meters. - Not as precise below 12 meters, but still relatively accurate.
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

#Looks through the bar list to see if there is a bar close to the point being looked at and adds a weight of .5. (The .5 is subject to change.)
def calc_bar_weight(bar_coords, pot_x, pot_y, grid_size):
    BAR_WEIGHT: Final = 15 #Has to be high for shorter distances, but might not need to be shorter for smaller distances.
    weight = 0
    for bar in bar_coords:
        distance_x = abs(bar[0]-pot_x)
        distance_y = abs(bar[1]-pot_y)
        if distance_x < grid_size*5: #Need to change the weight calculation.
            weight += distance_x * BAR_WEIGHT
        elif distance_y < grid_size:
            weight += BAR_WEIGHT
    # print('Weight Added:' + str(weight))
    return weight

#For now we are only going to use bars. - Just makes things easier
#Might have issues with bigger distances.
def get_route(origin_x, origin_y, dest_x, dest_y, avoid_place,opennow=True):
    API_KEY: Final = 'AIzaSyBzoCUm8NNP68qFTVdWHVlX-MfNIjXUwOE'

    origin_x = origin_x
    origin_y = origin_y
    destination_x = dest_x
    destination_y = dest_y

    #Defines what is the bigger x and y.
    if(destination_x > origin_x):
        bigger_x = destination_x
    else:
        bigger_x = origin_x

    if(destination_y > origin_y):
        bigger_y = destination_y
    else:
        bigger_y= origin_y

    avoid_place_lst = []
    #Formulates the url that looks for bars in the areas. Added open now.
    for place_type in avoid_place:
        coord = str(origin_x)+','+str(origin_y)
        radius_int = coord_to_m(origin_x,origin_y,destination_x,destination_y)
        radius = str(radius_int)
        #Set to 25 miles or 40233.6 meters
        # print("Radius:", radius)
        if radius_int < 40233.6:
            grid_size = .00055 #May need to be changed
        else:
            if(bigger_x>bigger_y):
                grid_size = bigger_x/20
            else:
                grid_size = bigger_y/20
        
        if opennow:
            radius_url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={coord}&radius={radius}&type={place_type}&opennow&key={API_KEY}'
        else:
            radius_url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={coord}&radius={radius}&type={place_type}&key={API_KEY}'

        #Makes the radius request. Gets bars in the area surrounding the origin and puts them into the bar_coords list. The radius is how far away the url looks away from the destination is.
        coords = []
        radius_request = requests.get(radius_url)
        if radius_request.status_code == 200:
            places = radius_request.json()
            if places['status'] == 'OK':
                bars = places['results']
                if bars:
                    for bar in bars:
                        lat = float(bar['geometry']['location']['lat'])
                        lng = float(bar['geometry']['location']['lng'])
                        coords.append([lat, lng])
            elif places['status'] == 'ZERO_RESULTS':
                print('No '+str(place_type)+'s') #Probably need to come up with situatiosn for these
            else:
                print("Error in response: ", places['status'])
        else:
            print("Request failed: ", radius_request.status_code)
        if len(coords) > 0:
            avoid_place_lst.append(coords)

    #Current node
    current_node_str = str(origin_x) + ',' + str(origin_y)
    current_node = [origin_x, origin_y]

    #Keeps track of connections - to not rereview places
    connection_graph = {current_node_str: ''} #?
    #Keep tracks of weight - to add on the amount it currently takes to get there
    weight_graph = {current_node_str: 0}
    #Puts weights into here
    pq = PriorityQueue()

    check_coords = ''

    x_variant = grid_size
    y_variant = grid_size

    #I think there is an issue here
    i = 0
    waypoints = ''
    if len(avoid_place_lst) > 0:
        print("Num places to avoid: "+str(len(avoid_place_lst)))
        while abs((abs(current_node[0])+ abs(current_node[1])) - (abs(destination_x)+ abs(destination_y))) > grid_size and i <= 50:
            #Test line
            print(abs(abs((current_node[0]) + abs(current_node[1])) - (abs(destination_x)+ abs(destination_y))))
            #Gets the locations and the weights of nodes it wants to look at surrounding the current node.
            check_coords += str(current_node[0]+x_variant) + ',' + str(current_node[1]+y_variant)
            check_coords += '|'+str(current_node[0]-x_variant)+','+str(current_node[1]+y_variant)
            check_coords += '|'+str(current_node[0]+x_variant)+','+str(current_node[1]-y_variant)
            check_coords += '|'+str(current_node[0]-x_variant)+','+str(current_node[1]-y_variant)
            check_coords += '|'+ str(current_node[0]+x_variant) + ',' + str(current_node[1])
            check_coords += '|'+ str(current_node[0]-x_variant) + ',' + str(current_node[1])
            check_coords += '|'+ str(current_node[0]) + ',' + str(current_node[1]+y_variant)
            check_coords += '|'+ str(current_node[0]) + ',' + str(current_node[1]-y_variant)

            #Gets the nearest roads from the points defined above.
            closest_road_url = f'https://roads.googleapis.com/v1/nearestRoads?points={check_coords}&key={API_KEY}'
            i += 1
            try:
                road_request = requests.get(closest_road_url)
                road_request.raise_for_status()  # Raise an error for HTTP codes 4xx/5xx
                road_request_data = road_request.json()
                with open("sample.json", "w") as outfile:
                    json.dump(road_request_data, outfile)
            except requests.exceptions.RequestException as e:
                print(f"Error: {e}")

            #Potential issue - For 2 way roads, they are listed twice. Need to formulate some way to not double them, but also not skipping over roads that have the same nearest road.
            #Goes through the data
            if "snappedPoints" in road_request_data:

                for snapped_point in road_request_data["snappedPoints"]:
                    #Gets string version of the closest road
                    latitude = snapped_point["location"]["latitude"]
                    longitude = snapped_point["location"]["longitude"]
                    lat_long = str(latitude)+ ','+ str(longitude)
                    #Test Line
                    # print("Coords:" + lat_long)
                    
                    #Checks to see if the road is already in the graph
                    if lat_long not in connection_graph:
                        #Adds it as a new node to the connection graph and connects it with the node that found it. Should not add to the pq again.
                        connection_graph.update({lat_long: current_node_str})
                        weight = abs(destination_x - latitude) + abs(destination_y - longitude) #Calculates the distance from the road
                        place_weight = 0
                        for place in avoid_place_lst:
                            place_weight += calc_bar_weight(place, latitude, longitude, grid_size)
                        weight_graph.update({lat_long: (weight + place_weight + (weight_graph.get(current_node_str)))})
                        #Test Line
                        # print("Weight:" + str(weight))
                        #Puts it in the priority queue with its associated weight
                        pq.put((weight_graph.get(lat_long), lat_long))
                
            #Gets the next current_node.
            new_current_node = pq.get()
            # print(new_current_node)
            current_node_str = new_current_node[1]
            ll = current_node_str.split(',')
            current_node = [float(ll[0]),float(ll[1])]
            # print("ans:" + str(abs(abs((current_node[0]) + abs(current_node[1])) - (abs(destination_x)+ abs(destination_y)))))
            # print("Current_Node:", current_node_str)
            #Divides the string of the next node into 2.
            check_coords = ''
            # i += 1

        past_current_node = min(weight_graph)
        waypoints = past_current_node
        j = 0
        while past_current_node != '' and j < 50:
            waypoints += '|' + past_current_node
            past_current_node = connection_graph.get(past_current_node,'')
            past_current_node = connection_graph.get(past_current_node,'')
            j+= 1

    print('While loop finished')

    #Open now
    #Gets the route based off of the way points.
    if waypoints != '':
        routing_url = f'https://maps.googleapis.com/maps/api/directions/json?origin={str(origin_x)},{str(origin_y)}&destination={str(destination_x)},{str(destination_y)}&waypoints={waypoints}&units=metric&key={API_KEY}'
    else:
        routing_url = f'https://maps.googleapis.com/maps/api/directions/json?origin={str(origin_x)},{str(origin_y)}&destination={str(destination_x)},{str(destination_y)}&units=metric&key={API_KEY}'
    i += 1

    route_request = requests.get(routing_url)
    route_json = route_request.json()

    #Look at why it is not printing the final destination
    if route_json['status'] == 'OK':
        # Get the first route
        route = route_json['routes'][0]

        return {
            'route_json': route,
            'num_api_calls': i
        }
        # print("\nDirections:")
        # # Print out the total distance and duration
        # for leg in route['legs']:
        #     print(f"Total Distance: {leg['distance']['text']}")
        #     print(f"Total Duration: {leg['duration']['text']}")
        
        #     # Print each step of the route
        #     for step in leg['steps']:
        #         instruction = step['html_instructions']  # Contains HTML instructions
        #         distance = step['distance']['text']  # Step distance
        #         duration = step['duration']['text']  # Step duration

        #         # Strip HTML tags from the instruction (if needed)
        #         import re
        #         clean_instruction = re.sub('<.*?>', '', instruction)  # Remove HTML tags

        #         # Print step details
        #         print(f"- {clean_instruction} ({distance}, {duration})")
        #     print("New leg")
    else:
        print(f"Error: {route_json['status']}")
        return {
            'route_json': None,
            'num_api_calls': i
        }
        
if __name__ == '__main__':
    #DownTown Art Museum - 37.2686°N 76.7048°W
    #Zable Stadium - 37.2730556 ″N -76.7133333″W
    #Current Example - Zable Stadium to Jay's Apartment
    origin_x = 37.2686
    origin_y = -76.7133333 #Zable Stadium
    destination_x = 37.27732
    destination_y = -76.70697 #Jay's Apartment
    avoid_place = ['bar']

    get_route(origin_x, origin_y, destination_x, destination_y, avoid_place)