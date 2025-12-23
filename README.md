# Vehicle Routing Problem (VRP) API

A FastAPI application that solves the Vehicle Routing Problem using Google OR-Tools.

## Features

- ✅ **Basic VRP**: Optimize routes for multiple vehicles from a single depot
- ✅ **Capacity-Constrained VRP (CVRP)**: Support for vehicle capacities and location demands
- ✅ **Great Circle Distance**: Accurate distance calculations using geopy
- ✅ **Advanced Optimization**: Uses PATH_CHEAPEST_ARC and GUIDED_LOCAL_SEARCH strategies
- ✅ **Type Safety**: Full type hinting with Pydantic models
- ✅ **Error Handling**: Comprehensive validation and error messages
- ✅ **Logging**: Structured logging for debugging and monitoring

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python main.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Usage

### Basic VRP Example

**Request:**
```bash
curl -X POST "http://localhost:8000/optimize" \
  -H "Content-Type: application/json" \
        -d '{
    "locations": [
        { "id": "depot", "lat": 40.7128, "lng": -74.006 },
        { "id": "customer_1", "lat": 40.758, "lng": -73.9855 },
        { "id": "customer_2", "lat": 40.7489, "lng": -73.968 }
    ],
    "num_vehicles": 2,
    "time_limit_seconds": 30
    }'
```

**Response:**
```json
    {
    "total_distance": 12235,
    "routes": [
    {
        "vehicle_id": 0,
        "location_ids": [
        "depot",
        "depot"
        ],
        "distance": 0
    },
    {
        "vehicle_id": 1,
        "location_ids": [
        "depot",
        "customer_2",
        "customer_1",
        "depot"
        ],
        "distance": 12235
    }
    ],
    "unvisited_nodes": [],
    "success": true,
    "message": "Optimization completed successfully"
    }
```

### Capacity-Constrained VRP Example

**Request:**
```bash
curl -X POST "http://localhost:8000/optimize" \
  -H "Content-Type: application/json" \
  -d '{
    "locations": [
      {"id": "depot", "lat": 40.7128, "lng": -74.0060},
      {"id": "customer1", "lat": 40.7580, "lng": -73.9855},
      {"id": "customer2", "lat": 40.7489, "lng": -73.9680},
      {"id": "customer3", "lat": 40.6782, "lng": -73.9442}
    ],
    "num_vehicles": 2,
    "vehicle_capacities": [100, 100],
    "demands": [0, 30, 50, 40]
  }'
```

## Request Schema

```json
{
  "locations": [
    {
      "id": "string",
      "lat": -90 to 90,
      "lng": -180 to 180
    }
  ],
  "num_vehicles": 1,
  "vehicle_capacities": [100, 100],  // Optional
  "demands": [0, 30, 50],            // Optional (depot must be 0)
  "time_limit_seconds": 30           // Optional (default: 30, max: 300)
}
```

**Important Notes:**
- First location is always the depot
- If using capacities, must provide demands for all locations
- Depot demand must be 0
- Number of capacities must match num_vehicles
- Number of demands must match number of locations

## Response Schema

```json
{
  "total_distance": 45230,           // Total distance in meters
  "routes": [
    {
      "vehicle_id": 0,
      "location_ids": ["depot", "customer1", "depot"],
      "distance": 23450              // Route distance in meters
    }
  ],
  "unvisited_nodes": [],             // IDs of unvisited locations
  "success": true,
  "message": "Optimization completed successfully"
}
```

## Project Structure

```
Trajecta/
├── main.py              # FastAPI application and endpoints
├── solver.py            # OR-Tools VRP solver implementation
├── utils.py             # Distance matrix calculations
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── example_request.json # Sample request for testing
```

## Technologies Used

- **FastAPI** - Modern web framework for building APIs
- **Google OR-Tools** - Constraint programming and optimization
- **geopy** - Geocoding and distance calculations
- **Pydantic** - Data validation and settings management
- **uvicorn** - ASGI server implementation

## Error Handling

The API provides detailed error messages for common issues:
- Invalid coordinates (lat/lng out of range)
- Mismatched capacities/demands
- No solution found by solver
- Invalid request format

## Logging

The application uses Python's standard logging module. Logs include:
- Request details (number of locations, vehicles)
- Distance matrix calculation
- Solver progress and results
- Errors and warnings


