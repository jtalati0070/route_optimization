import numpy as np

def compute_score(current, candidate, distance_matrix, customers, W):
    """
    Scoring Function
    :param current:
    :param candidate:
    :param distance_matrix:
    :param customers:
    :param W:
    :return:
    """
    return (
        W["priority"] * customers[candidate]["priority"]
        - W["pallets"] * customers[candidate]["pallets"]
        - W["distance"] * distance_matrix[current][candidate]
        - W["service_time"] * customers[candidate]["service_time"]
        - W["weather"] * customers[candidate]["weather"]
    )


def balanced_assignment(customers, vehicle_count):
    """
    Balanced Assignment for customers to routes.
    :param customers:
    :param vehicle_count:
    :return:
    """
    # Ignore depot at index 0
    customer_list = list(range(1, len(customers)))

    # Sort customers by priority
    customer_list.sort(key=lambda cid: customers[cid]["priority"], reverse=True)

    # Split into high, medium, low
    n = len(customer_list)
    high = customer_list[: n // 3]
    medium = customer_list[n // 3 : 2 * n // 3]
    low = customer_list[2 * n // 3 :]
    print(high, medium, low)

    # Round robin assignment
    vehicle_customers = [[] for _ in range(vehicle_count)]

    def round_robin_fill(group):
        vid = 0
        for c in group:
            vehicle_customers[vid % vehicle_count].append(c)
            vid += 1

    round_robin_fill(high)
    round_robin_fill(medium)
    round_robin_fill(low)
    print(vehicle_customers)
    return vehicle_customers


# ----------------------------------------------------------
# Rule-Based Route Builder for a Single Vehicle
# ----------------------------------------------------------

def build_route(customer_ids, customers, distance_matrix, W, vehicle_capacity=80, max_minutes=8*60):

    route = [0]  # depot
    current = 0
    time_used = 0
    capacity_used = 0
    remaining = set(customer_ids)

    while remaining:
        best, best_score = None, float("-inf")

        for cand in remaining:
            travel_time = distance_matrix[current][cand]
            service_time = customers[cand]["service_time"]
            pallets = customers[cand]["pallets"]

            if time_used + travel_time + service_time > max_minutes:
                continue
            if capacity_used + pallets > vehicle_capacity:
                continue

            score = compute_score(
                current, cand, distance_matrix, customers, W
            )

            if score > best_score:
                best, best_score = cand, score

        if best is None:
            break

        route.append(best)
        remaining.remove(best)

        time_used += distance_matrix[current][best] + customers[best]["service_time"]
        capacity_used += customers[best]["pallets"]
        current = best

    return route, time_used, capacity_used



# ----------------------------------------------------------
# Full Multi-Vehicle Routing with Balanced Priority Distribution
# ----------------------------------------------------------

def rule_based_multi_vehicle(customers, distance_matrix, W, vehicle_count=3):

    assignments = balanced_assignment(customers, vehicle_count)
    results = []

    for v in range(vehicle_count):
        route, time_used, pallets = build_route(
            assignments[v],
            customers,
            distance_matrix,
            W
        )

        results.append({
            "vehicle": v + 1,
            "assigned_customers": assignments[v],
            "route": route,
            "time_used": time_used,
            "pallets_used": pallets
        })

    return results



# ----------------------------------------------------------
# Example Data (12 Customers)
# ----------------------------------------------------------

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

np.random.seed(10)
distance_matrix = np.random.randint(7, 35, size=(13,13)).tolist()
for i in range(13):
    distance_matrix[i][i] = 0
time_matrix = distance_matrix

WEIGHTS = {
    "priority": 10,        # serve earlier
    "pallets": 9,          # vehicle load constraint
    "distance": 5,         # time taken to reach
    "service_time": 4,     # time spent at customer
    "weather": 1           # lowest impact
}

routes = rule_based_multi_vehicle(customers, distance_matrix, WEIGHTS)

for r in routes:
    print(f"\n🚚 Vehicle {r['vehicle']}")
    print("Assigned:", r["assigned_customers"])
    print("Route:", r["route"])
    print("Time used:", r["time_used"])
    print("Pallets:", r["pallets_used"])