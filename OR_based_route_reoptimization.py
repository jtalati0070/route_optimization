from ortools.constraint_solver import pywrapcp, routing_enums_pb2
import numpy as np
from route_analytics import *

def create_single_vehicle_data(customers, distance_matrix, route_customers):
    data = {}
    data["customers"] = route_customers
    data["distance_matrix"] = distance_matrix
    data["num_vehicles"] = 1
    data["depot"] = 0
    data["vehicle_capacity"] = 80
    data["max_time"] = 8 * 60
    return data


def build_routing_model(data, customers, weights):
    manager = pywrapcp.RoutingIndexManager(
        len(data["customers"]),
        data["num_vehicles"],
        0
    )

    routing = pywrapcp.RoutingModel(manager)

    def cost_callback(from_idx, to_idx):
        i = data["customers"][manager.IndexToNode(from_idx)]
        j = data["customers"][manager.IndexToNode(to_idx)]

        cost = (
            weights["distance"] * data["distance_matrix"][i][j]
            + weights["service_time"] * customers[j]["service_time"]
            + weights["weather"] * customers[j]["weather"]
            + weights["priority"] * (1 - customers[j]["priority"])
        )
        return int(cost)

    transit_cb = routing.RegisterTransitCallback(cost_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_cb)

    return routing, manager


def add_capacity_constraint(routing, manager, data, customers):
    def demand_callback(from_idx):
        node = data["customers"][manager.IndexToNode(from_idx)]
        return customers[node]["pallets"]

    demand_cb = routing.RegisterUnaryTransitCallback(demand_callback)

    routing.AddDimensionWithVehicleCapacity(
        demand_cb,
        0,
        [data["vehicle_capacity"]],
        True,
        "Capacity"
    )


def add_time_dimension(routing, manager, data, customers):
    def time_callback(from_idx, to_idx):
        i = data["customers"][manager.IndexToNode(from_idx)]
        j = data["customers"][manager.IndexToNode(to_idx)]
        return data["distance_matrix"][i][j] + customers[j]["service_time"]

    time_cb = routing.RegisterTransitCallback(time_callback)

    routing.AddDimension(
        time_cb,
        0,
        data["max_time"],
        True,
        "Time"
    )


def optimize_single_route(route, customers, distance_matrix, weights):
    data = create_single_vehicle_data(customers, distance_matrix, route)

    routing, manager = build_routing_model(data, customers, weights)
    add_capacity_constraint(routing, manager, data, customers)
    add_time_dimension(routing, manager, data, customers)

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    params.time_limit.seconds = 5

    solution = routing.SolveWithParameters(params)

    if not solution:
        return route

    idx = routing.Start(0)
    optimized_route = []

    while not routing.IsEnd(idx):
        optimized_route.append(
            data["customers"][manager.IndexToNode(idx)]
        )
        idx = solution.Value(routing.NextVar(idx))

    return optimized_route


def optimize_all_routes(assigned_routes, customers, distance_matrix, weights):
    optimized = {}

    for vehicle, route in assigned_routes.items():
        optimized[vehicle] = optimize_single_route(
            route,
            customers,
            distance_matrix,
            weights
        )

    return optimized


WEIGHTS = {
    "priority": 10,
    "pallets": 9,
    "distance": 5,
    "service_time": 4,
    "weather": 1
}

customers = [
    {"priority": 1.0, "service_time": 0,  "weather": 0,   "pallets": 0},  # depot
    {"priority": 0.95, "service_time": 15, "weather": 0.1, "pallets": 10},
    {"priority": 0.90, "service_time": 20, "weather": 0.2, "pallets": 15},
    {"priority": 0.92, "service_time": 10, "weather": 0.3, "pallets": 12},
    {"priority": 0.85, "service_time": 25, "weather": 0.2, "pallets": 18},
    {"priority": 0.75, "service_time": 30, "weather": 0.4, "pallets": 20},
    {"priority": 0.70, "service_time": 10, "weather": 0.1, "pallets": 10},
    {"priority": 0.65, "service_time": 15, "weather": 0.2, "pallets": 8},
    {"priority": 0.60, "service_time": 20, "weather": 0.3, "pallets": 25},
    {"priority": 0.50, "service_time": 10, "weather": 0.1, "pallets": 8},
    {"priority": 0.45, "service_time": 10, "weather": 0.4, "pallets": 5},
    {"priority": 0.35, "service_time": 10, "weather": 0.3, "pallets": 6},
]

np.random.seed(7)

distance_matrix = np.random.randint(8, 35, size=(12,12)).tolist()
for i in range(13):
    distance_matrix[i][i] = 0


assigned_routes = {
    "Vehicle-1": [0, 1, 5, 9, 12],
    "Vehicle-2": [0, 2, 6, 10],
    "Vehicle-3": [0, 3, 4, 7, 8, 11]
}

optimized_routes = optimize_all_routes(
    assigned_routes,
    customers,
    distance_matrix,
    WEIGHTS
)

for v, r in optimized_routes.items():
    print(v, "→", r)




route_map = visualize_routes(assigned_routes, optimized_routes, customers)
print(route_map)

kpi_df = compare_kpis(assigned_routes, optimized_routes, customers, distance_matrix)
print(kpi_df)

eta_vehicle_1 = compute_eta_table(
    optimized_routes["Vehicle-1"],
    customers,
    distance_matrix
)
print(eta_vehicle_1)
