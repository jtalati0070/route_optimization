import folium
import random
import pandas as pd

# ----------------------------------------------------------
# Route Visualization
# ----------------------------------------------------------

def visualize_routes(before_routes, after_routes, customers, route_list):
    # Center map at depot
    depot = customers[0]
    m = folium.Map(location=[depot["lat"], depot["lon"]], zoom_start=12)

    colors = [
        "red", "blue", "green", "purple", "orange",
        "darkred", "darkblue", "darkgreen"
    ]

    # -----------------------
    # BEFORE Optimization
    # -----------------------
    before_group = folium.FeatureGroup(name="Before Optimization")

    for idx, (vehicle, route) in enumerate(before_routes.items()):
        color = colors[idx % len(colors)]

        coords = [
            (customers[route_list.index(c)]["lat"], customers[route_list.index(c)]["lon"])
            for c in route
        ]

        folium.PolyLine(
            coords,
            color=color,
            weight=4,
            opacity=0.7,
            tooltip=f"{vehicle} (Before)"
        ).add_to(before_group)

        for c in route:
            folium.CircleMarker(
                location=(customers[route_list.index(c)]["lat"], customers[route_list.index(c)]["lon"]),
                radius=6,
                popup=f"{vehicle} - {customers[route_list.index(c)]['name']}",
                color=color,
                fill=True
            ).add_to(before_group)

    before_group.add_to(m)

    # -----------------------
    # AFTER Optimization
    # -----------------------
    after_group = folium.FeatureGroup(name="After Optimization")

    for idx, (vehicle, route) in enumerate(after_routes.items()):
        color = colors[idx % len(colors)]

        coords = [
            (customers[route_list.index(c)]["lat"], customers[route_list.index(c)]["lon"])
            for c in route
        ]

        folium.PolyLine(
            coords,
            color=color,
            weight=4,
            opacity=0.9,
            dash_array="5,5",
            tooltip=f"{vehicle} (After)"
        ).add_to(after_group)

        for i, c in enumerate(route):
            folium.Marker(
                location=(customers[route_list.index(c)]["lat"], customers[route_list.index(c)]["lon"]),
                popup=f"{vehicle} - Stop {i} - {customers[route_list.index(c)]['name']}",
                icon=folium.Icon(color="green", icon="ok-sign")
            ).add_to(after_group)

    after_group.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m


# ----------------------------------------------------------
# Distance / Time KPI Comparison (Before vs After)
# ----------------------------------------------------------

def compute_route_kpis(route, customers, distance_matrix):
    total_travel = 0
    total_service = 0

    for i in range(len(route) - 1):
        total_travel += distance_matrix[route[i]][route[i+1]]
        total_service += customers[route[i+1]]["service_time"]

    return {
        "travel_time": total_travel,
        "service_time": total_service,
        "total_time": total_travel + total_service
    }

def compare_kpis(before_routes, after_routes, customers, distance_matrix):
    rows = []

    for vehicle in before_routes.keys():
        before = compute_route_kpis(before_routes[vehicle], customers, distance_matrix)
        after  = compute_route_kpis(after_routes[vehicle], customers, distance_matrix)

        rows.append({
            "Vehicle": vehicle,
            "Before Total Time": before["total_time"],
            "After Total Time": after["total_time"],
            "Time Saved": before["total_time"] - after["total_time"],
        })

    return pd.DataFrame(rows)

# ----------------------------------------------------------
# Stop-by-Stop ETA Table (With SLA Flag)
# ----------------------------------------------------------

SLA_MAX_ETA = 240  # minutes (example SLA)
START_TIME = 9 * 60  # 9:00 AM in minutes

def compute_eta_table(route, customers, distance_matrix,
                      start_time=START_TIME, sla_limit=SLA_MAX_ETA):

    rows = []
    current_time = start_time
    elapsed = 0

    for i in range(len(route)):
        cid = route[i]

        if i > 0:
            travel = distance_matrix[route[i-1]][cid]
            current_time += travel
            elapsed += travel

        service = customers[cid]["service_time"]
        current_time += service
        elapsed += service

        rows.append({
            "Customer": cid,
            "Arrival Time (min)": current_time - service,
            "Departure Time (min)": current_time,
            "Elapsed Time": elapsed,
            "Priority": customers[cid]["priority"],
            "SLA Violation": elapsed > sla_limit
        })

    return pd.DataFrame(rows)
