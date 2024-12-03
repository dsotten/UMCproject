import re
import math
import random
import json
import datetime
import pandas as pd
# import DJ as DJ
import rerouting as AR

API_KEY = 'AIzaSyBzoCUm8NNP68qFTVdWHVlX-MfNIjXUwOE'

# trips = [
#     [('40.748817,-73.985428'),('40.785091,-73.968285')],
#     [('37.2731,-76.7133'),('37.27732,-76.70697')]
# ]

def reroute_function_testing(trips):

    ar_dict_list = []
    dj_dict_list = []

    for trip in trips:
        origin, destination = trip
        origin_str = ','.join(str(val) for val in origin)
        destination_str = ','.join(str(val) for val in destination)

        ar_info = call_ar(origin_str,destination_str,high_risk=False)
        ar_dict_list += [ar_info]

        # dj_info = call_dj(origin,destination,high_risk=False)
        # dj_dict_list += [dj_info]

        print('Instructions:'+str(ar_info['travel_instructions']))
        print('Distance:'+str(ar_info['travel_dist'])+' meters')
        print('Travel Time:'+str(ar_info['travel_time']))
        print('Num API Calls:'+str(ar_info['api_calls']))
        print('Runtime:'+str(ar_info['runtime'])+"\n")

    ar_df = pd.DataFrame(ar_dict_list)
    ar_df.to_csv('ar_test.csv')

    #repeat all tests for high_risk = True


#Calls Alternative Routes and returns
def call_ar(origin,destination,high_risk=False):

    start_time = datetime.datetime.now()
    alt_route = AR.handler(origin,destination,API_KEY,high_risk=high_risk)
    end_time = datetime.datetime.now()
    time_elapsed = end_time - start_time
    time_elapsed = time_elapsed.total_seconds()

    alt_route_json = alt_route['route_json']    
    travel_info = extract_travel_info(alt_route_json)

    ret_dict = {
        'origin':origin,
        'destination':destination,
        'route_json': alt_route_json,
        'travel_instructions': travel_info['instructions'],
        'travel_dist': travel_info['dist'],
        'travel_time': travel_info['time'],
        'danger_locs':alt_route['danger_locs'],
        'api_calls':alt_route['num_api_calls'],
        'runtime': time_elapsed,
    }

    return ret_dict

def call_dj(origin,destination,high_risk=False):
    
    start_time = datetime.datetime.now()
    dj_route = DJ.handler(origin,destination,API_KEY,high_risk=high_risk)
    end_time = datetime.datetime.now()
    time_elapsed = end_time - start_time

def extract_travel_info(file):
    instructions = ''
    travel_dist = 0
    travel_time = 0

    if file != 'ERROR':
        for leg in file['legs']:
            for step in leg['steps']:
                instruction = step['html_instructions']  # Contains HTML instructions
                distance = step['distance']['text']  # Step distance
                duration = step['duration']['text']  # Step duration

                # Strip HTML tags from the instruction (if needed)
                clean_instruction = re.sub('<.*?>', '', instruction)  # Remove HTML tags
                instructions += f"- {clean_instruction} ({distance}, {duration}) \n"

                #Add distance and duration
                travel_dist += step['distance']['value']
                travel_time += step['duration']['value']
    
    return {
        'instructions':instructions,
        'dist':travel_dist,
        'time':travel_time
    }

def generate_trips(num_of_trips, radius_km, min_distance_km=1, max_distance_km=5):
    
    def random_point_in_radius(center_lat, center_lon, radius_km):
        """
        Generate a random point within a given radius around a center point.
        """
        R = 6371  # Earth's radius in km
        radius_rad = radius_km / R

        # Generate a random angle and distance
        distance_rad = random.uniform(0, radius_rad)
        angle = random.uniform(0, 2 * math.pi)

        # Calculate latitude and longitude offsets
        lat1 = math.radians(center_lat)
        lon1 = math.radians(center_lon)

        lat2 = math.asin(math.sin(lat1) * math.cos(distance_rad) +
                         math.cos(lat1) * math.sin(distance_rad) * math.cos(angle))
        lon2 = lon1 + math.atan2(math.sin(angle) * math.sin(distance_rad) * math.cos(lat1),
                                 math.cos(distance_rad) - math.sin(lat1) * math.sin(lat2))

        return math.degrees(lat2), math.degrees(lon2)

    def destination_point(lat, lon, distance_km, bearing):
        """
        Calculate the destination point given a start point, distance, and bearing.
        """
        R = 6371  # Earth's radius in km
        distance_rad = distance_km / R
        bearing_rad = math.radians(bearing)

        lat1 = math.radians(lat)
        lon1 = math.radians(lon)

        lat2 = math.asin(math.sin(lat1) * math.cos(distance_rad) +
                         math.cos(lat1) * math.sin(distance_rad) * math.cos(bearing_rad))
        lon2 = lon1 + math.atan2(math.sin(bearing_rad) * math.sin(distance_rad) * math.cos(lat1),
                                 math.cos(distance_rad) - math.sin(lat1) * math.sin(lat2))

        return math.degrees(lat2), math.degrees(lon2)

    cities = [
        (35.6764, 139.6500), #Tokyo
        (28.7041, 77.1025), #Delhi
        (31.2304, 121.4737), #Shanghai
        (23.5558, 46.6396), #Sao Paulo
        (19.4326, 99.1332), #Mexico City
        (30.0444, 31.2357), #Cairo
        (40.7128, 74.0060), #New York City
        (34.6037, 58.3816), #Buenos Aires
        (41.0082, 28.9784), #Istanbul
        (14.5995, 120.9842) #Manila
    ]

    num_of_trips //= len(cities)
    trip_pairs = []

    for city in cities:
        city_lat, city_lon = city

        for _ in range(num_of_trips):
            # Generate the starting point within the city radius
            start = random_point_in_radius(city_lat, city_lon, radius_km)

            # Generate a random distance and bearing for the destination
            distance_km = random.uniform(min_distance_km, max_distance_km)
            bearing = random.uniform(0, 360)  # Random direction
            end = destination_point(start[0], start[1], distance_km, bearing)

            trip_pairs.append((start, end))

    return trip_pairs

if __name__ == "__main__":
    print('Start')
    new_trips = generate_trips(10, 50)
    print(str(new_trips))
    reroute_function_testing(new_trips)