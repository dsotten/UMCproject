import requests

API_KEY = 'AIzaSyBzoCUm8NNP68qFTVdWHVlX-MfNIjXUwOE'
location = '36.1716,-115.1391'
radius = 300  # 1.5 km
place_types1 = ['bar','liquor_store','casino','night_club']
place_types2 = ['convenience_store','drugstore','gas_station','supermarket']

for avoid_loc in place_types1:
    radius_url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius={radius}&type={avoid_loc}&key={API_KEY}'

    radius_request = requests.get(radius_url)
    to_avoid = []

    if radius_request.status_code == 200:
        places = radius_request.json()
        if places['status'] == 'OK':
            to_avoid = places['results']
        else:
            print("Error in response: ", places['status'])
    else:
        print("Request failed: ", radius_request.status_code)

    if to_avoid:
        print(avoid_loc+"s found:")
        for loc in to_avoid:
            print(loc['name'], "-", loc['vicinity'])