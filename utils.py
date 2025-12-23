"""
Utility functions for distance calculations in VRP.
"""
import logging
from typing import List, Dict
from geopy.distance import great_circle

logger = logging.getLogger(__name__)


def calculate_distance_matrix(locations: List[Dict[str, float]]) -> List[List[int]]:
    """
    Calculate the Great Circle distance matrix between all locations.
    
    Args:
        locations: List of dictionaries with 'lat' and 'lng' keys
        
    Returns:
        Distance matrix as a 2D list where distances are in meters (as integers)
    """
    num_locations = len(locations)
    distance_matrix = [[0] * num_locations for _ in range(num_locations)]
    
    for i in range(num_locations):
        for j in range(num_locations):
            if i == j:
                distance_matrix[i][j] = 0
            else:
                # Calculate great circle distance
                coord_i = (locations[i]['lat'], locations[i]['lng'])
                coord_j = (locations[j]['lat'], locations[j]['lng'])
                
                # Distance in meters, converted to integer
                distance = great_circle(coord_i, coord_j).meters
                distance_matrix[i][j] = int(distance)
    
    logger.info(f"Calculated distance matrix for {num_locations} locations")
    return distance_matrix
