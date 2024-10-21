import requests

API_KEY = 'AIzaSyBzoCUm8NNP68qFTVdWHVlX-MfNIjXUwOE'
location = '40.748817,-73.985428'  # New York City (example)
radius = 1500  # 1.5 km
place_type = 'bar'

url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius={radius}&type={place_type}&key={API_KEY}'

response = requests.get(url)
data = response.json()

# print(data)

# Print out the results
for place in data['results']:
    print(place['name'], '-', place['vicinity'])