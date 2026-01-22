import numpy as np
from customer_data import cust_list, distance_matr

def route_cost(route, customers, distance_matrix, weights):
    cost = 0
    for i in range(len(route) - 1):
        curr, nxt = route[i], route[i + 1]
        cost += (
            weights["distance"] * distance_matrix[curr][nxt]
            + weights["service_time"] * customers[nxt]["service_time"]
            + weights["weather"] * customers[nxt]["weather"]
            + weights["priority"] * (1 - customers[nxt]["priority"])
        )
    return cost

def check_feasibility(route, customers, distance_matrix,
                      max_time=8*60, max_capacity=80):
    time_used = 0
    pallets = 0

    for i in range(len(route) - 1):
        curr, nxt = route[i], route[i + 1]
        time_used += distance_matrix[curr][nxt]
        time_used += customers[nxt]["service_time"]
        pallets += customers[nxt]["pallets"]

    return time_used <= max_time and pallets <= max_capacity

def best_insertion_for_route(route, new_customer_id,
                             customers, distance_matrix, weights):
    best_route = None
    best_cost_delta = float("inf")

    base_cost = route_cost(route, customers, distance_matrix, weights)

    # Try inserting at every position except depot start
    for pos in range(1, len(route) + 1):
        new_route = route[:pos] + [new_customer_id] + route[pos:]

        if not check_feasibility(new_route, customers, distance_matrix):
            continue

        new_cost = route_cost(new_route, customers, distance_matrix, weights)
        delta = new_cost - base_cost

        if delta < best_cost_delta:
            best_cost_delta = delta
            best_route = new_route

    return best_route, best_cost_delta

def insert_new_customer(existing_routes, new_customer_id,
                        customers, distance_matrix, weights):

    best_vehicle = None
    best_route = None
    best_delta = float("inf")

    for vehicle, route in existing_routes.items():
        candidate_route, delta = best_insertion_for_route(
            route,
            new_customer_id,
            customers,
            distance_matrix,
            weights
        )

        if candidate_route and delta < best_delta:
            best_vehicle = vehicle
            best_route = candidate_route
            best_delta = delta

    return best_vehicle, best_route, best_delta


WEIGHTS = {
    "priority": 10,
    "pallets": 9,
    "distance": 5,
    "service_time": 4,
    "weather": 1
}

customers = cust_list
distance_matrix = distance_matr

existing_routes = {
    "Vehicle-1": [0, 1, 9, 5, 12],
    "Vehicle-2": [0, 2, 10, 6, 13],
    "Vehicle-3": [0, 3, 4, 7, 11, 8]
}
print(distance_matrix)

new_customer_id = 14
customers.append({
    "name": "Kroger",
    "address": "4851 Legacy Dr, Frisco, TX 75034, United States",
    "chain": "Kroger",
    "lat": 33.233139,
    "lon": -96.7767189,
    "priority": 0.70,
    "service_time": 50,
    "weather": 0.9,
    "pallets": 22
})

vehicle, updated_route, delta = insert_new_customer(
    existing_routes,
    new_customer_id,
    customers,
    distance_matrix,
    WEIGHTS
)

print("✅ Best Vehicle:", vehicle)
print("🔁 Updated Route:", updated_route)
print("📉 Cost Increase:", delta)
