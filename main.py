"""
FastAPI application for Vehicle Routing Problem optimization.
"""
import logging
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator

from utils import calculate_distance_matrix
from solver import solve_vrp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Vehicle Routing Problem Optimizer",
    description="Solve VRP using Google OR-Tools with FastAPI",
    version="1.0.0"
)


class Location(BaseModel):
    """Location model with ID and coordinates."""
    id: str = Field(..., description="Unique identifier for the location")
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lng: float = Field(..., ge=-180, le=180, description="Longitude")


class VRPRequest(BaseModel):
    """Request model for VRP optimization."""
    locations: List[Location] = Field(..., min_items=2, description="List of locations (first is depot)")
    num_vehicles: int = Field(..., gt=0, description="Number of vehicles available")
    vehicle_capacities: Optional[List[int]] = Field(None, description="Optional vehicle capacities for CVRP")
    demands: Optional[List[int]] = Field(None, description="Optional demands for each location (depot should be 0)")
    time_limit_seconds: int = Field(30, gt=0, le=300, description="Time limit for solver in seconds")
    
    @validator('vehicle_capacities')
    def validate_capacities(cls, v, values):
        """Validate that capacities match number of vehicles."""
        if v is not None and 'num_vehicles' in values:
            if len(v) != values['num_vehicles']:
                raise ValueError(f"Number of capacities must match num_vehicles ({values['num_vehicles']})")
        return v
    
    @validator('demands')
    def validate_demands(cls, v, values):
        """Validate that demands match number of locations."""
        if v is not None and 'locations' in values:
            if len(v) != len(values['locations']):
                raise ValueError(f"Number of demands must match number of locations ({len(values['locations'])})")
            if v[0] != 0:
                raise ValueError("Depot (first location) demand must be 0")
        return v


class Route(BaseModel):
    """Route model for a single vehicle."""
    vehicle_id: int = Field(..., description="Vehicle identifier")
    location_ids: List[str] = Field(..., description="Ordered list of location IDs in the route")
    distance: int = Field(..., description="Total distance of the route in meters")


class VRPResponse(BaseModel):
    """Response model for VRP optimization."""
    total_distance: int = Field(..., description="Total distance of all routes in meters")
    routes: List[Route] = Field(..., description="Individual routes per vehicle")
    unvisited_nodes: List[str] = Field(..., description="Location IDs that were not visited")
    success: bool = Field(..., description="Whether a solution was found")
    message: Optional[str] = Field(None, description="Additional information or error message")


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint with API information."""
    return {
        "name": "Vehicle Routing Problem Optimizer",
        "version": "1.0.0",
        "description": "Solve VRP using Google OR-Tools",
        "endpoint": "POST /optimize"
    }


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/optimize", response_model=VRPResponse)
async def optimize_routes(request: VRPRequest) -> VRPResponse:
    """
    Optimize vehicle routes using OR-Tools VRP solver.
    
    Args:
        request: VRP request with locations, vehicles, and optional constraints
        
    Returns:
        VRP solution with routes and total distance
        
    Raises:
        HTTPException: If there's an error in processing or solving
    """
    try:
        logger.info(f"Received optimization request for {len(request.locations)} locations and {request.num_vehicles} vehicles")
        
        # Extract location data
        location_data = [
            {"lat": loc.lat, "lng": loc.lng}
            for loc in request.locations
        ]
        location_ids = [loc.id for loc in request.locations]
        
        # Calculate distance matrix
        logger.info("Calculating distance matrix...")
        distance_matrix = calculate_distance_matrix(location_data)
        
        # Solve VRP
        logger.info("Solving VRP...")
        solution = solve_vrp(
            distance_matrix=distance_matrix,
            num_vehicles=request.num_vehicles,
            depot_index=0,
            vehicle_capacities=request.vehicle_capacities,
            demands=request.demands,
            time_limit_seconds=request.time_limit_seconds
        )
        
        # Check if solution was found
        if solution.get("error"):
            logger.error(f"Solver error: {solution['error']}")
            return VRPResponse(
                total_distance=0,
                routes=[],
                unvisited_nodes=location_ids,
                success=False,
                message=solution["error"]
            )
        
        # Convert routes from indices to location IDs
        routes = []
        for vehicle_id, route_indices in enumerate(solution["routes"]):
            route_ids = [location_ids[idx] for idx in route_indices]
            
            # Calculate route distance
            route_distance = 0
            for i in range(len(route_indices) - 1):
                from_idx = route_indices[i]
                to_idx = route_indices[i + 1]
                route_distance += distance_matrix[from_idx][to_idx]
            
            routes.append(Route(
                vehicle_id=vehicle_id,
                location_ids=route_ids,
                distance=route_distance
            ))
        
        # Convert unvisited nodes to location IDs
        unvisited_ids = [location_ids[idx] for idx in solution["unvisited_nodes"]]
        
        logger.info(f"Optimization successful. Total distance: {solution['total_distance']}m")
        
        return VRPResponse(
            total_distance=solution["total_distance"],
            routes=routes,
            unvisited_nodes=unvisited_ids,
            success=True,
            message="Optimization completed successfully"
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
