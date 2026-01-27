import h3
import itertools

from ortools.constraint_solver import pywrapcp, routing_enums_pb2


def build_h3_distance_matrix(customers):
    ids = list(customers.keys())
    index_map = {cid: i for i, cid in enumerate(ids)}

    n = len(ids)
    matrix = [[0]*n for _ in range(n)]

    for a, b in itertools.product(ids, ids):
        i, j = index_map[a], index_map[b]
        if a != b:
            matrix[i][j] = h3.grid_distance(
                customers[a]["h3"],
                customers[b]["h3"]
            )

    return matrix, index_map, ids

def optimize_route(route_customer_ids, customers, distance_matrix, index_map):
    manager = pywrapcp.RoutingIndexManager(
        len(route_customer_ids), 1, 0
    )
    routing = pywrapcp.RoutingModel(manager)

    def cost_cb(from_idx, to_idx):
        i = route_customer_ids[manager.IndexToNode(to_idx)]
        idx = index_map[i]

        return (
            WEIGHTS["dwell"] * customers[i]["dwell"]
            + WEIGHTS["distance"] * distance_matrix[manager.IndexToNode(from_idx)][manager.IndexToNode(to_idx)]
            + WEIGHTS["avg_pallets"] * customers[i]["avg_pallets"]
            + WEIGHTS["format"] * FORMAT_PENALTY[customers[i]["format"]]
        )

    transit_cb = routing.RegisterTransitCallback(cost_cb)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_cb)

    def demand_cb(from_idx):
        i = route_customer_ids[manager.IndexToNode(from_idx)]
        return customers[i]["avg_pallets"]

    demand_cb_idx = routing.RegisterUnaryTransitCallback(demand_cb)

    routing.AddDimensionWithVehicleCapacity(
        demand_cb_idx,
        0,
        [TRUCK_CAPACITY],
        True,
        "Capacity"
    )

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    params.time_limit.seconds = 5

    solution = routing.SolveWithParameters(params)

    if not solution:
        return route_customer_ids

    idx = routing.Start(0)
    optimized = []

    while not routing.IsEnd(idx):
        optimized.append(route_customer_ids[manager.IndexToNode(idx)])
        idx = solution.Value(routing.NextVar(idx))

    return optimized


def reoptimize_all_routes(pg):
    routes, customers = fetch_routes_and_customers(pg)
    distance_matrix, index_map, _ = build_h3_distance_matrix(customers)

    optimized_routes = {}

    for vehicle, custs in routes.items():
        optimized_routes[vehicle] = optimize_route(
            custs,
            customers,
            distance_matrix,
            index_map
        )

    return optimized_routes


WEIGHTS = {
    "dwell": 100,
    "distance": 50,
    "avg_pallets": 20,
    "format": 10
}

FORMAT_PENALTY = {
    "SMALL": 0,
    "LARGE": 1
}

TRUCK_CAPACITY = 100
