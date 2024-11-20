import requests
from typing import Final

class Node:
    def __init__(self, long, lat, connected):
        self.long = long
        self.lat = lat
        self.connected = connected

#Final Variables
API_KEY: Final = 'AIzaSyBzoCUm8NNP68qFTVdWHVlX-MfNIjXUwOE'
AVERAGE_WALK: Final = 85.2 #Per Minute 
WALKING_RADIUS: Final = 300
CORD_TO_METERS: Final = 10.9728 #For 0.0001 degrees
AVERAGE_COORD: Final = 85.2/10.9728*.0001
#Weights
BAR_WEIGHT: Final = 2


#Current Example
origin_x = 37.2731
origin_y = -76.7133 #Zable Stadium
destination_x = 37.27732
destination_y = -76.70697 #Jay's Apartment
estimate_min_add = 10

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


#Current Check:
#* *
# X
#* *
#Want:
#***
#*X*
#***
#Gets nearest roads in a grid like way.
check_coords = str(smaller_x) + ',' + str(smaller_y)
x_variant = 0
y_variant = 0
while smaller_x + x_variant < bigger_x:
    x_variant += AVERAGE_COORD*3
    y_variant = 0
    while smaller_y + y_variant < bigger_y:
        y_variant += AVERAGE_COORD*3
        check_coords += '|'+ str(smaller_x+x_variant) + ',' + str(smaller_y+y_variant)
        check_coords += '|'+str(smaller_x-x_variant)+','+str(smaller_y+y_variant)
        check_coords += '|'+str(smaller_x+x_variant)+','+str(smaller_y-y_variant)
        check_coords += '|'+str(smaller_x-x_variant)+','+str(smaller_y-y_variant)
closest_road_url = f'https://roads.googleapis.com/v1/nearestRoads?points={check_coords}&key={API_KEY}'


try:
    road_request = requests.get(closest_road_url)
    road_request.raise_for_status()  # Raise an error for HTTP codes 4xx/5xx
    road_request_data = road_request.json()
except requests.exceptions.RequestException as e:
    print(f"Error: {e}")

road_coordinates_list = []

if "snappedPoints" in road_request_data:
    for snapped_point in road_request_data["snappedPoints"]:
        latitude = snapped_point["location"]["latitude"]
        longitude = snapped_point["location"]["longitude"]
        if road_coordinates_list.__contains__([latitude, longitude]) == False:
            road_coordinates_list.append([latitude, longitude, ((abs(latitude-bigger_x))+abs(longitude-bigger_y))*100])
            print(((abs(latitude-bigger_x))+abs(longitude-bigger_y))*100)
            #Print testing line
            #print(latitude, longitude)

# Need to figure this out - weights - Probably look into that
place_type = 'bar'
# liquor_store, casino, night_club
# convenience_store, drugstore, gas_station, supermarket
# for i in road_coordinates_list:
#     cord = str(i[0]) + ',' + str(i[1])
#     radius = AVERAGE_COORD*300000 #Perhaps a distance to look into?
#     radius_url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={cord}&radius={radius}&type={place_type}&key={API_KEY}'
#     radius_request = requests.get(radius_url)
#     if radius_request.status_code == 200:
#         places = radius_request.json()
#         if places['status'] == 'OK':
#             bars = places['results']
#             i[2] += len(bars)
#             #Print testing lines
#             print(i[2])
# #            if bars:
# #                print("Bars found:")
# #                for bar in bars:
# #                    print(bar['name'], "-", bar['vicinity'])
#         elif places['status'] == 'ZERO_RESULTS':
#             i[2] += 0
#             print(i[2])
#         else:
#             print("Error in response: ", places['status'])
#     else:
#         print("Request failed: ", radius_request.status_code)
    

  
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
