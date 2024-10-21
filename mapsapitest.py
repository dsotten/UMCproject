import requests

API_KEY = 'AIzaSyBzoCUm8NNP68qFTVdWHVlX-MfNIjXUwOE'
location = '37.2744,-76.714'  # New York City (example)
radius = 300  # 1.5 km
place_type = 'bar'

radius_url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius={radius}&type={place_type}&key={API_KEY}'

routing_url = f'https://maps.googleapis.com/maps/api/directions/json?origin=37.2744,-76.7143&destination=37.27732,-76.70697&key={API_KEY}'

radius_request = requests.get(radius_url)
bars = []

if radius_request.status_code == 200:
    places = radius_request.json()
    if places['status'] == 'OK':
        bars = places['results']
    else:
        print("Error in response: ", places['status'])
else:
    print("Request failed: ", radius_request.status_code)


if bars:
    print("Bars found:")
    for bar in bars:
        print(bar['name'], "-", bar['vicinity'])


# Print out the results
# for place in data['results']:
#     print(place['name'], '-', place['vicinity'])

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
