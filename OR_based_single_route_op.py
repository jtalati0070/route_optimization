import h3
from config import config
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
import math

WEIGHTS = config.WEIGHTS
TRUCK_CAPACITY = config.TRUCK_CAPACITY
FORMAT_PENALTY = config.FORMAT_PENALTY
TOTAL_DRIVE_TIME = config.TOTAL_DRIVE_TIME


def normalize_h3(h3_cell, target_res):
    res = h3.get_resolution(h3_cell)
    if res == target_res:
        return h3_cell
    elif res > target_res:
        return h3.cell_to_parent(h3_cell, target_res)
    else:
        children = h3.cell_to_children(h3_cell, target_res)
        return list(children)[0]


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi/2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def build_h3_distance_matrix(cust_df):
    customers = cust_df["customer_id"].to_list()
    h3_map = dict(zip(cust_df["customer_id"], cust_df["h3_res"]))
    print(f"h3 map == {h3_map}")
    index_map = {cid: i for i, cid in enumerate(customers)}

    n = len(customers)
    matrix = [[0]*n for _ in range(n)]

    for i, c1 in enumerate(customers):
        for j, c2 in enumerate(customers):
            if i == j:
                continue
            try:
                h1 = h3_map[c1]
                h2 = h3_map[c2]
                matrix[i][j] = int(len(h3.grid_path_cells(h1, h2)))
            except:
                lat1, lon1 = h3.cell_to_latlng(h3_map[c1])
                lat2, lon2 = h3.cell_to_latlng(h3_map[c2])
                matrix[i][j] = int(haversine_distance(lat1, lon1, lat2, lon2)/0.190395)

    return matrix, index_map


def create_single_vehicle_data(customers, distance_matrix, route_customers):
    data = {}
    data["customers"] = route_customers
    data["distance_matrix"] = distance_matrix
    data["num_vehicles"] = 1
    data["depot"] = 0
    data["vehicle_capacity"] = TRUCK_CAPACITY
    data["max_time"] = TOTAL_DRIVE_TIME
    return data


def build_routing_model(data, customers, weights):
    manager = pywrapcp.RoutingIndexManager(
        len(data["customers"])-1,
        data["num_vehicles"],
        0
    )

    routing = pywrapcp.RoutingModel(manager)

    def cost_callback(from_idx, to_idx):
        i = from_idx
        j = to_idx
        cost = (
            weights["dwell_time"] * customers[j]["dwell_time"]
            + weights["distance"] * data["distance_matrix"][i][j]
            + weights["pallets"] * customers[j]["avg_pallets"]
            # + weights["format"] * FORMAT_PENALTY[customers[j]["format"]]
        )
        return int(cost)

    transit_cb = routing.RegisterTransitCallback(cost_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_cb)

    return routing, manager


def add_capacity_constraint(routing, manager, data, customers):
    def demand_callback(from_idx):
        node = from_idx
        return customers[node]["avg_pallets"]

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
        i = from_idx
        j = to_idx
        return data["distance_matrix"][i][j] + customers[j]["dwell_time"]

    time_cb = routing.RegisterTransitCallback(time_callback)

    routing.AddDimension(
        time_cb,
        0,
        data["max_time"],
        True,
        "Time"
    )


def optimize_single_route(route, customers, distance_matrix, weights):
    print(f"route == {route}, \n customers == {customers}, \n distance_matrix == {distance_matrix}, \n weights == {weights}")
    data = create_single_vehicle_data(customers, distance_matrix, route)

    routing, manager = build_routing_model(data, customers, weights)
    add_capacity_constraint(routing, manager, data, customers)
    # add_time_dimension(routing, manager, data, customers)

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    params.time_limit.seconds = 5

    solution = routing.SolveWithParameters(params)

    if not solution:
        print("No solution found. Returning the original route. ")
        return route

    idx = routing.Start(0)
    optimized_route = []

    while not routing.IsEnd(idx):
        optimized_route.append(
            data["customers"][manager.IndexToNode(idx)]
        )
        idx = solution.Value(routing.NextVar(idx))

    return optimized_route


def reoptimize_all_routes(customer_df):
    distance_matrix, index_map = build_h3_distance_matrix(customer_df)
    print(f"distance matrix: {distance_matrix}")
    route_customers = customer_df["customer_id"].to_list()
    customers = customer_df.to_dict("records")
    optimized = optimize_single_route(route_customers, customers, distance_matrix, WEIGHTS)
    print(f"optimized route: {optimized}")
    return optimized

#
# def optimize_route(route_df, distance_matrix, index_map):
#     customer_ids = route_df["customer_id"].to_list()
#     manager = pywrapcp.RoutingIndexManager(
#         len(customer_ids), 1, 0
#     )
#     routing = pywrapcp.RoutingModel(manager)
#
#     def cost_cb(from_idx, to_idx):
#         cid = customer_ids[manager.IndexToNode(int(to_idx))]
#         row = route_df.loc[route_df["customer_id"] == cid].iloc[0]
#
#         return (
#             WEIGHTS["dwell"] * row["dwell_time"]
#             + WEIGHTS["distance"] * distance_matrix[index_map[customer_ids[manager.IndexToNode(from_idx)]]][index_map[cid]]
#             + WEIGHTS["avg_pallets"] * row["avg_pallets"]
#             + WEIGHTS["format"] * FORMAT_PENALTY[row["format"]]
#         )
#
#     print("Defined the cost callback function")
#     transit_cb = routing.RegisterTransitCallback(cost_cb)
#     routing.SetArcCostEvaluatorOfAllVehicles(transit_cb)
#
#     def demand_cb(from_idx):
#         cid = customer_ids[manager.IndexToNode(from_idx)]
#         return int(
#             route_df.loc[
#                 route_df["customer_id"] == cid, "avg_pallets"
#             ].iloc[0]
#         )
#     print("Defined the demand_callback function")
#     demand_cb_idx = routing.RegisterUnaryTransitCallback(demand_cb)
#
#     routing.AddDimensionWithVehicleCapacity(
#         demand_cb_idx,
#         0,
#         [TRUCK_CAPACITY],
#         True,
#         "Capacity"
#     )
#     print("Solving the actual problem...")
#     params = pywrapcp.DefaultRoutingSearchParameters()
#     params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
#     params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
#     params.time_limit.seconds = 5
#
#     solution = routing.SolveWithParameters(params)
#
#     if not solution:
#         return customer_ids
#
#     idx = routing.Start(0)
#     optimized = []
#
#     while not routing.IsEnd(idx):
#         optimized.append(customer_ids[manager.IndexToNode(idx)])
#         idx = solution.Value(routing.NextVar(idx))
#
#     print(f"optimized customers: {optimized}")
#
#     return optimized
