# kiini/helpers/location.py 

from geopy.distance import geodesic


def calculate_distance(location1, location2):
    """
    Calculates distance in kilometers between two (lat, lon) tuples.
    """
    if not location1 or not location2:
        return None
    return geodesic(location1, location2).km