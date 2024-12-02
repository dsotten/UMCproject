import re
import math
import json
import datetime
import pandas as pd
# import DJ as DJ
import rerouting as AR

API_KEY = 'AIzaSyBzoCUm8NNP68qFTVdWHVlX-MfNIjXUwOE'

trips = [
    [('40.748817,-73.985428'),('40.785091,-73.968285')],
    [('37.2731,-76.7133'),('37.27732,-76.70697')]
]

def reroute_function_testing(trips=trips):

    ar_dict_list = []
    dj_dict_list = []

    for trip in trips:
        origin = trip[0]
        destination = trip[1]

        ar_info = call_ar(origin,destination,high_risk=False)
        ar_dict_list += [ar_info]

        # dj_info = call_dj(origin,destination,high_risk=False)
        # dj_dict_list += [dj_info]

        # print('Instructions:'+str(ar_info['travel_instructions']))
        # print('Distance:'+str(ar_info['travel_dist'])+' meters')
        # print('Travel Time:'+str(ar_info['travel_time']))
        # print('Num API Calls:'+str(ar_info['api_calls']))
        # print('Runtime:'+str(ar_info['runtime']))

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
    return DJ.handler()

def extract_travel_info(file):
    instructions = ''
    travel_dist = 0
    travel_time = 0

    for step in file['legs'][0]['steps']:
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

def generate_trips(num_of_trips):
    return

if __name__ == "__main__":
    print('Start')
    reroute_function_testing()