from ortools.constraint_solver import pywrapcp, routing_enums_pb2
import numpy as np

# ----------------------------------------------------------
# Balanced Assignment (same as rule-based)
# ----------------------------------------------------------

def balanced_assignment(customers, vehicle_count):
    customer_list = list(range(1, len(customers)))
    customer_list.sort(key=lambda cid: customers[cid]["priority"], reverse=True)

    n = len(customer_list)
    high = customer_list[: n // 3]
    medium = customer_list[n // 3 : 2 * n // 3]
    low = customer_list[2 * n // 3 :]

    vehicle_customers = [[] for _ in range(vehicle_count)]

    def rr(group):
        v = 0
        for c in group:
            vehicle_customers[v % vehicle_count].append(c)
            v += 1

    rr(high)
    rr(medium)
    rr(low)

    return vehicle_customers


# ----------------------------------------------------------
# OR-Tools Data Model
# ----------------------------------------------------------

def create_data_model(customers, distance_matrix, assignments):
    data = {}
    data["distance_matrix"] = distance_matrix
    data["customers"] = customers
    data["num_vehicles"] = len(assignments)
    data["depot"] = 0
    data["vehicle_customers"] = assignments
    data["vehicle_capacities"] = [80] * data["num_vehicles"]
    data["max_time"] = 8 * 60
    return data


def create_routing_model(data, weights):
    manager = pywrapcp.RoutingIndexManager(
        len(data["distance_matrix"]),
        data["num_vehicles"],
        data["depot"]
    )

    routing = pywrapcp.RoutingModel(manager)

    def cost_callback(from_idx, to_idx):
        i = manager.IndexToNode(from_idx)
        j = manager.IndexToNode(to_idx)
        cust = data["customers"]

        cost = (
            weights["distance"] * data["distance_matrix"][i][j]
            + weights["service_time"] * cust[j]["service_time"]
            + weights["weather"] * cust[j]["weather"]
            + weights["priority"] * (1 - cust[j]["priority"])
        )
        return int(cost)

    transit_cb = routing.RegisterTransitCallback(cost_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_cb)

    return routing, manager

def add_capacity_constraint(routing, manager, data):
    def demand_callback(from_idx):
        node = manager.IndexToNode(from_idx)
        print(f"Node == {node}, customers node == {customers[manager.IndexToNode(from_idx)]}")
        return data["customers"][node]["pallets"]

    demand_cb = routing.RegisterUnaryTransitCallback(demand_callback)

    routing.AddDimensionWithVehicleCapacity(
        demand_cb,
        0,
        data["vehicle_capacities"],
        True,
        "Capacity"
    )


def add_time_dimension(routing, manager, data):
    def time_callback(from_idx, to_idx):
        i = manager.IndexToNode(from_idx)
        j = manager.IndexToNode(to_idx)

        travel = data["distance_matrix"][i][j]
        service = data["customers"][j]["service_time"]
        return travel + service

    time_cb = routing.RegisterTransitCallback(time_callback)

    routing.AddDimension(
        time_cb,
        0,
        data["max_time"],
        True,
        "Time"
    )


def apply_vehicle_customer_constraints(routing, manager, data):
    for v, allowed_customers in enumerate(data["vehicle_customers"]):
        allowed = set(allowed_customers + [0])
        for node in range(len(data["customers"])):
            if node not in allowed:
                routing.VehicleVar(manager.NodeToIndex(node)).RemoveValue(v)


def solve_vrp(routing):
    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    params.time_limit.seconds = 10
    return routing.SolveWithParameters(params)


def print_solution(routing, manager, solution, data):
    for v in range(data["num_vehicles"]):
        idx = routing.Start(v)
        route = []
        while not routing.IsEnd(idx):
            route.append(manager.IndexToNode(idx))
            idx = solution.Value(routing.NextVar(idx))
        print(f"🚚 Vehicle {v+1}: {route}")


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
for i in range(12):
    distance_matrix[i][i] = 0

assignments = balanced_assignment(customers, 3)
print(assignments)
data = create_data_model(customers, distance_matrix, assignments)

routing, manager = create_routing_model(data, WEIGHTS)
add_capacity_constraint(routing, manager, data)
add_time_dimension(routing, manager, data)
apply_vehicle_customer_constraints(routing, manager, data)

solution = solve_vrp(routing)
print_solution(routing, manager, solution, data)
