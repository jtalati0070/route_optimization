cust_list = [
    {
        "name": "PepsiCo R&D",
        "address": "5600 Headquarters Dr, Plano, TX 75024",
        "chain": "PepsiCo",
        "lat": 33.0758322,
        "lon": -96.8475577,
        "priority": 1.0, "service_time": 0,  "weather": 0,   "pallets": 0
    },
    {
        "name": "Walmart Supercenter - Central Expy",
        "address": "6001 Central Expy, Plano, TX 75023",
        "chain": "Walmart",
        "lat": 33.0389,
        "lon": -96.6985,
        "priority": 0.90, "service_time": 15, "weather": 0.1, "pallets": 10
    },
    {
        "name": "Walmart Supercenter - Coit Rd",
        "address": "425 Coit Rd, Plano, TX 75075",
        "chain": "Walmart",
        "lat": 33.0423,
        "lon": -96.7337,
        "priority": 0.90, "service_time": 20, "weather": 0.2, "pallets": 15
    },
    {
        "name": "Walmart Supercenter - Ohio Dr",
        "address": "8801 Ohio Dr, Plano, TX 75024",
        "chain": "Walmart",
        "lat": 33.0261,
        "lon": -96.7699,
        "priority": 0.90, "service_time": 10, "weather": 0.3, "pallets": 12
    },
    {
        "name": "Walmart Supercenter - Dallas Pkwy",
        "address": "1700 Dallas Pkwy, Plano, TX 75093",
        "chain": "Walmart",
        "lat": 33.0470,
        "lon": -96.7518,
        "priority": 0.90, "service_time": 25, "weather": 0.2, "pallets": 18
    },
    {
        "name": "Walmart Neighborhood Market - Custer Rd",
        "address": "3100 Custer Rd, Plano, TX 75075",
        "chain": "Walmart",
        "lat": 33.0375,
        "lon": -96.7350,
        "priority": 0.90, "service_time": 19, "weather": 0.3, "pallets": 19
    },
    {
        "name": "Walmart Neighborhood Market - Park Blvd",
        "address": "3513 E Park Blvd, Plano, TX 75074",
        "chain": "Walmart",
        "lat": 33.0348,
        "lon": -96.6657,
        "priority": 0.90, "service_time": 30, "weather": 0.4, "pallets": 20
    },
    {
        "name": "Walmart Neighborhood Market - Preston Rd",
        "address": "3312 Preston Rd, Plano, TX 75093",
        "chain": "Walmart",
        "lat": 33.0229,
        "lon": -96.7081,
        "priority": 0.90, "service_time": 10, "weather": 0.1, "pallets": 10
    },
    {
        "name": "Walmart Neighborhood Market - Independence Pkwy",
        "address": "8040 Independence Pkwy, Plano, TX 75025",
        "chain": "Walmart",
        "lat": 33.0288,
        "lon": -96.7335,
        "priority": 0.90, "service_time": 15, "weather": 0.2, "pallets": 8
    },
    {
        "name": "Kroger Marketplace - 121 & Coit",
        "address": "9617 Coit Rd, Plano, TX 75024",
        "chain": "Kroger",
        "lat": 33.0471,
        "lon": -96.7161,
        "priority": 0.70, "service_time": 20, "weather": 0.3, "pallets": 25
    },
    {
        "name": "Kroger - Los Rios",
        "address": "4017 14th St, Plano, TX 75074",
        "chain": "Kroger",
        "lat": 33.0287,
        "lon": -96.6746,
        "priority": 0.70, "service_time": 10, "weather": 0.1, "pallets": 8
    },
    {
        "name": "Kroger - Custer Park",
        "address": "2925 Custer Rd, Plano, TX 75075",
        "chain": "Kroger",
        "lat": 33.0415,
        "lon": -96.7411,
        "priority": 0.70, "service_time": 10, "weather": 0.4, "pallets": 5
    },
    {
        "name": "Kroger - Independence Pkwy",
        "address": "7100 Independence Pkwy, Plano, TX 75025",
        "chain": "Kroger",
        "lat": 33.0174,
        "lon": -96.7479,
        "priority": 0.70, "service_time": 10, "weather": 0.3, "pallets": 6
    },
    {
        "name": "Kroger - Windhaven Plaza",
        "address": "3305 Dallas Pkwy, Plano, TX 75093",
        "chain": "Kroger",
        "lat": 33.0453,
        "lon": -96.7521,
        "priority": 0.70, "service_time": 14, "weather": 0.3, "pallets": 14
    }
]
print(len(cust_list))
distance_matr = [[0, 12, 33, 30, 11, 27, 31, 15, 33, 22, 31, 16, 33, 22, 18],
 [34, 0, 15, 14, 12, 24, 15, 20, 8, 19, 31, 34, 14, 27, 20],
 [13, 32, 0, 31, 29, 24, 8, 10, 32, 17, 22, 14, 12, 22, 70],
 [31, 11, 11, 0, 27, 24, 9, 8, 24, 30, 20, 15, 31, 18, 17],
 [11, 8, 15, 31, 0, 8, 29, 12, 11, 9, 11, 9, 27, 12, 27],
 [9, 33, 13, 17, 25, 0, 27, 26, 26, 29, 31, 11, 19, 34, 23],
 [24, 20, 19, 17, 17, 20, 0, 22, 22, 28, 29, 23, 11, 24, 44],
 [19, 16, 34, 34, 30, 19, 23, 0, 21, 26, 15, 11, 20, 20, 23],
 [16, 30, 14, 29, 14, 29, 20, 15, 0, 18, 23, 13, 12, 28, 17],
 [17, 34, 8, 30, 10, 20, 14, 16, 10, 0, 22, 28, 25, 14, 18],
 [25, 13, 23, 25, 30, 20, 17, 16, 30, 23, 0, 17, 31, 29, 44],
 [20, 17, 19, 14, 32, 9, 29, 29, 19, 32, 27, 0, 31, 33, 20],
 [20, 21, 12, 15, 29, 34, 17, 14, 23, 19, 26, 24, 0, 11, 21],
 [8, 29, 31, 9, 21, 16, 28, 22, 21, 17, 18, 8, 10, 0, 73],
 [14, 26, 70, 17, 21, 29, 91, 9, 22, 24, 50, 33, 25, 75, 0]]