"""
OR-Tools VRP solver implementation.
"""
import logging
from typing import List, Dict, Optional, Tuple
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

logger = logging.getLogger(__name__)


def solve_vrp(
    distance_matrix: List[List[int]],
    num_vehicles: int,
    depot_index: int = 0,
    vehicle_capacities: Optional[List[int]] = None,
    demands: Optional[List[int]] = None,
    time_limit_seconds: int = 30
) -> Dict:
    """
    Solve the Vehicle Routing Problem using OR-Tools.
    
    Args:
        distance_matrix: 2D list of distances between locations
        num_vehicles: Number of vehicles available
        depot_index: Index of the depot location (default: 0)
        vehicle_capacities: Optional list of vehicle capacities for CVRP
        demands: Optional list of demands for each location (depot should be 0)
        time_limit_seconds: Time limit for the solver
        
    Returns:
        Dictionary containing:
            - total_distance: Total distance of all routes
            - routes: List of routes, each route is a list of location indices
            - unvisited_nodes: List of location indices that were not visited
    """
    logger.info(f"Solving VRP with {num_vehicles} vehicles and {len(distance_matrix)} locations")
    
    # Create the routing index manager
    manager = pywrapcp.RoutingIndexManager(
        len(distance_matrix),
        num_vehicles,
        depot_index
    )
    
    # Create Routing Model
    routing = pywrapcp.RoutingModel(manager)
    
    # Create and register distance callback
    def distance_callback(from_index: int, to_index: int) -> int:
        """Returns the distance between the two nodes."""
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix[from_node][to_node]
    
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    
    # Define cost of each arc
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    # Add Capacity constraint if provided
    if vehicle_capacities is not None and demands is not None:
        logger.info("Adding capacity constraints")
        
        def demand_callback(from_index: int) -> int:
            """Returns the demand of the node."""
            from_node = manager.IndexToNode(from_index)
            return demands[from_node]
        
        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            vehicle_capacities,  # vehicle maximum capacities
            True,  # start cumul to zero
            'Capacity'
        )
    
    # Setting first solution heuristic
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.seconds = time_limit_seconds
    
    # Solve the problem
    logger.info("Starting OR-Tools solver...")
    solution = routing.SolveWithParameters(search_parameters)
    
    # Extract solution
    if solution:
        return _extract_solution(manager, routing, solution, num_vehicles)
    else:
        logger.error("No solution found")
        return {
            "total_distance": None,
            "routes": [],
            "unvisited_nodes": list(range(len(distance_matrix))),
            "error": "No solution found"
        }


def _extract_solution(
    manager: pywrapcp.RoutingIndexManager,
    routing: pywrapcp.RoutingModel,
    solution: pywrapcp.Assignment,
    num_vehicles: int
) -> Dict:
    """
    Extract the solution from OR-Tools solver.
    
    Args:
        manager: Routing index manager
        routing: Routing model
        solution: Solution assignment
        num_vehicles: Number of vehicles
        
    Returns:
        Dictionary with total_distance, routes, and unvisited_nodes
    """
    total_distance = 0
    routes = []
    visited_nodes = set()
    
    for vehicle_id in range(num_vehicles):
        route = []
        route_distance = 0
        index = routing.Start(vehicle_id)
        
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route.append(node_index)
            visited_nodes.add(node_index)
            
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
        
        # Add the depot at the end
        node_index = manager.IndexToNode(index)
        route.append(node_index)
        visited_nodes.add(node_index)
        
        routes.append(route)
        total_distance += route_distance
        
        logger.info(f"Vehicle {vehicle_id}: Route {route}, Distance: {route_distance}m")
    
    # Find unvisited nodes
    all_nodes = set(range(manager.GetNumberOfNodes()))
    unvisited_nodes = list(all_nodes - visited_nodes)
    
    logger.info(f"Total distance: {total_distance}m")
    if unvisited_nodes:
        logger.warning(f"Unvisited nodes: {unvisited_nodes}")
    
    return {
        "total_distance": total_distance,
        "routes": routes,
        "unvisited_nodes": unvisited_nodes
    }
