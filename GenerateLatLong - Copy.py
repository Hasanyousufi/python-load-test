import requests
import json
import polyline

def get_directions(api_key, origin, destination):
    url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{origin};{destination}?steps=true&access_token={api_key}&geometries=geojson"
    try:
        response = requests.get(url)
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error while fetching directions: {e}")
        return None

def interpolate_coordinates(lat1, lon1, lat2, lon2, interval):
    d_lat = lat2 - lat1
    d_lon = lon2 - lon1

    num_points = int(max(abs(d_lat), abs(d_lon)) / interval)
    
    if num_points > 0:
        lat_list = [lat1 + i * d_lat / num_points for i in range(num_points + 1)]
        lon_list = [lon1 + i * d_lon / num_points for i in range(num_points + 1)]

        return list(zip(lat_list, lon_list))
    else:
        return [(lat1, lon1), (lat2, lon2)]

def extract_lat_lon(directions_data, interval=0.000005):
    lat_lon_list = []
    if directions_data and 'routes' in directions_data:
        for route in directions_data['routes']:
            decoded_polyline = polyline.decode(route['geometry'])

            for i in range(len(decoded_polyline) - 1):
                lat1, lon1 = decoded_polyline[i]
                lat2, lon2 = decoded_polyline[i + 1]
                interpolated_coords = interpolate_coordinates(lat1, lon1, lat2, lon2, interval)
                lat_lon_list.extend(interpolated_coords)

    return lat_lon_list

def write_lat_lon_to_file(lat_lon_list, filename):
    with open(filename, 'w') as file:
        for lat, lon in lat_lon_list:
            file.write(f"{lat}, {lon}\n")

def main():
    api_key = "pk.eyJ1IjoiaGFzYW55b3VzdWZpIiwiYSI6ImNsZ29vdnMwbzBybGszZW9lNHgzODZ2aGMifQ._OLec_Ij2NXNuq-1hQo6aw"  # Replace with your Mapbox API access token
    origin = "67.0871514,24.7793893"  # DHA Phase 8 Nueplex, Karachi, Pakistan
    destination = " 73.050052,33.708518"  # North Nazimabad Block H Pie in the Sky, Karachi, Pakistan
    filename = "Karachi_to_islamabad_route.txt"

    directions_data = get_directions(api_key, origin, destination)

    if directions_data:
        if directions_data['code'] == 'Ok':
            lat_lon_list = extract_lat_lon(directions_data)
            write_lat_lon_to_file(lat_lon_list, filename)
        else:
            print(f"Error fetching directions: {directions_data['code']}")

if __name__ == "__main__":
    main()



